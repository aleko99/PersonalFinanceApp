import logging

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QTableWidget, QTabWidget,
                             QInputDialog, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSlot
from datetime import datetime

from models.budget_models import BudgetModel
from ui.config_dialog import ConfigDialog
from models.transaction import TransactionModel
from models.debt import DebtModel
from models.category import CategoryModel
from ui.debt_management_ui import DebtManagementUI
from ui.debt_payoff_planner import DebtPayoffPlanner, DebtRepaymentUI
from ui import BudgetPlanner
from ui.financial_dashboard import FinancialDashboard
from ui.investment_savings_ui import InvestmentSavingsUI
from models.consolidated_investment_savings_model import UnifiedInvestmentSavingsModel
from ui.smart_savings_advisor_ui import SmartSavingsAdvisorUI
from models.savings_goal import SavingsGoalModel
#from models.investment_model_old import InvestmentModel

from currency import CurrencyManager



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense, Income, and Debt Tracker")
        self.setGeometry(100, 100, 1000, 700)
        self.transaction_model = TransactionModel()
        self.debt_model = DebtModel()
        self.category_model = CategoryModel()
        self.investment_savings_model = UnifiedInvestmentSavingsModel()
        self.savings_goal_model = SavingsGoalModel()
        self.currency_manager = CurrencyManager()
        self.budget_model = BudgetModel()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Transactions Tab
        transactions_tab = self.create_transactions_tab()
        self.tab_widget.addTab(transactions_tab, "Transactions")

        # Debt Management Tab
        self.debt_management_ui = DebtManagementUI(self.debt_model, self.currency_manager)
        self.tab_widget.addTab(self.debt_management_ui, "Debt Management")

        # Debt Payoff Planner Tab
        self.debt_planner = DebtPayoffPlanner(self.debt_model, self.currency_manager)
        self.tab_widget.addTab(self.debt_planner, "Debt Payoff Planner")

        # Budget Planning Tab
        self.budget_planner = BudgetPlanner(self.category_model, self.budget_model, self.transaction_model)
        self.tab_widget.addTab(self.budget_planner, "Budget Planner")

        # Investment & Savings Tab
        self.investment_savings_ui = InvestmentSavingsUI(self.investment_savings_model, self.currency_manager)
        self.tab_widget.addTab(self.investment_savings_ui, "Investments & Savings")

        # Smart Savings Advisor Tab
        self.smart_savings_advisor = SmartSavingsAdvisorUI(
            self.transaction_model,
            self.debt_model,
            self.savings_goal_model,
            self.investment_savings_model  # Pass the investment_model here
        )
        self.tab_widget.addTab(self.smart_savings_advisor, "Smart Savings Advisor")

        # Financial Dashboard Tab
        self.financial_dashboard = FinancialDashboard(
            self.transaction_model,
            self.debt_model,
            self.investment_savings_model
        )
        self.tab_widget.addTab(self.financial_dashboard, "Financial Dashboard")


        # Configuration Button
        config_button = QPushButton("Configuration")
        config_button.clicked.connect(self.open_config_dialog)
        main_layout.addWidget(config_button)

        self.load_categories()
        self.load_transactions()


    def create_transactions_tab(self):
        transactions_tab = QWidget()
        transactions_layout = QVBoxLayout(transactions_tab)

        # Add Transaction
        add_transaction_layout = QHBoxLayout()
        self.date_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.category_input = QComboBox()
        self.amount_input = QLineEdit()
        self.transaction_type_input = QComboBox()
        self.transaction_type_input.addItems(["Expense", "Income"])
        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Enter comment (optional)")
        self.comment_input.setMaximumHeight(50)  # Limit the height of the comment box
        add_button = QPushButton("Add Transaction")
        add_button.clicked.connect(self.add_transaction)

        # Add new category button
        add_category_button = QPushButton("+")
        add_category_button.setFixedWidth(30)
        add_category_button.clicked.connect(self.quick_add_category)

        add_transaction_layout.addWidget(QLabel("Date:"))
        add_transaction_layout.addWidget(self.date_input)
        add_transaction_layout.addWidget(QLabel("Category:"))
        add_transaction_layout.addWidget(self.category_input)
        add_transaction_layout.addWidget(add_category_button)
        add_transaction_layout.addWidget(QLabel("Amount:"))
        add_transaction_layout.addWidget(self.amount_input)
        add_transaction_layout.addWidget(QLabel("Type:"))
        add_transaction_layout.addWidget(self.transaction_type_input)
        add_transaction_layout.addWidget(add_button)

        transactions_layout.addLayout(add_transaction_layout)
        transactions_layout.addWidget(QLabel("Comment:"))
        transactions_layout.addWidget(self.comment_input)

        self.transaction_type_input.addItems(["Expense", "Income", "Savings", "Investment"])
        self.transaction_type_input.currentTextChanged.connect(self.on_transaction_type_changed)

        self.goal_selection = QComboBox()
        self.goal_selection.setVisible(False)
        add_transaction_layout.addWidget(self.goal_selection)


        # Transaction Table
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(6)
        self.transaction_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Type", "Comment", "Action"])
        self.transaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        transactions_layout.addWidget(self.transaction_table)

        return transactions_tab

    def on_transaction_type_changed(self, transaction_type):
        if transaction_type in ['Savings', 'Investment']:
            self.load_goals_for_selection(transaction_type)
            self.goal_selection.setVisible(True)
        else:
            self.goal_selection.setVisible(False)

    def load_goals_for_selection(self, goal_type):
        goals = self.investment_savings_model.get_goals_by_type(goal_type)
        self.goal_selection.clear()
        for goal in goals:
            self.goal_selection.addItem(goal['name'], goal['id'])

    def open_config_dialog(self):
        dialog = ConfigDialog(self.category_model, self.currency_manager)
        dialog.currency_changed.connect(self.update_currency_display)
        if dialog.exec():
            self.load_categories()
            self.update_currency_display()


    def load_categories(self):
        categories = self.category_model.get_category_names()
        self.category_input.clear()
        self.category_input.addItems(categories)

    def quick_add_category(self):
        category, ok = QInputDialog.getText(self, "Add Category", "Enter new category name:")
        if ok and category:
            self.category_model.add_category(category)
            self.load_categories()
            self.category_input.setCurrentText(category)

    @pyqtSlot()
    def add_transaction(self):
        date = self.date_input.text()
        category = self.category_input.currentText()
        amount = self.amount_input.text()
        transaction_type = self.transaction_type_input.currentText()
        goal_id = None
        if transaction_type in ['Savings', 'Investment']:
            goal_id = self.goal_selection.currentData()
        comment = self.comment_input.toPlainText()
        currency = self.currency_manager.get_default_currency()

        if not all([date, category, amount, transaction_type]):
            QMessageBox.warning(self, "Invalid Input", "Please fill in all required fields.")
            return

        try:
            amount = float(amount)
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number for the amount.")
            return

        try:
            self.transaction_model.add_transaction(
                date, category, amount, transaction_type, comment, currency.code, goal_id
            )
            self.load_transactions()
            self.amount_input.clear()
            self.comment_input.clear()
            if goal_id:
                self.investment_savings_ui.update_goals_display()
            QMessageBox.information(self, "Success", "Transaction added successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding the transaction: {str(e)}")
            logging.exception("Error adding transaction")

    @pyqtSlot()
    def load_transactions(self):
        transactions = self.transaction_model.get_all_transactions()
        self.transaction_table.setColumnCount(7)  # Adjust to 7 columns
        self.transaction_table.setHorizontalHeaderLabels(
            ["Date", "Category", "Amount", "Currency", "Type", "Comment", "Action"])
        self.transaction_table.setRowCount(len(transactions))
        for row, transaction in enumerate(transactions):
            self.transaction_table.setItem(row, 0, QTableWidgetItem(transaction[1]))  # Date
            self.transaction_table.setItem(row, 1, QTableWidgetItem(transaction[2]))  # Category
            self.transaction_table.setItem(row, 2, QTableWidgetItem(f"{transaction[3]:.2f}"))  # Amount
            currency = self.currency_manager.get_currency_by_code(transaction[6])  # Assuming currency is the 7th field
            self.transaction_table.setItem(row, 3, QTableWidgetItem(str(currency)))  # Currency
            self.transaction_table.setItem(row, 4, QTableWidgetItem(transaction[4]))  # Type
            self.transaction_table.setItem(row, 5, QTableWidgetItem(transaction[5]))  # Comment

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(self.create_delete_transaction_function(transaction[0]))
            self.transaction_table.setCellWidget(row, 6, delete_button)  # Action

    def create_delete_transaction_function(self, transaction_id):
        return lambda: self.delete_transaction(transaction_id)

    @pyqtSlot(int)
    def delete_transaction(self, transaction_id):
        reply = QMessageBox.question(self, "Delete Transaction",
                                     "Are you sure you want to delete this transaction?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.transaction_model.delete_transaction(transaction_id)
            self.load_transactions()


    def update_currency_display(self, currency_code=None):
        current_currency = self.currency_manager.get_default_currency()

        # Update Investment & Savings tab
        self.investment_savings_ui.update_currency()

        # Update Transactions tab
        self.amount_input.setPlaceholderText(f"Amount ({current_currency.symbol})")
        self.load_transactions()  # Reload transactions to update currency display

        # Update Debt Management tab
        self.debt_management_ui.update_currency()

        # Update Debt Payoff Planner tab
        self.debt_planner.update_currency()

        # Update Budget Planner tab (if it has currency-related displays)
        if hasattr(self.budget_planner, 'update_currency'):
            self.budget_planner.update_currency()

        # Update Smart Savings Advisor tab (if it has currency-related displays)
        if hasattr(self.smart_savings_advisor, 'update_currency'):
            self.smart_savings_advisor.update_currency()