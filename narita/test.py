import csv
import os
import re
import fitz  # PyMuPDFライブラリ

def parse_pdf_data(pdf_path):
    """
    PDFファイルから請求書データを抽出し、指定された形式に整形します。

    Args:
        pdf_path (str): 読み込むPDFファイルのパス。

    Returns:
        list: 抽出・整形された請求書データのリスト。データが見つからない場合は空のリストを返します。
    """
    billing_data = []
    try:
        # PDFファイルを開く
        doc = fitz.open(pdf_path)
        # 1ページ目のみを対象とする
        page = doc[0]
        # ページからテキストを抽出
        raw_text = page.get_text()
        doc.close()

        # 1. ヘッダー（大項目）とその位置を特定する
        headers = []
        # "1 PCWL-0410:受入検査作業" や "2 送料" のようなパターンを検索
        header_regex = re.compile(r'"\d\s*([^":]+?)(?::受入検査作業)?"|"\d\s*(送料|その他)"')
        for match in header_regex.finditer(raw_text):
            # match.group(1) or match.group(2) でどちらかのパターンに一致したヘッダー名を取得
            header_name = (match.group(1) or match.group(2)).strip()
            headers.append({
                "name": header_name,
                "index": match.start()
            })

        # 2. 明細行のデータを特定する
        # "品名","単価","数量","単位","金額" のパターンを検索
        item_regex = re.compile(r'"([^"]+)"\s*,\s*"([¥\d,]+)"\s*,\s*"([\d\.]+)"\s*,\s*"[^"]"\s,\s*"([¥\d,]+)"')
        for match in item_regex.finditer(raw_text):
            name, unit_price_str, quantity_str, amount_str = match.groups()

            name = name.replace('\n', ' ').strip()

            # 表のヘッダー行（"品 名"など）はスキップ
            if name == '品 名' or '品名' in name:
                continue
            
            # 金額を数値に変換
            try:
                amount = float(amount_str.replace('¥', '').replace(',', ''))
            except ValueError:
                continue # 金額が数値でない場合はスキップ

            # 3. 各明細行がどのヘッダーに属するかを位置情報から判断
            current_header = ''
            # ヘッダーリストを逆順に見て、明細行より前にある直近のヘッダーを探す
            for header in reversed(headers):
                if match.start() > header['index']:
                    current_header = header['name']
                    break
            
            # 4. ルールに従って計算とフォーマットを行う
            # 税込金額を計算 (10%加算)
            tax_included_amount = int(amount * 1.1)
            
            # descriptionフィールドを作成
            description = f"品名: {current_header + ' - ' if current_header else ''}{name}, 単価: {unit_price_str}, 数量: {quantity_str}"

            billing_data.append({
                "description": description,
                "amount": f"¥{tax_included_amount:,}" # 3桁区切りにする
            })

        return billing_data

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {pdf_path}")
        return []
    except Exception as e:
        print(f"PDFの処理中にエラーが発生しました: {e}")
        return []


def export_to_csv(filename, data):
    """
    請求書データをCSVファイルに出力します。

    Args:
        filename (str): 出力するCSVファイル名。
        data (list): CSVに出力するデータのリスト（辞書形式）。
    """
    if not data:
        print("CSVに出力するデータがありません。")
        return

    header = ['品名・単価・数量', '金額（税込）']
    try:
        # encoding='utf-8-sig' はExcelで日本語が文字化けしないようにするため
        with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            for item in data:
                writer.writerow([item['description'], item['amount']])
        
        full_path = os.path.abspath(filename)
        print(f"\n'{filename}' の作成が完了しました。")
        print(f"ファイルは次の場所に保存されています: {full_path}")

    except IOError as e:
        print(f"ファイルの書き込み中にエラーが発生しました: {e}")


# メインの処理
if __name__ == "__main__":
    # ユーザーにPDFファイルのパスを入力してもらう
    pdf_file_path = input("読み込むPDFファイルのパスを入力してください: ").strip()

    # ファイルが存在するかチェック
    if os.path.exists(pdf_file_path):
        # PDFからデータを抽出
        extracted_data = parse_pdf_data(pdf_file_path)
        
        # 抽出したデータをCSVに出力
        output_filename = 'billing_summary.csv'
        export_to_csv(output_filename, extracted_data)
    else:
        print("指定されたパスにファイルが存在しません。パスを確認してください。")