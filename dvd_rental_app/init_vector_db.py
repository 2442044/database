import sqlite3
import os
from vector_search import VectorSearch

# Database paths
# データベースファイルのパス設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'dvd_rental.db')
VECTOR_DB_PATH = os.path.join(BASE_DIR, 'dvd_vector.db')

def get_db_connection():
    """
    RDB (dvd_rental.db) への接続を取得します。
    """
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_vector_db():
    """
    ベクトルデータベースを初期化し、既存のDVDデータを登録します。
    RDBからDVD情報を取得し、整形したテキストをベクトル化してVector DBに保存します。
    """
    print("Initializing Vector Search DB...")
    
    # 1. Vector Search機能（DB含む）の初期化
    vs = VectorSearch(VECTOR_DB_PATH)
    
    # 2. SQLite (RDB) からDVDデータとジャンルを取得
    conn = get_db_connection()
    dvds = conn.execute('''
        SELECT d.dvd_id, d.title, d.description, g.name as genre_name 
        FROM dvds d
        LEFT JOIN genres g ON d.genre_id = g.genre_id
    ''').fetchall()
    conn.close()
    
    print(f"Found {len(dvds)} DVDs in SQLite.")
    
    count = 0
    for dvd in dvds:
        # 説明文がない場合はスキップ
        if not dvd['description']:
            continue
            
        # 検索精度向上のため、タイトル・ジャンル・説明文を自然言語形式で結合してベクトル化します
        enriched_text = f"{dvd['title']}。ジャンルは{dvd['genre_name']}。{dvd['description']}"
            
        print(f"Vectorizing DVD {dvd['dvd_id']}: {dvd['title']}...")
        # ベクトル化して保存
        vs.add_dvd(dvd['dvd_id'], enriched_text)
        count += 1
    
    print(f"Successfully vectorized and stored {count} DVD descriptions.")

if __name__ == "__main__":
    init_vector_db()
