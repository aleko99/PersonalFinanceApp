from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QInputDialog, QProgressBar)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class DebtManagementUI(QWidget):
    def __init__(self, debt_model, currency_manager):
        super().__init__()
        self.model = debt_model
        self.currency_manager = currency_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form for adding new debts
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Debt Name")
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText(f"Balance ({self.currency_manager.get_default_currency().symbol})")
        self.apr_input = QLineEdit()
        self.apr_input.setPlaceholderText("APR (%)")
        add_button = QPushButton("Add Debt")
        add_button.clicked.connect(self.add_debt)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.balance_input)
        form_layout.addWidget(self.apr_input)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)

        # Table to display debts
        self.debts_table = QTableWidget()
        self.debts_table.setColumnCount(8)
        self.debts_table.setHorizontalHeaderLabels([
            "Name", "Original Balance", "Current Balance", "APR", "Progress", "Actions", "Make Payment", "View Details"
        ])
        self.debts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.debts_table)

        self.update_debts_display()

    def add_debt(self):
        name = self.name_input.text()
        try:
            balance = float(self.balance_input.text())
            apr = float(self.apr_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for balance and APR.")
            return

        self.model.add_debt(name, balance, apr)
        self.update_debts_display()
        self.clear_inputs()

    def update_debts_display(self):
        debts = self.model.get_all_debts()
        self.debts_table.setRowCount(len(debts))
        currency_symbol = self.currency_manager.get_default_currency().symbol
        for row, debt in enumerate(debts):
            self.debts_table.setItem(row, 0, QTableWidgetItem(debt[1]))  # Name
            self.debts_table.setItem(row, 1, QTableWidgetItem(f"{currency_symbol}{debt[2]:,.2f}"))  # Original Balance
            self.debts_table.setItem(row, 2, QTableWidgetItem(f"{currency_symbol}{debt[3]:,.2f}"))  # Current Balance
            self.debts_table.setItem(row, 3, QTableWidgetItem(f"{debt[4]:.2f}%"))  # APR

            progress = self.model.calculate_repayment_progress(debt[0])
            progress_bar = QProgressBar()
            progress_bar.setValue(int(progress))
            self.debts_table.setCellWidget(row, 4, progress_bar)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, d_id=debt[0]: self.delete_debt(d_id))
            self.debts_table.setCellWidget(row, 5, delete_button)

            payment_button = QPushButton("Make Payment")
            payment_button.clicked.connect(lambda _, d_id=debt[0]: self.make_payment(d_id))
            self.debts_table.setCellWidget(row, 6, payment_button)

            details_button = QPushButton("Details")
            details_button.clicked.connect(lambda _, d_id=debt[0]: self.view_debt_details(d_id))
            self.debts_table.setCellWidget(row, 7, details_button)

            self.apply_row_color(row, progress)

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

        for col in range(self.debts_table.columnCount()):
            item = self.debts_table.item(row, col)
            if item:
                item.setBackground(color)

    def delete_debt(self, debt_id):
        reply = QMessageBox.question(self, "Delete Debt",
                                     "Are you sure you want to delete this debt?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.model.delete_debt(debt_id)
            self.update_debts_display()

    def make_payment(self, debt_id):
        amount, ok = QInputDialog.getDouble(self, "Make Payment", "Enter payment amount:",
                                            0, 0, 1000000, 2)
        if ok and amount > 0:
            self.model.update_debt_balance(debt_id, amount)
            self.update_debts_display()

    def view_debt_details(self, debt_id):
        # Implement a method to show detailed information about the debt
        # This could open a new dialog with more information, payment history, etc.
        pass

    def clear_inputs(self):
        self.name_input.clear()
        self.balance_input.clear()
        self.apr_input.clear()

    def update_currency(self):
        currency_symbol = self.currency_manager.get_default_currency().symbol
        self.balance_input.setPlaceholderText(f"Balance ({currency_symbol})")
        self.update_debts_display()