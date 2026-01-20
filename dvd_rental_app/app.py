from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime
import os
from vector_search import VectorSearch

# Flaskアプリケーションの初期化
app = Flask(__name__)
# セッションやフラッシュメッセージ（通知）の暗号化に使用する秘密鍵
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# データベースファイルのパス設定
DATABASE = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), 'dvd_vector.db')

# VectorSearchの初期化
vector_search = VectorSearch(VECTOR_DB_PATH)

@app.template_filter('is_overdue')
def is_overdue(rental_date_str):
    """
    HTMLテンプレート内で使用するカスタムフィルタ。
    貸出日から7日以上経過しているかを判定し、期限切れならTrueを返します。
    """
    if not rental_date_str:
        return False
    try:
        # 文字列形式の時刻をPythonのdatetimeオブジェクトに変換
        rental_date = datetime.datetime.strptime(rental_date_str, '%Y-%m-%d %H:%M:%S')
        # 貸出期限を7日後に設定
        due_date = rental_date + datetime.timedelta(days=7)
        # 現在時刻が期限を過ぎているかチェック
        return datetime.datetime.now() > due_date
    except ValueError:
        return False

def get_db_connection():
    """
    データベースへの接続を確立し、列名でデータにアクセスできるように設定します。
    """
    conn = sqlite3.connect(DATABASE)
    # 取得した結果を辞書形式（conn.execute(...).fetchone()['column_name']）で扱えるようにする
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """
    ダッシュボード画面（ホームページ）を表示します。
    #5 JOIN: 複数のテーブルを結合して必要な情報を取得します。
    """
    conn = get_db_connection()
    
    # --- 統計情報の取得 (#5 SubQuery的利用) ---
    # 各テーブルのレコード数をカウントして概要を把握します
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    dvd_count = conn.execute('SELECT COUNT(*) FROM dvds').fetchone()[0]
    # return_date IS NULL は「まだ返却されていない」ことを意味します
    active_rentals = conn.execute('SELECT COUNT(*) FROM rentals WHERE return_date IS NULL').fetchone()[0]
    
    # 本日の貸出数を取得（SQLiteのdate関数で日付部分のみ比較）
    today = datetime.date.today().strftime('%Y-%m-%d')
    today_rentals = conn.execute('SELECT COUNT(*) FROM rentals WHERE date(rental_date) = ?', (today,)).fetchone()[0]

    # 期限切れの貸出数（julianday関数で日数の差分が7日を超えるものを抽出）
    overdue_rentals = conn.execute('''
        SELECT COUNT(*) FROM rentals 
        WHERE return_date IS NULL 
        AND julianday('now') - julianday(rental_date) > 7
    ''').fetchone()[0]

    # ジャンルごとの在庫統計（LEFT JOINでDVDが0件のジャンルも表示）
    genre_stats = conn.execute('''
        SELECT g.name, COUNT(d.dvd_id) as count, SUM(d.stock_count) as total_stock
        FROM genres g
        LEFT JOIN dvds d ON g.genre_id = d.genre_id
        GROUP BY g.genre_id
    ''').fetchall()

    # 最近のレンタル情報5件 (#5 JOIN)
    # rentalsテーブルにusers(名前)とdvds(タイトル)を紐付けて取得
    recent_rentals = conn.execute('''
        SELECT r.*, u.name as user_name, d.title as dvd_title 
        FROM rentals r
        JOIN users u ON r.user_id = u.user_id
        JOIN dvds d ON r.dvd_id = d.dvd_id
        ORDER BY r.rental_date DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    # 現在時刻をフォーマットして表示用に準備
    now = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')
    return render_template('index.html', 
                         user_count=user_count, 
                         dvd_count=dvd_count, 
                         active_rentals=active_rentals, 
                         today_rentals=today_rentals,
                         overdue_rentals=overdue_rentals,
                         genre_stats=genre_stats,
                         recent_rentals=recent_rentals,
                         now=now)

@app.route('/dvds')
def dvds():
    """
    DVD一覧を表示し、検索機能を提供します。
    """
    # 検索キーワードとジャンルIDをURLパラメータから取得
    query = request.args.get('query', '')
    genre_id = request.args.get('genre_id', '')
    search_type = request.args.get('search_type', 'keyword')
    
    conn = get_db_connection()
    dvds = []
    
    if query and search_type == 'semantic':
        # AI (ベクトル) 検索 + キーワード補正 (Hybrid Search)
        results = vector_search.search(query, limit=20) # 多めに取得
        
        if results:
            dvd_ids = [r['dvd_id'] for r in results]
            placeholders = ','.join('?' * len(dvd_ids))
            
            sql = f'''
                SELECT d.*, g.name as genre_name 
                FROM dvds d 
                LEFT JOIN genres g ON d.genre_id = g.genre_id
                WHERE d.dvd_id IN ({placeholders})
            '''
            params = list(dvd_ids)
            if genre_id:
                sql += ' AND d.genre_id = ?'
                params.append(genre_id)
                
            rows = conn.execute(sql, params).fetchall()
            
            # ハイブリッドスコアの計算
            # ベクトルスコアに、キーワードが含まれている場合のボーナスを加算
            scored_dvds = []
            vector_scores = {r['dvd_id']: r['score'] for r in results}
            
            for row in rows:
                did = row['dvd_id']
                score = vector_scores.get(did, 0)
                
                # キーワードが含まれている場合は大幅に加点（ブースト）
                # タイトル一致は特に高く
                title = row['title']
                desc = row['description'] or ""
                
                if query in title:
                    score += 2.0 # 強力なブースト
                elif query in desc:
                    score += 1.0 # 中程度のブースト
                
                scored_dvds.append({'row': row, 'score': score})
            
            # 最終的なスコアでソート
            scored_dvds.sort(key=lambda x: x['score'], reverse=True)
            dvds = [item['row'] for item in scored_dvds[:10]]
        else:
            dvds = []
    else:
        # 通常のキーワード検索（タイトル一致）
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

    # ジャンル選択プルダウン用のデータを取得
    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    
    return render_template('dvds.html', dvds=dvds, genres=genres, query=query, genre_id=genre_id, search_type=search_type)

@app.route('/add_dvd', methods=['GET', 'POST'])
def add_dvd():
    """
    新規DVDを登録します。
    POSTリクエスト時はフォームの内容をDBに保存します。
    """
    conn = get_db_connection()
    if request.method == 'POST':
        # フォーム入力を取得
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_date = request.form['release_date']
        stock_count = request.form['stock_count']
        storage_location = request.form['storage_location']
        description = request.form['description']
        
        # 初期登録時は、現在在庫と総在庫を同じにする
        total_stock = stock_count

        try:
            # 入力がない場合はNULL値（None）として扱う
            if not genre_id: genre_id = None
            if not release_date: release_date = None

            cursor = conn.execute('''
                INSERT INTO dvds (title, genre_id, release_date, stock_count, total_stock, storage_location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, genre_id, release_date, stock_count, total_stock, storage_location, description))
            new_dvd_id = cursor.lastrowid
            conn.commit()
            
            # Vector DBにも追加
            if description:
                try:
                    # ジャンル名を取得
                    genre_name = ""
                    if genre_id:
                        genre_row = conn.execute('SELECT name FROM genres WHERE genre_id = ?', (genre_id,)).fetchone()
                        if genre_row:
                            genre_name = genre_row['name']
                    
                    enriched_text = f"{title}。ジャンルは{genre_name}。{description}"
                    vector_search.add_dvd(new_dvd_id, enriched_text)
                except Exception as ve:
                    print(f"Vector DB Error: {ve}")

            flash('新規商品を登録しました。', 'success')
            return redirect(url_for('dvds'))
        except Exception as e:
            # エラー時はロールバック（SQLiteは自動ですが明示的に例外処理）して通知
            flash(f'登録エラー: {str(e)}', 'error')
            
    # ジャンル一覧を取得して登録フォームを表示
    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    return render_template('add_dvd.html', genres=genres)

