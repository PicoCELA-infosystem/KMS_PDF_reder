import pdfplumber
import sys
import csv
import re

def clean_price(text):
    # 「¥」などの文字除去・カンマ除去、数値へ整形
    if text is None:
        return ""
    return re.sub(r'[^\d]', '', text)

def main(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        if not tables:
            print("Error: 1ページ目に表が見つかりません。")
            return
        
        table = tables[0]
        headers = table
        # 必要列のインデックス取得
        try:
            idx_pinmei = headers.index("品名")
            idx_tanka = headers.index("単価(円)")
            idx_suryo = headers.index("数量")
            idx_kingaku = headers.index("金額(円)")
            idx_biko = headers.index("備考")
        except ValueError as e:
            print("Error: 必要な列が見つかりません。")
            return
        
        writer = csv.writer(sys.stdout)
        writer.writerow(["明細名", "税込金額"])  # ヘッダー出力
        
        # 品名には部品番号も付随している行もあるため処理
        current_prefix = ""
        
        for row in table[1:]:
            pinmei = row[idx_pinmei] or ""
            tanka = clean_price(row[idx_tanka])
            suryo = row[idx_suryo] or ""
            kingaku = clean_price(row[idx_kingaku])
            biko = row[idx_biko] or ""
            
            # 品名が空欄の場合、前のprefixが続く明細かもしれない
            if pinmei.strip() == "":
                # 無視または備考だけある場合もあるのでスキップ
                continue
            
            # 品名前に番号などがあれば除去（例: '1 PCWL-0410:受入検査作業'）
            if re.match(r'^\d+\s+', pinmei):
                prefix = re.sub(r'^\d+\s+', '', pinmei).strip()
            else:
                prefix = pinmei.strip()
            
            # 明細名を品名＋備考＋数量＋単価の読みやすい形に変換
            detail_name = prefix
            if suryo != "" and tanka != "":
                try:
                    int_suryo = int(suryo)
                except ValueError:
                    int_suryo = None
                if int_suryo:
                    detail_name += f" {int_suryo}台 @{int(tanka)}"
                else:
                    detail_name += f" {suryo} @ {tanka}"
            if biko.strip() != "":
                detail_name += f" {biko.strip()}"
            
            if kingaku == "":
                kingaku = "0"
            
            writer.writerow([detail_name, kingaku])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <PDFファイルパス>")
    else:
        main(sys.argv[1])
