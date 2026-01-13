from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

import os
DATABASE = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # 統計情報の取得
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    dvd_count = conn.execute('SELECT COUNT(*) FROM dvds').fetchone()[0]
    rental_count = conn.execute('SELECT COUNT(*) FROM rentals WHERE return_date IS NULL').fetchone()[0]
    
    # 最近のレンタル情報
    recent_rentals = conn.execute('''
        SELECT r.*, u.name as user_name, d.title as dvd_title 
        FROM rentals r
        JOIN users u ON r.user_id = u.user_id
        JOIN dvds d ON r.dvd_id = d.dvd_id
        ORDER BY r.rental_date DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', user_count=user_count, dvd_count=dvd_count, rental_count=rental_count, recent_rentals=recent_rentals)

@app.route('/dvds')
def dvds():
    conn = get_db_connection()
    dvds = conn.execute('''
        SELECT d.*, g.name as genre_name 
        FROM dvds d 
        LEFT JOIN genres g ON d.genre_id = g.genre_id
    ''').fetchall()
    conn.close()
    return render_template('dvds.html', dvds=dvds)

@app.route('/rent', methods=['POST'])
def rent_dvd():
    user_id = request.form['user_id']
    dvd_id = request.form['dvd_id']
    
    conn = get_db_connection()
    try:
        # トランザクション開始
        conn.execute('BEGIN TRANSACTION')
        
        # 在庫チェック
        dvd = conn.execute('SELECT stock_count FROM dvds WHERE dvd_id = ?', (dvd_id,)).fetchone()
        if not dvd or dvd['stock_count'] <= 0:
            flash('在庫がありません。', 'error')
            conn.rollback()
            return redirect(url_for('index'))
        
        # rentalsに追加
        conn.execute('INSERT INTO rentals (user_id, dvd_id) VALUES (?, ?)', (user_id, dvd_id))
        
        # 在庫を減らす
        conn.execute('UPDATE dvds SET stock_count = stock_count - 1 WHERE dvd_id = ?', (dvd_id,))
        
        conn.commit()
        flash('レンタル処理が完了しました。', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/return/<int:rental_id>')
def return_dvd(rental_id):
    conn = get_db_connection()
    try:
        conn.execute('BEGIN TRANSACTION')
        
        rental = conn.execute('SELECT dvd_id FROM rentals WHERE rental_id = ?', (rental_id,)).fetchone()
        if rental:
            dvd_id = rental['dvd_id']
            # 返却日更新
            conn.execute('UPDATE rentals SET return_date = CURRENT_TIMESTAMP, status = "returned" WHERE rental_id = ?', (rental_id,))
            # 在庫を戻す
            conn.execute('UPDATE dvds SET stock_count = stock_count + 1 WHERE dvd_id = ?', (dvd_id,))
            
            conn.commit()
            flash('返却処理が完了しました。', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
