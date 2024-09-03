# In a new file called budget_models.py

from database import get_db_connection
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class BudgetModel:
    def __init__(self):
        self.init_table()

    def init_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_budgets (
                id INTEGER PRIMARY KEY,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                item_type TEXT DEFAULT 'Mandatory',
                total_income REAL DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def get_available_months(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT month FROM monthly_budgets ORDER BY month")
        months = [datetime.strptime(row[0], '%Y-%m') for row in cursor.fetchall()]
        conn.close()
        return months

    def get_budget(self, month):
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, check if item_type column exists
        cursor.execute("PRAGMA table_info(monthly_budgets)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'item_type' in columns:
            cursor.execute(
                "SELECT category, amount, item_type FROM monthly_budgets WHERE month = ?",
                (month.strftime('%Y-%m'),)
            )
            budget = {row[0]: {'amount': row[1], 'type': row[2]} for row in cursor.fetchall()}
        else:
            cursor.execute(
                "SELECT category, amount FROM monthly_budgets WHERE month = ?",
                (month.strftime('%Y-%m'),)
            )
            budget = {row[0]: {'amount': row[1], 'type': 'Mandatory'} for row in cursor.fetchall()}

        conn.close()
        return budget

    def create_budget(self, month, base_budget=None):
        conn = get_db_connection()
        cursor = conn.cursor()

        if base_budget is None:
            base_budget = self.get_budget(month - relativedelta(months=1))

        for category, amount in base_budget.items():
            cursor.execute(
                "INSERT INTO monthly_budgets (month, category, amount) VALUES (?, ?, ?)",
                (month.strftime('%Y-%m'), category, amount)
            )

        conn.commit()
        conn.close()

    def update_budget(self, month, new_budget):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if item_type column exists
        cursor.execute("PRAGMA table_info(monthly_budgets)")
        columns = [column[1] for column in cursor.fetchall()]

        for category, item in new_budget.items():
            if isinstance(item, dict):
                amount = item['amount']
                item_type = item.get('type', 'Mandatory')
            else:
                amount = item
                item_type = 'Mandatory'

            if 'item_type' in columns:
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_budgets (month, category, amount, item_type)
                    VALUES (?, ?, ?, ?)
                ''', (month.strftime('%Y-%m'), category, amount, item_type))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_budgets (month, category, amount)
                    VALUES (?, ?, ?)
                ''', (month.strftime('%Y-%m'), category, amount))

        conn.commit()
        conn.close()

    def delete_budget_item(self, month, category):
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                 DELETE FROM monthly_budgets
                 WHERE month = ? AND category = ?
             ''', (month.strftime('%Y-%m'), category))

            conn.commit()
            logger.info(f"Deleted budget item: {category} for {month.strftime('%Y-%m')}")
            return True
        except Exception as e:
            conn.rollback()
            logger.exception(f"Error deleting budget item {category}: {str(e)}")
            return False
        finally:
            conn.close()

    def update_total_income(self, month, total_income):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO monthly_budgets (month, category, amount, total_income)
                VALUES (?, 'TotalIncome', 0, ?)
            ''', (month.strftime('%Y-%m'), total_income))
            conn.commit()
            logger.info(f"Updated total income for {month.strftime('%Y-%m')}: {total_income}")
        except Exception as e:
            logger.exception(f"Error updating total income: {str(e)}")
        finally:
            conn.close()

    def get_total_income(self, month):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT total_income FROM monthly_budgets
                WHERE month = ? AND category = 'TotalIncome'
            ''', (month.strftime('%Y-%m'),))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.exception(f"Error retrieving total income: {str(e)}")
            return 0
        finally:
            conn.close()