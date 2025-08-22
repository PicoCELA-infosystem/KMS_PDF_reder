import sys
import pandas as pd
import camelot
import re
import csv

def extract_table_from_pdf(pdf_path, page_number='1'):
    """
    指定されたPDFのページからテーブルを抽出します。

    Args:
        pdf_path (str): PDFファイルのパス
        page_number (str): 抽出するページ番号。デフォルトは'1'です。

    Returns:
        camelot.core.TableList: 抽出されたテーブルのリスト
    """
    try:
        tables = camelot.read_pdf(pdf_path, pages=page_number, flavor='stream', table_areas=['0,800,600,0'], split_text=True)
        return tables
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        return None

def find_header_row(df, headers):
    """
    DataFrame内で指定されたヘッダー行を見つけ、そのインデックスを返します。

    Args:
        df (pd.DataFrame): 検索対象のDataFrame。
        headers (list): 探しているヘッダー名のリスト。

    Returns:
        int or None: ヘッダー行のインデックス。見つからない場合はNone。
    """
    for idx, row in df.iterrows():
        # ヘッダーのリストに含まれる単語がすべて行に含まれているかチェック
        # 大文字小文字を区別せず、全角/半角スペースを考慮
        row_str = " ".join(row.fillna("").astype(str).str.replace(r'\s+', ' ', regex=True))
        
        # '品名'が単独で含まれている場合と、'品'と'名'が分かれている場合を考慮
        pname_found = ('品名' in row_str or ('品' in row_str and '名' in row_str))

        if pname_found and '単価(円)' in row_str and '数量' in row_str and '金額(円)' in row_str and '備考' in row_str:
            return idx
    return None

def process_table(tables, required_columns):
    """
    抽出されたテーブルを処理し、指定された列のデータを抽出します。

    Args:
        tables (camelot.core.TableList): 抽出されたテーブルのリスト
        required_columns (list): 抽出する列名のリスト

    Returns:
        list: 抽出された行データのリスト
    """
    extracted_rows = []
    
    if not tables or len(tables) == 0:
        print("No tables found in the PDF.", file=sys.stderr)
        return extracted_rows
        
    for table in tables:
        df = table.df.copy()
        
        # ヘッダー行を特定
        header_index = find_header_row(df, required_columns)
        if header_index is None:
            continue

        # ヘッダーより下の行を抽出
        data_df = df.iloc[header_index+1:]

        # ヘッダー列のインデックスを取得
        header_map = {}
        header_row = df.iloc[header_index].astype(str)
        header_row_normalized = [re.sub(r'[\s\(\)円\r\n]+', '', col).replace('品名','品').replace('金額','金額').replace('単価','単価').replace('数量','数量').replace('備考','備考') for col in header_row]
        for col in required_columns:
            # 正規表現で列名を検索
            match_col = None
            if col == '品名':
                # '品'と'名'が分かれているパターンに対応
                for idx, h in enumerate(header_row_normalized):
                    if '品' in h and '名' in h:
                        match_col = idx
                        break
            else:
                for idx, h in enumerate(header_row_normalized):
                    if re.search(re.sub(r'[\s\(\)円\r\n]+', '', col), h):
                        match_col = idx
                        break

            if match_col is not None:
                header_map[col] = match_col

        if not all(col in header_map for col in required_columns):
            print(f"Required columns not found in the table: {required_columns}", file=sys.stderr)
            continue
            
        # データをループして抽出
        for _, row in data_df.iterrows():
            # ヘッダー行の下に複数の空行がある場合があるので、最初の非空行から始める
            if row.isnull().all():
                continue

            extracted_row = []
            for col in required_columns:
                value = row.get(header_map.get(col, -1), '')
                # 不要な改行や余分なスペースを削除
                value = re.sub(r'[\r\n\s]+', ' ', str(value)).strip()
                extracted_row.append(value)
            
            # 全ての項目が空の場合はスキップ
            if all(val == '' for val in extracted_row):
                continue

            extracted_rows.append(extracted_row)
            
    return extracted_rows

def main():
    """
    メイン関数。コマンドライン引数からPDFパスを受け取り、処理を実行します。
    """
    if len(sys.argv) < 2:
        print("Usage: python script.py <pdf_file_path>", file=sys.stderr)
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    
    # 抽出する列を指定
    required_columns = ['品名', '単価(円)', '数量', '金額(円)', '備考']
    
    # PDFからテーブルを抽出
    tables = extract_table_from_pdf(pdf_path)
    
    # テーブルを処理してデータを取得
    extracted_data = process_table(tables, required_columns)
    
    # CSV形式で標準出力に出力
    writer = csv.writer(sys.stdout)
    writer.writerow(required_columns)
    for row in extracted_data:
        writer.writerow(row)

if __name__ == "__main__":
    main()
