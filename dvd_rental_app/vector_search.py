import sqlite3
import numpy as np
import os
from sentence_transformers import SentenceTransformer

# モデルをグローバル変数としてキャッシュし、再ロードを防ぎます
# 多言語対応モデルを使用し、日本語のクエリでも英語や日本語の説明文を検索できるようにします
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
_model = None

def get_model():
    """
    Embeddingモデルをロードして返します。
    既にロードされている場合はキャッシュされたモデルを返します。
    """
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

class VectorSearch:
    """
    ベクトル検索機能を提供するクラス。
    SQLiteを使用してベクトルデータ（Embedding）を管理します。
    """
    def __init__(self, db_path):
        """
        コンストラクタ。
        :param db_path: ベクトルデータを保存するSQLiteデータベースのパス
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        データベーステーブルを初期化します。
        dvd_id（主キー）とembedding（BLOB形式のベクトルデータ）を持つテーブルを作成します。
        """
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
        """
        DVDのテキスト情報をベクトル化してデータベースに保存します。
        :param dvd_id: DVDの一意なID
        :param text: ベクトル化する対象のテキスト（タイトル、説明文など）
        """
        model = get_model()
        # テキストをベクトル（数値の配列）に変換
        embedding = model.encode(text)
        # NumPy配列をバイト列（BLOB）に変換して保存用にシリアライズ
        blob = embedding.astype(np.float32).tobytes()
        
        conn = sqlite3.connect(self.db_path)
        # 既に存在する場合は上書き（REPLACE）
        conn.execute('INSERT OR REPLACE INTO dvd_embeddings (dvd_id, embedding) VALUES (?, ?)', 
                     (dvd_id, blob))
        conn.commit()
        conn.close()

    def search(self, query_text, limit=5):
        """
        入力されたクエリテキストに意味的に近いDVDを検索します。
        :param query_text: 検索キーワードや文章
        :param limit: 取得する最大件数
        :return: {'dvd_id': int, 'score': float} のリスト（スコア降順）
        """
        model = get_model()
        # クエリをベクトル化
        query_embedding = model.encode(query_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT dvd_id, embedding FROM dvd_embeddings')
        rows = cursor.fetchall()
        conn.close()
        
        # すべてのDVDベクトルとの類似度（スコア）を計算
        results = []
        for dvd_id, blob in rows:
            # BLOBからNumPy配列に復元
            doc_embedding = np.frombuffer(blob, dtype=np.float32)
            
            # コサイン類似度の計算: (A . B) / (||A|| * ||B||)
            norm_q = np.linalg.norm(query_embedding)
            norm_d = np.linalg.norm(doc_embedding)
            
            if norm_q == 0 or norm_d == 0:
                score = 0
            else:
                score = np.dot(query_embedding, doc_embedding) / (norm_q * norm_d)
                
            results.append({'dvd_id': dvd_id, 'score': float(score)})
            
        # スコアが高い順にソートして上位を返す
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
