from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QRegularExpressionValidator, QColor
from PyQt6.QtCore import QRegularExpression
from datetime import datetime
from models.consolidated_investment_savings_model import UnifiedInvestmentSavingsModel, GoalType, GoalCategory, \
    RiskLevel


class InvestmentSavingsUI(QWidget):
    def __init__(self, investment_savings_model, currency_manager):
        super().__init__()
        self.model = investment_savings_model
        self.currency_manager = currency_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form for adding new goals
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Goal Name")
        self.target_amount_input = QLineEdit()
        self.target_amount_input.setPlaceholderText(f"Target Amount ({self.currency_manager.get_default_currency().symbol})")

        # Date input field with format validation
        self.target_date_input = QLineEdit()
        self.target_date_input.setPlaceholderText("YYYY-MM-DD")
        date_regex = QRegularExpression("^\\d{4}-\\d{2}-\\d{2}$")
        date_validator = QRegularExpressionValidator(date_regex, self.target_date_input)
        self.target_date_input.setValidator(date_validator)

        self.goal_type_input = QComboBox()
        self.goal_type_input.addItems([gt.value for gt in GoalType])
        self.category_input = QComboBox()
        self.category_input.addItems([gc.value for gc in GoalCategory])
        self.risk_level_input = QComboBox()
        self.risk_level_input.addItems([rl.value for rl in RiskLevel])
        add_button = QPushButton("Add Goal")
        add_button.clicked.connect(self.add_goal)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.target_amount_input)
        form_layout.addWidget(self.target_date_input)
        form_layout.addWidget(self.goal_type_input)
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(self.risk_level_input)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)

        # Table to display goals
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(9)
        self.goals_table.setHorizontalHeaderLabels(
            ["Name", "Target", "Current", "Progress", "Date", "Type", "Category", "Risk", "Action"])
        layout.addWidget(self.goals_table)

        # Summary labels
        self.total_savings_label = QLabel(f"Total Savings: {self.currency_manager.get_default_currency().symbol}0")
        self.total_investments_label = QLabel(
            f"Total Investments: {self.currency_manager.get_default_currency().symbol}0")
        layout.addWidget(self.total_savings_label)
        layout.addWidget(self.total_investments_label)

        self.update_goals_display()

    def add_goal(self):
        name = self.name_input.text()
        try:
            target_amount = float(self.target_amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid target amount.")
            return

        date_str = self.target_date_input.text()
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Please enter a valid date in the format YYYY-MM-DD.")
            return

        goal_type = GoalType(self.goal_type_input.currentText())
        category = GoalCategory(self.category_input.currentText())
        risk_level = RiskLevel(self.risk_level_input.currentText())

        try:
            self.model.add_goal(
                name=name,
                target_amount=target_amount,
                target_date=target_date,
                goal_type=goal_type,
                category=category,
                risk_level=risk_level
            )
            self.update_goals_display()
            self.clear_inputs()
            QMessageBox.information(self, "Success", "Goal added successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding the goal: {str(e)}")

    def update_goals_display(self):
        goals = self.model.get_all_goals()
        self.goals_table.setRowCount(len(goals))
        currency_symbol = self.currency_manager.get_default_currency().symbol
        for row, goal in enumerate(goals):
            self.goals_table.setItem(row, 0, QTableWidgetItem(goal['name']))
            self.goals_table.setItem(row, 1, QTableWidgetItem(f"{currency_symbol}{goal['target_amount']:,.2f}"))
            self.goals_table.setItem(row, 2, QTableWidgetItem(f"{currency_symbol}{goal['current_amount']:,.2f}"))

            progress = self.model.calculate_progress(goal['id'])
            progress_bar = QProgressBar()
            progress_bar.setValue(int(progress))
            self.goals_table.setCellWidget(row, 3, progress_bar)

            self.goals_table.setItem(row, 4, QTableWidgetItem(goal['target_date'].strftime("%Y-%m-%d")))
            self.goals_table.setItem(row, 5, QTableWidgetItem(goal['goal_type'].value))
            self.goals_table.setItem(row, 6, QTableWidgetItem(goal['category'].value))
            self.goals_table.setItem(row, 7, QTableWidgetItem(goal['risk_level'].value))

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, g=goal: self.delete_goal(g))
            self.goals_table.setCellWidget(row, 8, delete_button)

            # Apply color to the row based on progress
            self.apply_row_color(row, progress)

        total_savings = self.model.calculate_total_savings()
        total_investments = self.model.calculate_total_investments()
        self.total_savings_label.setText(f"Total Savings: {currency_symbol}{total_savings:,.2f}")
        self.total_investments_label.setText(f"Total Investments: {currency_symbol}{total_investments:,.2f}")


    def apply_row_color(self, row, progress):
        if progress >= 100:
            color = QColor(144, 238, 144)  # Light Green
        elif progress >= 75:
            color = QColor(173, 255, 47)  # Green Yellow
        elif progress >= 50:
            color = QColor(255, 255, 0)  # Yellow
        elif progress >= 25:
            color = QColor(255, 165, 0)  # Orange
        else:
            color = QColor(255, 99, 71)  # Tomato (reddish)

        for col in range(self.goals_table.columnCount()):
            item = self.goals_table.item(row, col)
            if item:
                item.setBackground(color)

    def delete_goal(self, goal):
        reply = QMessageBox.question(self, "Delete Goal",
                                     f"Are you sure you want to delete the goal '{goal['name']}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.model.delete_goal(goal['id'])
            self.update_goals_display()

    def clear_inputs(self):
        self.name_input.clear()
        self.target_amount_input.clear()
        self.target_date_input.clear()
        self.goal_type_input.setCurrentIndex(0)
        self.category_input.setCurrentIndex(0)
        self.risk_level_input.setCurrentIndex(0)

    def update_currency(self):
        currency_symbol = self.currency_manager.get_default_currency().symbol
        self.target_amount_input.setPlaceholderText(f"Target Amount ({currency_symbol})")
        self.update_goals_display()