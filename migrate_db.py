import sqlite3
from database import DATABASE_NAME, get_db_connection


def migrate_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if goal_id column exists in transactions table
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'goal_id' not in columns:
        print("Adding goal_id column to transactions table...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN goal_id INTEGER")
        print("Column added successfully.")
    else:
        print("goal_id column already exists in transactions table.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate_database()