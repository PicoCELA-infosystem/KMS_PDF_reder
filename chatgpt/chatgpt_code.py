#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF(画像ベース)の1ページ目から明細行をOCRで抽出し、
「明細名, 税込金額」の2列CSVに整形して出力します。

使い方:
  python ocr_to_items_csv.py 0f3fcb71-6daf-4622-b138-4b176603c42b.pdf [csvFormat.csv]

要件:
  - poppler( pdf2image用 ) と Tesseract OCR を事前インストール
  - pip install pdf2image pytesseract pillow

仕様:
  - 1ページ目のみ対象
  - 末尾に金額が書かれている行 → その金額を税込金額として採用
  - 「数量(台)」「@単価」だけの行 → 数量×単価×(1+TAX_RATE) で税込金額を算出(四捨五入)
  - 合計/小計/税などの集計行は除外
"""

import sys
import csv
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pdf2image import convert_from_path
import pytesseract

# 必要に応じて調整
TAX_RATE = Decimal("0.10")  # 消費税10%

# ---- ユーティリティ ----
def nfkc(s: str) -> str:
    """全角→半角などNFKC正規化"""
    return unicodedata.normalize("NFKC", s)

def to_int(num_str: str) -> int:
    """カンマ/円記号などを除去してint化"""
    clean = re.sub(r"[^\d\-]", "", num_str)
    return int(clean) if clean else 0

def round_half_up_decimal(value: Decimal) -> int:
    """四捨五入(商習慣に近い)でintへ"""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def looks_like_summary(text: str) -> bool:
    """合計/小計/計/税/消費税などの集計行を判定"""
    return bool(re.search(r"(合計|小計|計|税|消費税|内税|外税)", text))

def find_trailing_amount(text: str):
    """
    行末に金額があれば返す。
    ただし '@1500' のような単価を末尾で拾わないように回避。
    戻り値: (has_amount: bool, amount_int: int, desc_wo_amount: str)
    """
    s = text.rstrip()

    # 末尾が @xxxx で終わる(=単価)なら金額扱いしない
    if re.search(r"[@＠]\s*\d[\d,]*\s*$", s):
        return (False, 0, s)

    # 末尾の金額 (任意の円記号を許容)
    m = re.search(r"(.*?)[\s　]*[¥￥]?\s*(\d[\d,]*)\s*$", s)
    if not m:
        return (False, 0, s)

    desc = m.group(1)
    amt_str = m.group(2)

    # ただし、desc側が空で、行全体が数字だけ…のような不自然さを排除
    if not desc.strip():
        return (False, 0, s)

    # さらに直前が "@数字" だった場合は単価とみなし除外(保険)
    tail = s[max(0, m.start(2)-2):m.end(2)]
    if re.search(r"[@＠]\s*\d", tail):
        return (False, 0, s)

    return (True, to_int(amt_str), desc.rstrip())

def compute_tax_included_from_qty_unit(text: str):
    """
    「XX台 @YY」/「XX台@YY」/「XX台×YY」等から税込金額を計算。
    該当しなければ None を返す。
    """
    # 例: "57台 @300", "40台@1,900", "1台×1500", "1台 ＠ 1500"
    m = re.search(
        r"(?P<qty>\d+)\s*台\s*[×xX*]?\s*[@＠]?\s*(?P<unit>\d[\d,]*)",
        text
    )
    if not m:
        return None

    qty = int(m.group("qty"))
    unit = to_int(m.group("unit"))
    base = Decimal(qty * unit)
    tax_included = round_half_up_decimal(base * (Decimal("1.0") + TAX_RATE))
    return tax_included

def clean_description(desc: str) -> str:
    """説明文の余分な空白を軽く整形(必要最低限)"""
    # 複数空白→1空白
    d = re.sub(r"\s{2,}", " ", desc).strip()
    return d

# ---- メイン処理 ----
def ocr_first_page_to_csv(pdf_path: str, out_csv: str = "csvFormat.csv"):
    # PDF→画像(1ページ目のみ)
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    if not images:
        raise RuntimeError("PDFから画像を取得できませんでした。")

    # OCR (日本語+英数)
    raw_text = pytesseract.image_to_string(images[0], lang="jpn+eng")

    lines = [nfkc(l).strip() for l in raw_text.splitlines()]
    lines = [l for l in lines if l]  # 空行除外

    rows = []
    for line in lines:
        if looks_like_summary(line):
            continue  # 集計系はスキップ

        # 1) 末尾に金額がある行はそれを採用
        has_amt, amt, desc = find_trailing_amount(line)
        if has_amt:
            rows.append([clean_description(desc), str(amt)])
            continue

        # 2) 末尾金額が無ければ、数量×単価から税込計算
        amt2 = compute_tax_included_from_qty_unit(line)
        if amt2 is not None:
            rows.append([clean_description(line), str(amt2)])
            continue

        # 3) どちらも取れなければスキップ（必要ならログ化）
        # print(f"SKIP: {line}")  # デバッグ用

    # CSV出力（ヘッダ含む）
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["明細名", "税込金額"])
        w.writerows(rows)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python ocr_to_items_csv.py input.pdf [csvFormat.csv]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_csv = sys.argv[2] if len(sys.argv) >= 3 else "csvFormat.csv"
    ocr_first_page_to_csv(pdf_path, out_csv)
