import sqlite3

def init_local_db():
    # This creates 'jobs.db' in your folder if it doesn't exist
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    
    # Create the table (matches your Supabase schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_url TEXT UNIQUE,
            match_score INTEGER,
            status TEXT DEFAULT 'Found'
        )
    ''')
    conn.commit()
    conn.close()
    print("Local SQLite database initialized.")

if __name__ == "__main__":
    init_local_db()