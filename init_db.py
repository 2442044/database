import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
    print(f"Initializing database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Genres table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS genres (
        genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # Users table
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

    # DVDs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dvds (
        dvd_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre_id INTEGER,
        release_date DATE,
        stock_count INTEGER CHECK(stock_count >= 0),
        total_stock INTEGER DEFAULT 1,
        storage_location TEXT,
        description TEXT,
        FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
    )
    ''')

    # Rentals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rentals (
        rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        dvd_id INTEGER NOT NULL,
        rental_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        return_date DATETIME,
        status TEXT DEFAULT 'rented',
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (dvd_id) REFERENCES dvds (dvd_id)
    )
    ''')

    # Initial Data
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('Action')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('Comedy')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('Drama')")
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES ('Sci-Fi')")
    
    # Add some sample DVDs if none exist
    cursor.execute("SELECT COUNT(*) FROM dvds")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO dvds (title, genre_id, stock_count, storage_location) VALUES ('Inception', 4, 5, 'A-1')")
        cursor.execute("INSERT INTO dvds (title, genre_id, stock_count, storage_location) VALUES ('The Dark Knight', 1, 3, 'A-2')")
        cursor.execute("INSERT INTO users (name, address, phone, birth_date, member_code) VALUES ('山田 太郎', '東京都新宿区', '090-1234-5678', '1990-01-01', 'M00001')")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
