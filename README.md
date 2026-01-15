# DVD Rental App (DVDレンタル管理システム)

![Home Screen](docs/home.png)

## 概要

Flaskを使用したDVDレンタル管理Webアプリケーションです。
ユーザー管理、DVD在庫管理、貸出・返却処理を直感的な操作で行うことができます。

本アプリケーションは、プログラミング学習や小規模なレンタル管理業務のプロトタイプとして設計されています。

---

## プロジェクト構成

- **バックエンド:** Flask (Python)
- **データベース:** SQLite
- **環境構築:** Docker / Docker Compose

### 主なファイル・ディレクトリ
- `app.py`: アプリケーションのメインロジック（ルーティング、DB操作）
- `templates/`: 画面のHTMLテンプレート（Jinja2）
- `dvd_rental.db`: SQLiteデータベースファイル
- `ER図/`: データベース設計書（SchemaSpyにより生成）
- `docker-compose.yml`: Docker環境での起動設定
- `Dockerfile`: アプリケーションコンテナの定義

---

## 起動方法

### Dockerを使用する場合 (推奨)
Docker Desktopなどがインストールされている環境であれば、以下のコマンドですぐに起動できます。

1. **起動**
   ```bash
   docker compose up
   ```
   初回起動時はビルドが行われます。

2. **アクセス**
   ブラウザで `http://localhost:80` (または設定によりポートが異なる場合があります) にアクセスしてください。

3. **終了**
   ```bash
   docker compose down
   ```

### ローカルPython環境で起動する場合
Pythonがインストールされている場合、以下の手順で起動可能です。

1. **依存ライブラリのインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **データベースの初期化** (初回のみ)
   ```bash
   python init_db.py
   ```

3. **アプリの起動**
   ```bash
   python app.py
   ```
   ブラウザで `http://localhost:5000` にアクセスしてください。

---

## 機能・画面紹介

### 1. ダッシュボード (ホーム)
システムの利用状況を一目で確認できるダッシュボードです。
- 登録ユーザー数、DVD数、貸出中件数
- 最近のレンタル履歴

![Dashboard](docs/home.png)

### 2. DVD管理
在庫DVDの検索、新規登録、編集、削除機能を提供します。
- タイトルやジャンルによる絞り込み検索
- 在庫数や保管場所の管理

![DVD List](docs/dvds.png)

### 3. ユーザー管理
会員情報の管理を行います。
- 会員の新規登録、編集、削除
- 貸出履歴がある会員の保護（削除防止）

![User List](docs/users.png)

### 4. 貸出・返却
シンプルな操作で貸出と返却の処理が行えます。
- ユーザーとDVDを選択して貸出
- 未返却一覧からのワンクリック返却処理

![Rental](docs/rental.png)

---

## データベース設計 (ER図)

本システムのデータベース構造は以下のようになっています。

![ER図](dvd_rental_app/ER%E5%9B%B3/diagrams/summary/relationships.real.large.png)

### テーブル概要
- **users**: 会員情報を管理
- **dvds**: DVDの商品情報・在庫を管理
- **genres**: DVDのジャンル定義
- **rentals**: 貸出・返却のトランザクション履歴

詳細なカラム定義や制約については、`dvd_rental_app/ER%E5%9B%B3/index.html` を開くことで詳細なドキュメントを閲覧できます。
