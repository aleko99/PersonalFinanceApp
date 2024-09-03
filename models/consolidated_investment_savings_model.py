from database import get_db_connection
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class GoalType(Enum):
    INVESTMENT = "Investment"
    SAVINGS = "Savings"


class GoalCategory(Enum):
    SHORT_TERM = "Short Term"
    MEDIUM_TERM = "Medium Term"
    LONG_TERM = "Long Term"
    RETIREMENT = "Retirement"


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class UnifiedInvestmentSavingsModel:
    def __init__(self):
        self.init_tables()

    def init_tables(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create investment_savings_goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investment_savings_goals (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL,
                target_date TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                category TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                creation_date TEXT NOT NULL,
                annual_return REAL
            )
        ''')

        # Create investments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                date TEXT NOT NULL,
                annual_return REAL,
                risk_level TEXT
            )
        ''')

        conn.commit()
        conn.close()

    # Methods for goals (former ConsolidatedInvestmentSavingsModel methods)
    def add_goal(self, name, target_amount, target_date, goal_type, category, risk_level, current_amount=0,
                 annual_return=None):
        logger.info(f"Adding goal: {name}, {target_amount}, {goal_type}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investment_savings_goals 
                (name, target_amount, current_amount, target_date, goal_type, category, risk_level, creation_date, annual_return)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, target_amount, current_amount, target_date.strftime('%Y-%m-%d'),
                  goal_type.value, category.value, risk_level.value, datetime.now().strftime('%Y-%m-%d'),
                  annual_return))
            conn.commit()
            logger.info("Goal added successfully")
        except Exception as e:
            logger.exception("Error adding goal")
            raise
        finally:
            conn.close()

    def get_all_goals(self):
        logger.info("Fetching all goals")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investment_savings_goals")
            goals = cursor.fetchall()
            logger.info(f"Fetched {len(goals)} goals")
            return [self._convert_to_goal_object(goal) for goal in goals]
        except Exception as e:
            logger.exception("Error fetching goals")
            raise
        finally:
            conn.close()

    def update_goal(self, goal_id, name, target_amount, current_amount, target_date, goal_type, category, risk_level,
                    annual_return=None):
        logger.info(f"Updating goal with id: {goal_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE investment_savings_goals
                SET name = ?, target_amount = ?, current_amount = ?, target_date = ?, 
                    goal_type = ?, category = ?, risk_level = ?, annual_return = ?
                WHERE id = ?
            ''', (name, target_amount, current_amount, target_date.strftime('%Y-%m-%d'),
                  goal_type.value, category.value, risk_level.value, annual_return, goal_id))
            conn.commit()
            logger.info("Goal updated successfully")
        except Exception as e:
            logger.exception(f"Error updating goal with id {goal_id}")
            raise
        finally:
            conn.close()

    def delete_goal(self, goal_id):
        logger.info(f"Deleting goal with id: {goal_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM investment_savings_goals WHERE id = ?", (goal_id,))
            conn.commit()
            logger.info("Goal deleted successfully")
        except Exception as e:
            logger.exception(f"Error deleting goal with id {goal_id}")
            raise
        finally:
            conn.close()

    def calculate_progress(self, goal_id):
        logger.info(f"Calculating progress for goal with id: {goal_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT current_amount, target_amount FROM investment_savings_goals WHERE id = ?",
                           (goal_id,))
            result = cursor.fetchone()
            if result:
                current_amount, target_amount = result
                progress = (current_amount / target_amount) * 100
                logger.info(f"Progress calculated: {progress:.2f}%")
                return progress
            else:
                logger.warning(f"No goal found with id {goal_id}")
                return 0
        except Exception as e:
            logger.exception(f"Error calculating progress for goal with id {goal_id}")
            raise
        finally:
            conn.close()

    def calculate_total_savings(self):
        return self._calculate_total_by_type(GoalType.SAVINGS)

    def calculate_total_investments(self):
        return self._calculate_total_by_type(GoalType.INVESTMENT)

    def _calculate_total_by_type(self, goal_type):
        logger.info(f"Calculating total for {goal_type.value}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(current_amount) FROM investment_savings_goals WHERE goal_type = ?',
                           (goal_type.value,))
            total = cursor.fetchone()[0]
            return total if total is not None else 0
        except Exception as e:
            logger.exception(f"Error calculating total for {goal_type.value}")
            raise
        finally:
            conn.close()

    # Methods for investments (former InvestmentModel methods)
    def add_investment(self, name, amount, investment_type, date, annual_return=None, risk_level=None):
        logger.info(f"Adding investment: {name}, {amount}, {investment_type}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investments (name, amount, type, date, annual_return, risk_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, amount, investment_type, date, annual_return, risk_level))
            conn.commit()
            logger.info("Investment added successfully")
        except Exception as e:
            logger.exception("Error adding investment")
            raise
        finally:
            conn.close()

    def get_all_investments(self):
        logger.info("Fetching all investments")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investments")
            investments = cursor.fetchall()
            logger.info(f"Fetched {len(investments)} investments")
            return investments
        except Exception as e:
            logger.exception("Error fetching investments")
            raise
        finally:
            conn.close()

    def update_investment(self, investment_id, name, amount, investment_type, date, annual_return=None,
                          risk_level=None):
        logger.info(f"Updating investment with id: {investment_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE investments
                SET name = ?, amount = ?, type = ?, date = ?, annual_return = ?, risk_level = ?
                WHERE id = ?
            ''', (name, amount, investment_type, date, annual_return, risk_level, investment_id))
            conn.commit()
            logger.info("Investment updated successfully")
        except Exception as e:
            logger.exception(f"Error updating investment with id {investment_id}")
            raise
        finally:
            conn.close()

    def delete_investment(self, investment_id):
        logger.info(f"Deleting investment with id: {investment_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM investments WHERE id = ?", (investment_id,))
            conn.commit()
            logger.info("Investment deleted successfully")
        except Exception as e:
            logger.exception(f"Error deleting investment with id {investment_id}")
            raise
        finally:
            conn.close()

    def get_investments_by_type(self, investment_type):
        logger.info(f"Fetching investments of type: {investment_type}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investments WHERE type = ?", (investment_type,))
            investments = cursor.fetchall()
            logger.info(f"Fetched {len(investments)} investments of type {investment_type}")
            return investments
        except Exception as e:
            logger.exception(f"Error fetching investments of type {investment_type}")
            raise
        finally:
            conn.close()

    # Combined methods
    def calculate_portfolio_return(self):
        logger.info("Calculating portfolio return")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get returns from goals
            cursor.execute(
                "SELECT current_amount, annual_return FROM investment_savings_goals WHERE goal_type = ? AND annual_return IS NOT NULL",
                (GoalType.INVESTMENT.value,))
            goal_investments = cursor.fetchall()

            # Get returns from investments
            cursor.execute("SELECT amount, annual_return FROM investments WHERE annual_return IS NOT NULL")
            individual_investments = cursor.fetchall()

            all_investments = goal_investments + individual_investments

            total_value = sum(inv[0] for inv in all_investments)
            weighted_return = sum(inv[0] * inv[1] for inv in all_investments)

            if total_value > 0:
                portfolio_return = weighted_return / total_value
            else:
                portfolio_return = 0

            logger.info(f"Calculated portfolio return: {portfolio_return:.2f}%")
            return portfolio_return
        except Exception as e:
            logger.exception("Error calculating portfolio return")
            raise
        finally:
            conn.close()

    def get_net_worth_trend(self):
        logger.info("Calculating net worth trend")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get investment and savings goal values
            cursor.execute("""
                SELECT strftime('%Y-%m', target_date) as month, SUM(current_amount) as amount
                FROM investment_savings_goals
                GROUP BY month
                ORDER BY month
                LIMIT 12
            """)
            goal_values = dict(cursor.fetchall())

            # Get individual investment values
            cursor.execute("""
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as amount
                FROM investments
                GROUP BY month
                ORDER BY month
                LIMIT 12
            """)
            investment_values = dict(cursor.fetchall())

            # Combine and calculate net worth
            all_months = sorted(set(goal_values.keys()) | set(investment_values.keys()))
            net_worth_trend = {}
            for month in all_months:
                net_worth_trend[month] = goal_values.get(month, 0) + investment_values.get(month, 0)

            logger.info(f"Calculated net worth trend for {len(net_worth_trend)} months")
            return net_worth_trend
        except Exception as e:
            logger.exception("Error calculating net worth trend")
            raise
        finally:
            conn.close()

    def _convert_to_goal_object(self, goal_tuple):
        goal_dict = {
            'id': goal_tuple[0],
            'name': goal_tuple[1],
            'target_amount': goal_tuple[2],
            'current_amount': goal_tuple[3],
            'target_date': datetime.strptime(goal_tuple[4], '%Y-%m-%d').date(),
            'goal_type': GoalType(goal_tuple[5]),
            'category': GoalCategory(goal_tuple[6]),
            'risk_level': RiskLevel(goal_tuple[7]),
            'creation_date': datetime.strptime(goal_tuple[8], '%Y-%m-%d'),
        }
        if len(goal_tuple) > 9:
            goal_dict['annual_return'] = goal_tuple[9]
        else:
            goal_dict['annual_return'] = None
        return goal_dict

    def get_goals_by_type(self, goal_type):
        logger.info(f"Fetching goals of type: {goal_type}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investment_savings_goals WHERE goal_type = ?", (goal_type.value,))
            goals = cursor.fetchall()
            logger.info(f"Fetched {len(goals)} goals of type {goal_type}")
            return [self._convert_to_goal_object(goal) for goal in goals]
        except Exception as e:
            logger.exception(f"Error fetching goals of type {goal_type}")
            raise
        finally:
            conn.close()