import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
    print(f"Initializing database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Genres table (#3 RDB Table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS genres (
        genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # Users table (#3 RDB Table, #8 Tuning: UNIQUE constraint acts as an index)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_code TEXT UNIQUE,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        birth_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # DVDs table (#3 RDB Table, #8 Normalization)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dvds (
        dvd_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre_id INTEGER, -- #5 Foreign Key: 外部キーによるリレーション
        release_date DATE,
        stock_count INTEGER CHECK(stock_count >= 0),
        total_stock INTEGER DEFAULT 1,
        storage_location TEXT,
        description TEXT,
        FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
    )
    ''')

    # Rentals table (#3 RDB Table: 多対多を解消する中間テーブル)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rentals (
        rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        dvd_id INTEGER NOT NULL,
        rental_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        return_date DATETIME,
        status TEXT DEFAULT 'rented',
        FOREIGN KEY (user_id) REFERENCES users (user_id), -- #5 Foreign Key
        FOREIGN KEY (dvd_id) REFERENCES dvds (dvd_id)   -- #5 Foreign Key
    )
    ''')

    # Initial Data
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('アクション')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('コメディ')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('ドラマ')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('SF')")
    
    # Add some sample DVDs if none exist
    cursor.execute("SELECT COUNT(*) FROM dvds")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO dvds (title, genre_id, stock_count, storage_location) VALUES ('インセプション', 4, 5, 'A-1')")
        cursor.execute("INSERT INTO dvds (title, genre_id, stock_count, storage_location) VALUES ('ダークナイト', 1, 3, 'A-2')")
        cursor.execute("INSERT INTO users (name, address, phone, birth_date, member_code) VALUES ('山田 太郎', '東京都新宿区', '090-1234-5678', '1990-01-01', 'M00001')")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
