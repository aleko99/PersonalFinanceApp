import logging

from dateutil.relativedelta import relativedelta

from database import get_db_connection

logging.basicConfig(level=logging.DEBUG, filename='transaction.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TransactionModel:
    def add_transaction(self, date, category, amount, transaction_type, comment, currency_code, goal_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (date, category, amount, type, comment, currency, goal_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, category, amount, transaction_type, comment, currency_code, goal_id))
            conn.commit()

            if goal_id and transaction_type in ['Savings', 'Investment']:
                self.update_goal_progress(goal_id, amount)

            logger.info("Transaction added successfully")
        except Exception as e:
            logger.exception("Error adding transaction")
            raise
        finally:
            conn.close()

    def update_goal_progress(self, goal_id, amount):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE investment_savings_goals
                SET current_amount = current_amount + ?
                WHERE id = ?
            """, (amount, goal_id))
            conn.commit()
            logger.info(f"Updated progress for goal {goal_id}")
        except Exception as e:
            logger.exception(f"Error updating progress for goal {goal_id}")
            raise
        finally:
            conn.close()

    def get_all_transactions(self):
        logger.info("Fetching all transactions")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
            transactions = cursor.fetchall()
            logger.info(f"Fetched {len(transactions)} transactions")
            return transactions
        except Exception as e:
            logger.exception("Error fetching transactions")
            raise
        finally:
            conn.close()

    def get_category_spending(self, month, category):
        conn = get_db_connection()
        cursor = conn.cursor()
        start_date = month.strftime('%Y-%m-01')
        end_date = (month + relativedelta(months=1)).strftime('%Y-%m-01')

        cursor.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE date >= ? AND date < ? AND category = ? AND type = 'Expense'
        """, (start_date, end_date, category))

        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0.0

    def delete_transaction(self, transaction_id):
        logger.info(f"Attempting to delete transaction with id: {transaction_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            logger.info("Transaction deleted successfully")
        except Exception as e:
            logger.exception("Error deleting transaction")
            raise
        finally:
            conn.close()

    def get_transactions_in_range(self, start_date, end_date):
        logger.info(f"Fetching transactions between {start_date} and {end_date}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date DESC
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            transactions = cursor.fetchall()
            logger.info(f"Fetched {len(transactions)} transactions in the date range")
            return transactions
        except Exception as e:
            logger.exception("Error fetching transactions in range")
            raise
        finally:
            conn.close()

    def get_spending_by_category(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE type = 'Expense' 
            GROUP BY category
        """)
        results = cursor.fetchall()
        conn.close()
        return {category: amount for category, amount in results}

    def get_income_vs_expenses(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m', date) as month,
                   SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expenses
            FROM transactions
            GROUP BY month
            ORDER BY month
            LIMIT 12
        """)
        results = cursor.fetchall()
        conn.close()
        return {month: {'income': income, 'expenses': expenses} for month, income, expenses in results}