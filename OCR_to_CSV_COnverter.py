import requests
import json
import base64
import os
import re

def ocr_pdf_to_json(pdf_path, output_json_path, api_key):
    """
    OCR処理を開始し、結果をJSONファイルとして保存する。
    """
    print(f"1. PDFファイル '{pdf_path}' のOCR処理を開始します...")
    try:
        # PDFをBase64でエンコード
        with open(pdf_path, 'rb') as pdf_file:
            content = base64.b64encode(pdf_file.read()).decode('utf-8')

        # APIリクエストのペイロード
        request_data = {
            "requests": [
                {
                    "image": {
                        "content": content
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION"
                        }
                    ]
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        # API呼び出し
        response = requests.post(api_url, data=json.dumps(request_data), headers=headers)
        response.raise_for_status()
        result = response.json()

        # 結果をJSONファイルに保存
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"   OCR結果を '{output_json_path}' に保存しました。")
    
    except requests.exceptions.RequestException as e:
        print(f"エラー: APIリクエストに失敗しました: {e}")
    except Exception as e:
        print(f"エラー: PDF処理中に予期せぬエラーが発生しました: {e}")


def process_json_to_csv(json_path, csv_path, tax_rate=0.10):
    """
    OCR結果のJSONファイルを読み込み、CSV形式に変換する。
    """
    print(f"2. JSONファイル '{json_path}' のデータ加工を開始します...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "fullTextAnnotation" not in data["responses"][0]:
            print("   JSONデータにテキスト情報が見つかりませんでした。")
            return
            
        text = data["responses"][0]["fullTextAnnotation"]["text"]
        
        # OCR結果の前処理
        cleaned_text = re.sub(r'[\r\n]+', '\n', text).strip()
        lines = cleaned_text.split('\n')
        
        output_lines = ['明細名,税込金額']
        
        # OCR結果のばらつきを考慮した解析ロジック
        parent_item = None
        for i, line in enumerate(lines):
            line = line.strip()

            # 親の品目名 (例: PCWL-0510:) を抽出
            if re.match(r'PCWL-\d+.*:', line):
                parent_item = line.replace(':', '').strip()
                continue

            # "品名"と"単価","数量","単位","金額"のパターンを抽出
            if re.search(r'¥(\d+(?:,\d+)*)\s+\d+\s+台', line):
                item_name_match = re.search(r'^"([^"]+)"', line)
                price_match = re.search(r'¥(\d+(?:,\d+)*)', line)
                quantity_match = re.search(r'¥\d+(?:,\d+)*\s+(\d+\.?\d*)\s+台', line)

                if item_name_match and price_match and quantity_match:
                    item_name = item_name_match.group(1).strip()
                    unit_price = int(price_match.group(1).replace(',', ''))
                    quantity = float(quantity_match.group(1))

                    # 税込金額を計算
                    tax_included_price = int((unit_price * quantity) * (1 + tax_rate))
                    
                    detail_name = f'"{parent_item} {item_name} {int(quantity)}台@{unit_price}"'
                    output_lines.append(f'{detail_name},{tax_included_price}')
                    parent_item = None

            # "送料"、"保管費用"、"部材" などの明細を抽出
            elif "送料" in line or "保管費用" in line or "部材" in line:
                price_match = re.search(r'¥(\d+(?:,\d+)*)$', line.replace(',', ''))
                if price_match:
                    total_price = int(price_match.group(1))
                    item_name = re.sub(r'¥\d+(?:,\d+)*$', '', line).strip()
                    output_lines.append(f'"{item_name}",{total_price}')
            
            # 親項目がなく、単体で金額情報を持つ明細を抽出
            elif re.search(r'¥(\d+(?:,\d+)*)$', line.replace(',', '')):
                price_match = re.search(r'¥(\d+(?:,\d+)*)$', line.replace(',', ''))
                if price_match:
                    total_price = int(price_match.group(1))
                    item_name = re.sub(r'¥\d+(?:,\d+)*$', '', line).strip()
                    output_lines.append(f'"{item_name}",{total_price}')

        # CSVファイルとして保存
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"   CSVファイル '{csv_path}' の生成が完了しました。")

    except Exception as e:
        print(f"エラー: JSON処理中に予期せぬエラーが発生しました: {e}")

# --- 実行部分 ---
if __name__ == "__main__":
    # TODO: 1. ここにGoogle Cloud Vision APIのキーを貼り付けてください。
    API_KEY = "AIzaSyDxdSFTCJHoJ-B_oUp3R1LwiKy2jjtqUxE"
    
    # TODO: 2. 処理したいPDFファイルのパスを指定してください。
    PDF_FILE_PATH = "仕様書/0f3fcb71-6daf-4622-b138-4b176603c42b.pdf"
    
    # 出力ファイル名
    JSON_FILE_PATH = "invoice_ocr_result.json"
    CSV_FILE_PATH = "invoice_data.csv"
    
    # APIキーの検証とPDFファイルの存在チェック
    if API_KEY == "YOUR_API_KEY_HERE":
        print("エラー: APIキーを設定してください。")
    elif not os.path.exists(PDF_FILE_PATH):
        print(f"エラー: 指定されたPDFファイルが見つかりません: '{PDF_FILE_PATH}'")
    else:
        # OCR処理を実行し、結果をJSONファイルに保存
        ocr_pdf_to_json(PDF_FILE_PATH, JSON_FILE_PATH, API_KEY)
        
        # OCR結果が正常に保存されていれば、データ加工を実行
        if os.path.exists(JSON_FILE_PATH):
            process_json_to_csv(JSON_FILE_PATH, CSV_FILE_PATH)
