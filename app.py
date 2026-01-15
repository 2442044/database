from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

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
    active_rentals = conn.execute('SELECT COUNT(*) FROM rentals WHERE return_date IS NULL').fetchone()[0]
    
    # 本日の貸出数
    today = datetime.date.today().strftime('%Y-%m-%d')
    today_rentals = conn.execute('SELECT COUNT(*) FROM rentals WHERE date(rental_date) = ?', (today,)).fetchone()[0]

    # 最近のレンタル情報
    recent_rentals = conn.execute('''
        SELECT r.*, u.name as user_name, d.title as dvd_title 
        FROM rentals r
        JOIN users u ON r.user_id = u.user_id
        JOIN dvds d ON r.dvd_id = d.dvd_id
        ORDER BY r.rental_date DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    now = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')
    return render_template('index.html', 
                         user_count=user_count, 
                         dvd_count=dvd_count, 
                         active_rentals=active_rentals, 
                         today_rentals=today_rentals,
                         recent_rentals=recent_rentals,
                         now=now)

@app.route('/dvds')
def dvds():
    query = request.args.get('query', '')
    genre_id = request.args.get('genre_id', '')
    
    conn = get_db_connection()
    sql = '''
        SELECT d.*, g.name as genre_name 
        FROM dvds d 
        LEFT JOIN genres g ON d.genre_id = g.genre_id
        WHERE d.title LIKE ?
    '''
    params = [f'%{query}%']
    
    if genre_id:
        sql += ' AND d.genre_id = ?'
        params.append(genre_id)
        
    dvds = conn.execute(sql, params).fetchall()
    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    return render_template('dvds.html', dvds=dvds, genres=genres, query=query, genre_id=genre_id)

@app.route('/add_dvd', methods=['GET', 'POST'])
def add_dvd():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_date = request.form['release_date']
        stock_count = request.form['stock_count']
        storage_location = request.form['storage_location']
        description = request.form['description']
        
        # total_stock も stock_count と同じにする
        total_stock = stock_count

        try:
            # 空文字の場合は None (NULL) にする
            if not genre_id: genre_id = None
            if not release_date: release_date = None

            conn.execute('''
                INSERT INTO dvds (title, genre_id, release_date, stock_count, total_stock, storage_location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, genre_id, release_date, stock_count, total_stock, storage_location, description))
            conn.commit()
            flash('新規商品を登録しました。', 'success')
            return redirect(url_for('dvds'))
        except Exception as e:
            flash(f'登録エラー: {str(e)}', 'error')
            
    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    return render_template('add_dvd.html', genres=genres)

@app.route('/users', methods=['GET', 'POST'])
def users():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        birth_date = request.form['birth_date']
        try:
            conn.execute('INSERT INTO users (name, address, phone, birth_date) VALUES (?, ?, ?, ?)',
                         (name, address, phone, birth_date))
            conn.commit()
            flash('ユーザーを登録しました。', 'success')
        except Exception as e:
            flash(f'登録エラー: {str(e)}', 'error')
        return redirect(url_for('users'))

    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/rental')
def rental_page():
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, name FROM users').fetchall()
    # 在庫があるDVDのみ表示
    dvds = conn.execute('SELECT dvd_id, title FROM dvds WHERE stock_count > 0').fetchall()
    # 貸出中のもの
    active_rentals = conn.execute('''
        SELECT r.*, u.name as user_name, d.title as dvd_title 
        FROM rentals r
        JOIN users u ON r.user_id = u.user_id
        JOIN dvds d ON r.dvd_id = d.dvd_id
        WHERE r.return_date IS NULL
        ORDER BY r.rental_date DESC
    ''').fetchall()
    conn.close()
    return render_template('rental.html', users=users, dvds=dvds, active_rentals=active_rentals)

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

        # 既にレンタル中かチェック
        existing_rental = conn.execute('''
            SELECT * FROM rentals 
            WHERE user_id = ? AND dvd_id = ? AND return_date IS NULL
        ''', (user_id, dvd_id)).fetchone()
        
        if existing_rental:
            flash('このユーザーは既にこのDVDをレンタル中です。', 'error')
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
    # host='0.0.0.0' を指定することで、同じネットワーク内の他のPCからもアクセス可能になります
    app.run(debug=True, host='0.0.0.0', port=5000)
