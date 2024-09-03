import sqlite3

DATABASE_NAME = 'expenses.db'


def get_db_connection():
    return sqlite3.connect(DATABASE_NAME)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create transactions table with goal_id column
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                date TEXT,
                category TEXT,
                amount REAL,
                type TEXT,
                comment TEXT,
                currency TEXT,
                goal_id INTEGER
            )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            balance REAL,
            apr REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    # Check if goal_id column exists in transactions table
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'goal_id' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN goal_id INTEGER")

    conn.commit()
    conn.close()