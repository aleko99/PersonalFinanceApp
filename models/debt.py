from database import get_db_connection
import logging

logger = logging.getLogger(__name__)


class DebtModel:
    def __init__(self):
        self.init_table()

    def init_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create the table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                balance REAL,
                apr REAL
            )
        ''')

        # Check if original_balance column exists, if not, add it
        cursor.execute("PRAGMA table_info(debts)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'original_balance' not in columns:
            cursor.execute("ALTER TABLE debts ADD COLUMN original_balance REAL")

        # Check if current_balance column exists, if not, add it
        if 'current_balance' not in columns:
            cursor.execute("ALTER TABLE debts ADD COLUMN current_balance REAL")

        # If original_balance is NULL, set it to balance
        cursor.execute("UPDATE debts SET original_balance = balance WHERE original_balance IS NULL")

        # If current_balance is NULL, set it to balance
        cursor.execute("UPDATE debts SET current_balance = balance WHERE current_balance IS NULL")

        conn.commit()
        conn.close()

    def add_debt(self, name, balance, apr):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO debts (name, balance, original_balance, current_balance, apr) VALUES (?, ?, ?, ?, ?)",
            (name, balance, balance, balance, apr))
        conn.commit()
        conn.close()

    def get_all_debts(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, original_balance, current_balance, apr FROM debts")
        debts = cursor.fetchall()
        conn.close()
        return debts

    def delete_debt(self, debt_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
        conn.commit()
        conn.close()

    def update_debt_balance(self, debt_id, amount_paid):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE debts SET current_balance = current_balance - ? WHERE id = ?", (amount_paid, debt_id))
        conn.commit()
        conn.close()

    def calculate_repayment_progress(self, debt_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT original_balance, current_balance FROM debts WHERE id = ?", (debt_id,))
        debt = cursor.fetchone()
        conn.close()
        if debt:
            original_balance, current_balance = debt
            if original_balance is not None and original_balance > 0:
                return ((original_balance - current_balance) / original_balance) * 100
        return 0

    # In DebtModel
    def get_debt_repayment_progress(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, 
                   (original_balance - current_balance) / original_balance * 100 as progress
            FROM debts
        """)
        results = cursor.fetchall()
        conn.close()
        return {name: progress for name, progress in results}