@app.route('/edit_dvd/<int:dvd_id>', methods=['GET', 'POST'])
def edit_dvd(dvd_id):
    """
    既存DVDの情報を編集します。
    """
    conn = get_db_connection()
    if request.method == 'POST':
        # 更新する情報をフォームから取得
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_date = request.form['release_date']
        stock_count = request.form['stock_count']
        storage_location = request.form['storage_location']
        description = request.form['description']
        
        try:
            if not genre_id: genre_id = None
            if not release_date: release_date = None

            # 指定されたdvd_idのレコードを更新
            conn.execute('''
                UPDATE dvds 
                SET title = ?, genre_id = ?, release_date = ?, stock_count = ?, storage_location = ?, description = ?
                WHERE dvd_id = ?
            ''', (title, genre_id, release_date, stock_count, storage_location, description, dvd_id))
            conn.commit()
            
            # Vector DBも更新
            if description:
                try:
                    # ジャンル名を取得
                    genre_name = ""
                    if genre_id:
                        genre_row = conn.execute('SELECT name FROM genres WHERE genre_id = ?', (genre_id,)).fetchone()
                        if genre_row:
                            genre_name = genre_row['name']
                            
                    enriched_text = f"{title}。ジャンルは{genre_name}。{description}"
                    vector_search.add_dvd(dvd_id, enriched_text)
                except Exception as ve:
                    print(f"Vector DB Error: {ve}")

            flash('DVD情報を更新しました。', 'success')
            return redirect(url_for('dvds'))
        except Exception as e:
            flash(f'更新エラー: {str(e)}', 'error')
    
    # 編集対象のDVDデータを取得
    dvd = conn.execute('SELECT * FROM dvds WHERE dvd_id = ?', (dvd_id,)).fetchone()
    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    
    if dvd is None:
        flash('DVDが見つかりません。', 'error')
        return redirect(url_for('dvds'))
        
    return render_template('edit_dvd.html', dvd=dvd, genres=genres)

