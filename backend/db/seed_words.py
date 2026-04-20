from sqlalchemy import text

def seed_words(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO words (target, source, part_of_speech) VALUES
                ('안녕하세요', 'hello', 'greeting'),
                ('세계', 'world', 'noun'),
                ('감사합니다', 'thank you', 'greeting'),
                ('네', 'yes', 'adverb'),
                ('아니요', 'no', 'adverb'),
                ('물', 'water', 'noun'),
                ('밥', 'rice / meal', 'noun'),
                ('사람', 'person', 'noun'),
                ('좋다', 'good', 'adjective'),
                ('크다', 'big', 'adjective'),
                ('작다', 'small', 'adjective'),
                ('먹다', 'to eat', 'verb'),
                ('가다', 'to go', 'verb'),
                ('오다', 'to come', 'verb'),
                ('하다', 'to do', 'verb'),
                ('보다', 'to see', 'verb'),
                ('집', 'house', 'noun'),
                ('학교', 'school', 'noun'),
                ('오늘', 'today', 'noun'),
                ('내일', 'tomorrow', 'noun');
        """))