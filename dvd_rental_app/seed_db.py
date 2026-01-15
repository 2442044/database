import sqlite3
import os

def seed_data():
    db_path = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
    print(f"Seeding data into: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Genres (already has Action, Comedy, Drama, Sci-Fi)
    genres = [('Horror',), ('Animation',), ('Romance',)]
    cursor.executemany("INSERT OR IGNORE INTO genres (name) VALUES (?)", genres)
    
    # Get genre IDs for reference
    cursor.execute("SELECT genre_id, name FROM genres")
    genre_map = {name: gid for gid, name in cursor.fetchall()}

    # Users
    users = [
        ('M00002', '佐藤 花子', '神奈川県横浜市', '080-8765-4321', '1995-05-15'),
        ('M00003', '鈴木 一郎', '大阪府大阪市', '070-1111-2222', '1985-11-20'),
        ('M00004', '高橋 健太', '愛知県名古屋市', '090-9999-8888', '2000-03-10')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO users (member_code, name, address, phone, birth_date) 
        VALUES (?, ?, ?, ?, ?)
    """, users)

    # DVDs
    dvds = [
        ('Interstellar', genre_map.get('Sci-Fi'), 4, 4, 'B-1', 'A team of explorers travel through a wormhole in space.'),
        ('Toy Story', genre_map.get('Animation'), 5, 5, 'C-1', 'A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him.'),
        ('The Godfather', genre_map.get('Drama'), 2, 2, 'A-3', 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.'),
        ('Spirited Away', genre_map.get('Animation'), 3, 3, 'C-2', 'During her family''s move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits.'),
        ('Your Name.', genre_map.get('Romance'), 6, 6, 'D-1', 'Two strangers find themselves linked in a bizarre way.')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO dvds (title, genre_id, stock_count, total_stock, storage_location, description) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, dvds)

    conn.commit()
    conn.close()
    print("Sample data inserted successfully.")

if __name__ == '__main__':
    seed_data()
