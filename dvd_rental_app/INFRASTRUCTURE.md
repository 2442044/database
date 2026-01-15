# インフラストラクチャ構築ガイド

## 1. システム構成 (Architecture)

本システムは、Web 3層アーキテクチャ（Web Server, Application Server, Database）をDockerコンテナを用いて構築しています。

```mermaid
graph TD
    User((User)) -->|Internet| ngrok[ngrok Tunnel]
    subgraph Docker Host
        ngrok -->|Localhost:80| Nginx[Web Server (Nginx)]
        Nginx -->|Reverse Proxy| App[App Server (Flask/Gunicorn)]
        App -->|File Access| DB[(SQLite DB)]
    end
```

- **Web Server**: Nginx (リバースプロキシとして動作、静的配信も可能)
- **Application Server**: Python Flask + Gunicorn (WSGIサーバー)
- **Database**: SQLite (アプリケーションコンテナ内のファイルとして永続化)

## 2. ローカル環境の構築手順 (Infra)

DockerおよびDocker Composeがインストールされている前提です。

1.  **コンテナのビルドと起動**
    ```bash
    docker-compose up -d --build
    ```

2.  **動作確認**
    ブラウザで `http://localhost` にアクセスしてください。
    正常に起動していれば、DVDレンタルアプリが表示されます。

3.  **停止**
    ```bash
    docker-compose down
    ```

## 3. インターネット公開手順 (Infra)

要件にある「Internetからアクセスできるようにする」ためには、ローカル環境を外部にトンネリングするツール `ngrok` の利用を推奨します。

### 手順

1.  **ngrokのインストール**
    [ngrok公式サイト](https://ngrok.com/download)からダウンロードし、インストールしてください。

2.  **ngrokの起動**
    以下のコマンドを実行して、ローカルの80番ポート（Nginx）を公開します。
    ```bash
    ngrok http 80
    ```

3.  **アクセスの確認**
    ngrokが起動すると、以下のようなURLが表示されます。
    ```
    Forwarding      https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:80
    ```
    この `https://...` のURLにスマートフォンや外部PCからアクセスしてください。システムが利用可能であれば成功です。

---
**補足**: 
- データベースファイル `dvd_rental.db` はホスト側のディレクトリに同期（ボリュームマウント）されているため、コンテナを再起動してもデータは保持されます。
- 本番環境（AWS, Azure等）へのデプロイが必要な場合は、このDocker構成をそのまま利用可能です（ただしSQLiteではなくPostgreSQL等のマネージドDBへの切り替えを推奨）。
