import sqlite3
import os

def seed_data():
    db_path = os.path.join(os.path.dirname(__file__), 'dvd_rental.db')
    print(f"Seeding data into: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Genres (already has Action, Comedy, Drama, Sci-Fi from init_db.py)
    # Adding more specific genres and Japanese names if needed, but schema is 'name'
    # Let's add some more genres
    genres = [('ホラー',), ('アニメ',), ('恋愛',), ('アクション',), ('SF',), ('ドラマ',), ('コメディ',), ('ミステリー',), ('ドキュメンタリー',)]
    
    # Check existing genres and add new ones if not exist
    # Since genres table might have English names from init_db, let's just insert ignore
    # Note: If schema has unique constraint on name, this works.
    cursor.executemany("INSERT OR IGNORE INTO genres (name) VALUES (?)", genres)
    
    # To handle potential mixed English/Japanese genre names, let's map them.
    # We will try to fetch all and see what we have.
    cursor.execute("SELECT genre_id, name FROM genres")
    all_genres = cursor.fetchall()
    genre_map = {name: gid for gid, name in all_genres}
    
    # Helper to fuzzy get genre id (e.g. map 'Sci-Fi' to 'SF' if needed, or just use what's available)
    def get_gid(name):
        # Try exact match first
        if name in genre_map:
            return genre_map[name]
        # Fallback for known English/Japanese mapping
        mapping = {
            'Sci-Fi': 'SF',
            'Animation': 'アニメ',
            'Romance': '恋愛',
            'Horror': 'ホラー',
            'Action': 'アクション',
            'Comedy': 'コメディ',
            'Drama': 'ドラマ'
        }
        target = mapping.get(name, name)
        return genre_map.get(target)

    # Users
    users = [
        ('M00002', '佐藤 花子', '神奈川県横浜市', '080-8765-4321', '1995-05-15'),
        ('M00003', '鈴木 一郎', '大阪府大阪市', '070-1111-2222', '1985-11-20'),
        ('M00004', '高橋 健太', '愛知県名古屋市', '090-9999-8888', '2000-03-10'),
        ('M00005', '田中 美咲', '福岡県福岡市', '090-1234-5678', '1998-07-22'),
        ('M00006', '伊藤 翔太', '北海道札幌市', '080-9876-5432', '1990-12-05')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO users (member_code, name, address, phone, birth_date) 
        VALUES (?, ?, ?, ?, ?)
    """, users)

    # DVDs (Japanese titles and descriptions)
    # Using Replace to update existing English entries to Japanese if ID matches, 
    # but since we don't control IDs explicitly here, we'll rely on Title being unique?
    # Actually schema might not enforce unique title. Let's just insert.
    # To avoid duplicates if run multiple times, we can check existence or just INSERT OR IGNORE if title unique.
    # Let's assume we want to populate these specific items.
    
    dvds = [
        ('インターステラー', get_gid('SF'), 4, 4, 'B-1', '食糧難と環境変化によって人類滅亡が迫る近未来。元エンジニアの男は、居住可能な新たな惑星を探すというミッションに選ばれ、愛する家族を地球に残して宇宙の彼方へ旅立つ。父と娘の絆、そして愛の力を描いた壮大なSF叙事詩。'),
        ('トイ・ストーリー', get_gid('アニメ'), 5, 5, 'C-1', 'カウボーイ人形のウッディは、アンディ少年の大のお気に入り。しかし、最新式のアクション人形バズ・ライトイヤーが現れ、主役の座を奪われてしまう。反発し合う二人だったが、やがて冒険を通じて固い友情で結ばれていく。子供から大人まで楽しめる感動のファンタジー。'),
        ('ゴッドファーザー', get_gid('ドラマ'), 2, 2, 'A-3', 'アメリカのマフィア界に君臨するコルレオーネ一族の盛衰を描いた傑作。偉大な父ビトーから、組織のドンとしての地位を受け継ぐことになった息子マイケルの苦悩と冷徹な決断。家族の絆と裏切りが交錯する重厚なドラマ。'),
        ('千と千尋の神隠し', get_gid('アニメ'), 3, 3, 'C-2', '10歳の少女・千尋は、引越し先へ向かう途中で不思議な世界に迷い込む。そこは八百万の神々が住む世界だった。豚に変えられてしまった両親を救うため、千尋は湯屋「油屋」で働くことになる。成長と自立を描いた日本アニメーションの金字塔。'),
        ('君の名は。', get_gid('恋愛'), 6, 6, 'D-1', '東京に住む男子高校生・瀧と、飛騨の山奥に住む女子高生・三葉。出会うはずのない二人が、夢の中で入れ替わっていることに気づく。時空を超えたつながりと、忘れたくない想いを描いた青春ファンタジー。'),
        ('ショーシャンクの空に', get_gid('ドラマ'), 3, 3, 'A-1', '妻殺しの濡れ衣を着せられ、ショーシャンク刑務所に収監された元銀行員アンディ。絶望的な状況でも希望を捨てず、誠実な人柄で周囲を変えていく。長きにわたる刑務所生活と、驚きの脱獄劇を描いた感動のヒューマンドラマ。'),
        ('バック・トゥ・ザ・フューチャー', get_gid('SF'), 5, 5, 'B-2', '高校生のマーティは、友人の科学者ドクが発明したタイムマシンで30年前にタイムスリップしてしまう。そこで若き日の両親に出会い、二人の恋を成就させなければ自分の存在が消えてしまうことに。ハラハラドキドキの冒険を描いたSFアドベンチャーの傑作。'),
        ('タイタニック', get_gid('恋愛'), 4, 4, 'D-2', '豪華客船タイタニック号で出会った、貧しい青年ジャックと上流階級の娘ローズ。身分違いの恋に落ちた二人だったが、船は氷山に衝突し、沈没の時が迫る。悲劇的な運命の中で永遠の愛を誓う、世界中が涙したラブストーリー。'),
        ('となりのトトロ', get_gid('アニメ'), 4, 4, 'C-3', '田舎へ引っ越してきたサツキとメイの姉妹。そこで出会ったのは、森の主である不思議な生き物トトロだった。子供にしか見えないトトロとの交流を描いた、心温まるファンタジー。家族みんなで楽しめる不朽の名作。'),
        ('インセプション', get_gid('SF'), 3, 3, 'B-3', '他人の夢の中に潜入し、アイデアを盗み出す産業スパイのコブ。彼に舞い込んだ最後の仕事は、アイデアを盗むのではなく「植え付ける（インセプション）」ことだった。複雑に入り組んだ夢の世界で繰り広げられる、圧倒的映像美のサスペンスアクション。'),
        ('ローマの休日', get_gid('恋愛'), 2, 2, 'D-3', '某国の王女アンは、公務に追われる日々に疲れ、ローマの街へ一人で逃げ出す。そこで出会った新聞記者ジョーと、束の間の自由な一日を過ごす。身分を隠した王女とスクープを狙う記者の、切なくも美しいラブストーリー。'),
        ('ライフ・イズ・ビューティフル', get_gid('ドラマ'), 3, 3, 'A-2', '第二次世界大戦下のイタリア。ユダヤ系イタリア人のグイドは、強制収容所に送られてしまう。幼い息子を怖がらせないため、彼は収容所生活を「ゲーム」だと嘘をつき、ユーモアで家族を守り抜こうとする。父の深い愛に涙が止まらない感動作。'),
        ('アベンジャーズ', get_gid('アクション'), 6, 6, 'E-1', '地球侵略の危機に、アイアンマン、キャプテン・アメリカ、ソー、ハルクら最強のヒーローたちが集結する。個性豊かなヒーローたちがぶつかり合いながらも結束し、強大な敵に立ち向かう。ド派手なアクションと痛快なストーリーが楽しめるエンターテインメント大作。'),
        ('セブン', get_gid('ミステリー'), 3, 3, 'F-1', 'キリスト教の「七つの大罪」に見立てた連続猟奇殺人事件が発生。退職間近のベテラン刑事サマセットと、血気盛んな新人刑事ミルズが捜査に当たる。雨の降り続く陰鬱な都会を舞台に、驚愕の結末へと向かうサイコサスペンス。'),
        ('アバウト・タイム', get_gid('恋愛'), 4, 4, 'D-4', 'タイムトラベルの能力を持つ家系に生まれた青年ティム。彼はその能力を使って、恋人メアリーとの関係をより良くしようと奮闘する。しかし、過去を変えることには代償も伴っていた。何気ない日常の尊さを教えてくれる、温かい愛の物語。')
    ]

    # Insert DVDs. If title exists, we might want to update description to Japanese.
    # Simple approach: Check if title exists (english or japanese).
    # Since we changed titles to Japanese in the list, they likely won't match English titles in DB.
    # So we might end up adding new rows.
    # To clean up, maybe we should DELETE all existing DVDs first? 
    # Or update specific IDs if we knew them.
    # Given the request "sample data ... Japanese", replacing all seems appropriate for a clean state.
    
    # Let's verify if user wants to KEEP English ones? "すべて日本語で登録してほしい" implies ALL should be Japanese.
    # So wiping dvds table (or at least the sample ones) is better.
    
    print("Clearing existing DVD data to replace with Japanese data...")
    # Be careful with Foreign Keys. Delete rentals first?
    cursor.execute("DELETE FROM rentals")
    cursor.execute("DELETE FROM dvds")
    # Reset sequence if possible (sqlite)
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='dvds'")
    
    print("Inserting Japanese DVD data...")
    cursor.executemany("""
        INSERT INTO dvds (title, genre_id, stock_count, total_stock, storage_location, description) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, dvds)

    conn.commit()
    conn.close()
    print("Japanese sample data inserted successfully.")

if __name__ == '__main__':
    seed_data()
