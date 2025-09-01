# PDF請求書CSV変換ツール

## 1. 概要

このツールは、PDF形式の請求書ファイルをアップロードし、その内容をAIが解析してCSV形式のデータに変換するためのウェブアプリケーションです。手作業でのデータ入力の手間を省き、迅速に請求書情報をデータ化することを目的としています。

## 2. ご利用方法

**ツールURL:** https://picocela-infosystem.github.io/KMS_PDF_reder/

詳しい使い方は、以下のご利用ガイドを参照してください。
- **[ご利用ガイド (user_guide.html)](user_guide.html)**

### 初回設定：APIキー

ツールの初回利用時には、GoogleのAIを動かすための「Gemini APIキー」の設定が必要です。設定方法は以下のガイドで詳しく説明しています。
- **[Gemini APIキー 取得・設定ガイド (GEMINI_API_GUIDE.html)](GEMINI_API_GUIDE.html)**

### Excelへの貼り付け方法

出力されたCSVデータをExcelで正しく開く方法は、以下のガイドを参照してください。
- **[Excel: 区切り位置を使ったデータの貼り付け方法 (Excel_Delimiter_Manual.html)](Excel_Delimiter_Manual.html)**


## 3. 必要な環境

- パソコン
- Google ChromeやMicrosoft EdgeなどのモダンなWebブラウザ
- インターネット接続 (ツールの動作に必須です)

## 4. ローカル環境での実行

配布されたZIPファイルを解凍し、`index.html` をWebブラウザで開くことでも利用可能です。その際、以下のファイルがすべて同じ階層に配置されている必要があります。

```
/
|-- index.html
|-- user_guide.html
|-- GEMINI_API_GUIDE.html
|-- Excel_Delimiter_Manual.html
|-- prompt.js
|-- styles/
|   |-- main.css
|   |-- manual.css
|-- README.md
```

## 5. 開発者向け情報

このプロジェクトのソースコードはGitHubで管理されています。
- **リポジトリURL:** `https://github.com/PicoCELA-infosystem/KMS_PDF_reder`

MarkdownからHTMLへの変換方法など、開発に関する詳細は `no_push/DEVELOPMENT.md` を参照してください。
