import sqlite3
import os
from vector_search import VectorSearch

# Database paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'dvd_rental.db')
# We store embeddings in the same DB file or a separate one? 
# vector_search.py allows separate. Let's keep it separate to not mess with existing schema easily.
VECTOR_DB_PATH = os.path.join(BASE_DIR, 'dvd_vector.db')

def get_db_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_vector_db():
    print("Initializing Vector Search DB...")
    
    # 1. Initialize Vector Search
    vs = VectorSearch(VECTOR_DB_PATH)
    
    # 2. Fetch Data from SQLite
    conn = get_db_connection()
    dvds = conn.execute('SELECT dvd_id, title, description FROM dvds').fetchall()
    conn.close()
    
    print(f"Found {len(dvds)} DVDs in SQLite.")
    
    count = 0
    for dvd in dvds:
        # Skip if description is empty
        if not dvd['description']:
            continue
            
        print(f"Vectorizing DVD {dvd['dvd_id']}: {dvd['title']}...")
        vs.add_dvd(dvd['dvd_id'], dvd['description'])
        count += 1
    
    print(f"Successfully vectorized and stored {count} DVD descriptions.")

if __name__ == "__main__":
    init_vector_db()
