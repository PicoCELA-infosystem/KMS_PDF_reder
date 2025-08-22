import pandas as pd
import sys
import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_best_match_header(text, headers_map):
    for key, variations in headers_map.items():
        for var in variations:
            if var in text:
                return key
    return None

def parse_ocr_text(ocr_text):
    lines = ocr_text.strip().split('\n')
    
    data = []
    # ヘッダーのバリエーションを定義
    headers_map = {
        '品名': ['品名', '品'],
        '単価(円)': ['単価', '単'],
        '数量': ['数量', '数'],
        '金額(円)': ['金額', '金'],
        '備考': ['備考', '備']
    }
    
    # どの行からデータが始まるかを特定（「受入検査作業」などを含む行）
    start_processing = False
    for line in lines:
        # データ行の開始キーワード
        if any(keyword in line for keyword in ['受入検査', '発送業務', '識別作業', '送料']):
            start_processing = True
        
        if not start_processing:
            continue

        # 金額らしきもの（円マークや数字）がある行をデータ行と判断
        if re.search(r'[¥\d,.]+', line):
            # ¥やカンマを除去して数字のリストを取得
            numbers = re.findall(r'[\d,.]+', line.replace(',', ''))
            text_parts = re.split(r'\s+', line)
            
            # 簡易的な行解析
            # この部分はPDFのレイアウトに強く依存するため、調整が必要になる可能性が高い
            if len(numbers) >= 2 and len(text_parts) > 1:
                row = {
                    '品名': text_parts[0],
                    '単価(円)': numbers[0] if len(numbers) > 0 else '',
                    '数量': numbers[1] if len(numbers) > 1 else '',
                    '金額(円)': numbers[2] if len(numbers) > 2 else '',
                    '備考': text_parts[-1] if text_parts[-1] not in numbers else ''
                }
                data.append(row)

    if not data:
        print("OCR結果からデータを抽出できませんでした。")
        return None

    df = pd.DataFrame(data)
    return df

def ocr_and_create_csv(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        ocr_text = pytesseract.image_to_string(image, lang='jpn')
        
        df = parse_ocr_text(ocr_text)

        if df is not None:
            output_path = os.path.join(os.path.dirname(__file__), 'output.csv')
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"CSVファイルを {output_path} に出力しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        ocr_and_create_csv(pdf_path)
    else:
        print("PDFファイルのパスを引数として指定してください。")
