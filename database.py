import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('voters.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY,
            pdf_name TEXT,
            serial INTEGER,
            name TEXT,
            voter_no TEXT,
            father TEXT,
            mother TEXT,
            occupation TEXT,
            dob TEXT,
            address TEXT,
            upload_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(df, pdf_name):
    init_db()
    conn = sqlite3.connect('voters.db')
    df['pdf_name'] = pdf_name
    df['upload_date'] = pd.Timestamp.now()
    df.to_sql('voters', conn, if_exists='append', index=False)
    conn.close()
    print(f"✅ {len(df)} জন ডাটাবেসে সেভ হয়েছে")

def search_voters(query):
    conn = sqlite3.connect('voters.db')
    df = pd.read_sql_query(f"""
        SELECT * FROM voters 
        WHERE name LIKE '%{query}%' 
           OR voter_no LIKE '%{query}%' 
           OR father LIKE '%{query}%'
        ORDER BY serial
    """, conn)
    conn.close()
    return df
