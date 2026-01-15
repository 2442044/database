import sqlite3
import os

def check_data():
    db_path = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- Genres ---")
    cursor.execute("SELECT * FROM genres")
    for row in cursor.fetchall():
        print(row)

    print("\n--- Users ---")
    cursor.execute("SELECT * FROM users")
    for row in cursor.fetchall():
        print(row)

    print("\n--- DVDs ---")
    cursor.execute("SELECT * FROM dvds")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == '__main__':
    check_data()
