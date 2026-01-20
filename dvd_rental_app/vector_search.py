import sqlite3
import numpy as np
import os
from sentence_transformers import SentenceTransformer

# Load model globally to avoid reloading (it caches)
# Use multilingual model to support Japanese queries against English descriptions
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

class VectorSearch:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dvd_embeddings (
                dvd_id INTEGER PRIMARY KEY,
                embedding BLOB
            )
        ''')
        conn.commit()
        conn.close()

    def add_dvd(self, dvd_id, text):
        model = get_model()
        embedding = model.encode(text)
        # Convert to bytes (float32)
        blob = embedding.astype(np.float32).tobytes()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('INSERT OR REPLACE INTO dvd_embeddings (dvd_id, embedding) VALUES (?, ?)', 
                     (dvd_id, blob))
        conn.commit()
        conn.close()

    def search(self, query_text, limit=5):
        model = get_model()
        query_embedding = model.encode(query_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT dvd_id, embedding FROM dvd_embeddings')
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for dvd_id, blob in rows:
            # Convert bytes back to numpy array
            doc_embedding = np.frombuffer(blob, dtype=np.float32)
            
            # Calculate cosine similarity
            # Cosine Similarity = (A . B) / (||A|| * ||B||)
            # Add simple check for zero norm to avoid division by zero
            norm_q = np.linalg.norm(query_embedding)
            norm_d = np.linalg.norm(doc_embedding)
            
            if norm_q == 0 or norm_d == 0:
                score = 0
            else:
                score = np.dot(query_embedding, doc_embedding) / (norm_q * norm_d)
                
            results.append((dvd_id, score))
            
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
