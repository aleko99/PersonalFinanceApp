from database import get_db_connection
from datetime import datetime

class SavingsGoalModel:
    def __init__(self):
        self.init_table()

    def init_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL,
                target_date TEXT NOT NULL,
                category TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add_goal(self, name, target_amount, current_amount, target_date, category):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO savings_goals (name, target_amount, current_amount, target_date, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, target_amount, current_amount, target_date.strftime('%Y-%m-%d'), category))
        conn.commit()
        conn.close()

    def get_all_goals(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM savings_goals')
        goals = cursor.fetchall()
        conn.close()
        return [self._convert_to_goal_object(goal) for goal in goals]

    def update_goal(self, goal_id, name, target_amount, current_amount, target_date, category):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE savings_goals
            SET name = ?, target_amount = ?, current_amount = ?, target_date = ?, category = ?
            WHERE id = ?
        ''', (name, target_amount, current_amount, target_date.strftime('%Y-%m-%d'), category, goal_id))
        conn.commit()
        conn.close()

    def delete_goal(self, goal_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM savings_goals WHERE id = ?', (goal_id,))
        conn.commit()
        conn.close()

    def _convert_to_goal_object(self, goal_tuple):
        return SavingsGoal(
            goal_id=goal_tuple[0],
            name=goal_tuple[1],
            target_amount=goal_tuple[2],
            current_amount=goal_tuple[3],
            target_date=datetime.strptime(goal_tuple[4], '%Y-%m-%d').date(),
            category=goal_tuple[5]
        )

    def calculate_total_savings(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(current_amount) FROM savings_goals')
        total = cursor.fetchone()[0]
        conn.close()
        return total if total is not None else 0

class SavingsGoal:
    def __init__(self, goal_id, name, target_amount, current_amount, target_date, category):
        self.id = goal_id
        self.name = name
        self.target_amount = target_amount
        self.current_amount = current_amount
        self.target_date = target_date
        self.category = category