@app.route('/delete_dvd/<int:dvd_id>', methods=['POST'])
def delete_dvd(dvd_id):
    """
    DVDを削除します。ただし、一度でもレンタルされた履歴がある場合は削除不可。
    """
    conn = get_db_connection()
    try:
        # レンタル履歴が存在するかチェック
        rental_count = conn.execute('SELECT COUNT(*) FROM rentals WHERE dvd_id = ?', (dvd_id,)).fetchone()[0]
        if rental_count > 0:
             flash('レンタル履歴があるDVDは削除できません。', 'error')
        else:
            conn.execute('DELETE FROM dvds WHERE dvd_id = ?', (dvd_id,))
            conn.commit()
            flash('DVDを削除しました。', 'success')
    except Exception as e:
        flash(f'削除エラー: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('dvds'))

@app.route('/users', methods=['GET', 'POST'])
def users():
    """
    ユーザー一覧表示と新規登録。
    """
    conn = get_db_connection()
    if request.method == 'POST':
        # フォーム入力を取得
        member_code = request.form['member_code']
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        birth_date = request.form['birth_date']
        try:
            # データベースへ挿入
            conn.execute('INSERT INTO users (name, address, phone, birth_date, member_code) VALUES (?, ?, ?, ?, ?)',
                         (name, address, phone, birth_date, member_code))
            conn.commit()
            flash('ユーザーを登録しました。', 'success')
        except Exception as e:
            flash(f'登録エラー: {str(e)}', 'error')
        return redirect(url_for('users'))

    # 最新順にユーザーを表示
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    """
    ユーザー情報の編集。
    """
    conn = get_db_connection()
    if request.method == 'POST':
        member_code = request.form['member_code']
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        birth_date = request.form['birth_date']
        
        try:
            conn.execute('''
                UPDATE users 
                SET member_code = ?, name = ?, address = ?, phone = ?, birth_date = ?
                WHERE user_id = ?
            ''', (member_code, name, address, phone, birth_date, user_id))
            conn.commit()
            flash('ユーザー情報を更新しました。', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            flash(f'更新エラー: {str(e)}', 'error')
            
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user is None:
        flash('ユーザーが見つかりません。', 'error')
        return redirect(url_for('users'))
        
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """
    ユーザーを削除します。ただし、レンタル中や過去の履歴がある場合は削除不可。
    """
    conn = get_db_connection()
    try:
        # 履歴チェック
        rental_count = conn.execute('SELECT COUNT(*) FROM rentals WHERE user_id = ?', (user_id,)).fetchone()[0]
        if rental_count > 0:
             flash('レンタル履歴があるユーザーは削除できません。', 'error')
        else:
            conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            flash('ユーザーを削除しました。', 'success')
    except Exception as e:
        flash(f'削除エラー: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('users'))

@app.route('/rental')
def rental_page():
    """
    貸出処理と貸出状況の確認ページ。
    """
    conn = get_db_connection()
    # プルダウン選択用のデータを取得
    users = conn.execute('SELECT user_id, name, member_code FROM users').fetchall()
    # 在庫があるDVDのみを表示対象とする
    dvds = conn.execute('SELECT dvd_id, title FROM dvds WHERE stock_count > 0').fetchall()
    
    # 現在貸出中（未返却）のレコードを最新順に取得
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

@app.route('/genres', methods=['GET', 'POST'])
def genres():
    """
    ジャンルの管理（追加と一覧）。
    """
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        try:
            conn.execute('INSERT INTO genres (name) VALUES (?)', (name,))
            conn.commit()
            flash('ジャンルを追加しました。', 'success')
        except Exception as e:
            flash(f'追加エラー: {str(e)}', 'error')
        return redirect(url_for('genres'))

    genres = conn.execute('SELECT * FROM genres').fetchall()
    conn.close()
    return render_template('genres.html', genres=genres)

@app.route('/delete_genre/<int:genre_id>', methods=['POST'])
def delete_genre(genre_id):
    """
    ジャンルを削除。ただし、そのジャンルに属するDVDがある場合は削除不可。
    """
    conn = get_db_connection()
    try:
        # 使用状況チェック
        dvd_count = conn.execute('SELECT COUNT(*) FROM dvds WHERE genre_id = ?', (genre_id,)).fetchone()[0]
        if dvd_count > 0:
            flash('このジャンルを使用しているDVDがあるため削除できません。', 'error')
        else:
            conn.execute('DELETE FROM genres WHERE genre_id = ?', (genre_id,))
            conn.commit()
            flash('ジャンルを削除しました。', 'success')
    except Exception as e:
        flash(f'削除エラー: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('genres'))

@app.route('/rent', methods=['POST'])
def rent_dvd():
    """
    DVDの貸出処理を実行します。
    #4 Transaction: 複数のDB更新を一つの単位として実行し、整合性を保ます。
    """
    user_id = request.form['user_id']
    dvd_id = request.form['dvd_id']
    
    conn = get_db_connection()
    try:
        # トランザクション開始 (#4 Transaction)
        conn.execute('BEGIN TRANSACTION')
        
        # 在庫チェック（同時に他者が借りて在庫切れになるのを防ぐため、処理内でも確認）
        dvd = conn.execute('SELECT stock_count FROM dvds WHERE dvd_id = ?', (dvd_id,)).fetchone()
        if not dvd or dvd['stock_count'] <= 0:
            flash('在庫がありません。', 'error')
            conn.rollback()
            return redirect(url_for('index'))

        # 重複貸出チェック（同じ人が同じものを現在借りていないか）
        existing_rental = conn.execute('''
            SELECT * FROM rentals 
            WHERE user_id = ? AND dvd_id = ? AND return_date IS NULL
        ''', (user_id, dvd_id)).fetchone()
        
        if existing_rental:
            flash('このユーザーは既にこのDVDをレンタル中です。', 'error')
            conn.rollback()
            return redirect(url_for('index'))
        
        # rentalsテーブルに履歴を挿入
        conn.execute('INSERT INTO rentals (user_id, dvd_id) VALUES (?, ?)', (user_id, dvd_id))
        
        # dvdsテーブルの在庫数を1つ減らす
        conn.execute('UPDATE dvds SET stock_count = stock_count - 1 WHERE dvd_id = ?', (dvd_id,))
        
        # すべて成功したらコミット（確定）
        conn.commit()
        flash('レンタル処理が完了しました。', 'success')
    except Exception as e:
        # 途中で失敗した場合はロールバック（最初からなかったことにする）
        conn.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/return/<int:rental_id>')
def return_dvd(rental_id):
    """
    DVDの返却処理を実行します。
    """
    conn = get_db_connection()
    try:
        conn.execute('BEGIN TRANSACTION')
        
        # 対象のレンタル情報を特定
        rental = conn.execute('SELECT dvd_id FROM rentals WHERE rental_id = ?', (rental_id,)).fetchone()
        if rental:
            dvd_id = rental['dvd_id']
            # 返却日を現在時刻に更新し、ステータスを変更
            conn.execute('UPDATE rentals SET return_date = CURRENT_TIMESTAMP, status = "returned" WHERE rental_id = ?', (rental_id,))
            # DVDの在庫数を1つ戻す
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
    # Flaskアプリの起動
    # host='0.0.0.0' にすることで、同じWi-Fi内のスマホなどからもアクセス可能になります
    app.run(debug=True, host='0.0.0.0', port=5000)
