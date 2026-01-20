# データベース講義内容の適用解説

本DVDレンタルシステムでは、大学の講義で扱われたデータベースの重要概念が随所に取り入れられています。発表時に活用できるよう、各項目に関連するソースコードの箇所と解説をまとめました。

---

## #3 RDB Table (リレーショナルデータベースのテーブル構造)

システムは4つの主要なテーブルで構成されています。
- **ファイル:** `dvd_rental_app/init_db.py`

| テーブル名 | 用途 |
| :--- | :--- |
| `users` | 会員情報を管理 (名前、住所、電話番号など) |
| `dvds` | 在庫情報を管理 (タイトル、ジャンル、在庫数など) |
| `genres` | DVDのカテゴリーを管理 |
| `rentals` | 貸出履歴と現在のステータスを管理 |

**解説ポイント:**
データが単一のリストではなく、意味のある単位（エンティティ）ごとに「テーブル」として分割されている点が、RDBの基本構造です。

---

## #4 SQL, Transaction (SQL操作とトランザクション)

### SQL (Structured Query Language)
システム全体で、データの取得(`SELECT`)、追加(`INSERT`)、更新(`UPDATE`)、削除(`DELETE`)のCRUD操作をSQLで行っています。
- **例 (データの絞り込み検索):** `app.py` の `dvds()` 関数内
  ```sql
  SELECT d.*, g.name as genre_name FROM dvds d LEFT JOIN genres g ON d.genre_id = g.genre_id WHERE d.title LIKE ?
  ```

### Transaction (トランザクション)
貸出処理や返却処理では、データの整合性を保つためにトランザクションを利用しています。
- **ファイル:** `dvd_rental_app/app.py` の `rent_dvd()` 関数
- **処理内容:**
  1. `BEGIN TRANSACTION`: トランザクションの開始
  2. `rentals` テーブルへの挿入
  3. `dvds` テーブルの在庫数(`stock_count`)を減らす
  4. `COMMIT`: すべて成功すれば確定。失敗すれば `ROLLBACK`。

**解説ポイント:**
「貸出履歴は増えたが在庫が減らなかった」という矛盾（不整合）を防ぐために、一連の処理を「不可分な単位」として扱っています。

---

## #5 Foreign Key, JOIN, SubQuery (外部キーと結合)

### Foreign Key (外部キー)
テーブル間の関連付けを強制し、参照整合性を維持しています。
- **例:** `dvds` テーブルの `genre_id` は `genres` テーブルを参照しています。
  ```sql
  FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
  ```

### JOIN (結合)
複数のテーブルを組み合わせて情報を表示します。
- **例 (内部結合 - JOIN):** `app.py` の `index()` 関数
  レンタル履歴にユーザー名とDVDタイトルを紐付けて表示。
  ```sql
  SELECT r.*, u.name as user_name, d.title as dvd_title FROM rentals r
  JOIN users u ON r.user_id = u.user_id
  JOIN dvds d ON r.dvd_id = d.dvd_id
  ```

### SubQuery (副問い合わせ / スカラサブクエリ的利用)
集計処理などでSQL内で別の値を参照しています。
- **例:** `app.py` の `index()` 関数内の統計取得など（個別の `SELECT COUNT(*)` 実行）。

---

## #8 正規化, DB Tuning

### 正規化 (Normalization)
データの重複を排除し、管理を容易にするために行っています。
- **第1正規形:** 各列が単一の値を持つ。
- **第2・3正規形:** `dvds` テーブルにジャンル名を持たせず、`genre_id` のみを持つことで、ジャンル名が変更されても1箇所の修正で済むように設計。

### DB Tuning
現状は小規模ですが、将来的なチューニングの基礎として以下を考慮しています。
- **Index (索引):** `users.member_code` や `users.phone` に `UNIQUE` 制約を付与しており、これらは自動的にインデックスとして機能し、検索が高速化されます。

---

## #10 分散DB, 列指向DB (システムへの適用可能性)

- **分散DB:** 本システムは現在 SQLite（単一ファイル）ですが、大規模化（全国展開など）した場合は、地理的に分散したサーバーでデータを同期する分散データベースへの移行が検討課題となります。
- **列指向DB:** 売上の分析やトレンド調査（OLAP）を行う場合、行単位ではなく「どのジャンルがいつ借りられたか」を列ごとに集計する列指向DB（BigQuery等）を分析基盤として組み合わせるのが有効です。

---

## #11 Vector DB (RAG), OTA

- **Vector DB (RAG):** DVDの説明文(`description`)をベクトル化して保存すれば、「泣ける映画を探して」「手に汗握るアクション」といった**自然言語による曖昧検索**を実装できます（現在は `LIKE` 検索）。これは最新のAI（RAG: Retrieval-Augmented Generation）技術との連携ポイントです。
- **OTA (Over-the-Air):** Dockerを利用しているため、システム構成の変更をコンテナイメージの更新としてOTAで配信可能な構成になっています。

---

**まとめ:**
このシステムは、基本的なRDBの原則（ACID特性や正規化）を忠実に守りつつ、将来の拡張（分析、AI活用、分散化）を見据えた設計になっています。
