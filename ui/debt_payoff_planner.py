import logging
import math
from datetime import datetime

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                             QHeaderView, QMessageBox, QDialogButtonBox, QDialog, QInputDialog, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSlot

logger = logging.getLogger('ExpenseTracker')


class DebtPriorityDialog(QDialog):
    def __init__(self, debts, currency_manager, parent=None):
        super().__init__(parent)
        self.debts = debts
        self.currency_manager = currency_manager
        self.setWindowTitle("Set Debt Priorities")
        self.layout = QVBoxLayout(self)

        self.priority_inputs = []
        currency_symbol = self.currency_manager.get_default_currency().symbol
        for debt in debts:
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{debt[1]} ({currency_symbol}{debt[3]:.2f} at {debt[4]}%):"))
            priority_input = QLineEdit()
            priority_input.setPlaceholderText("Priority (optional)")
            self.priority_inputs.append(priority_input)
            row_layout.addWidget(priority_input)
            self.layout.addLayout(row_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_priorities(self):
        return [int(input.text()) if input.text() else None for input in self.priority_inputs]

class DebtPayoffPlanner(QWidget):
    def __init__(self, debt_model, currency_manager):
        super().__init__()
        self.debt_model = debt_model
        self.currency_manager = currency_manager
        self.debt_priorities = {}
        self.last_payoff_plan = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Input for monthly payment
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Monthly Payment:"))
        self.payment_input = QLineEdit()
        payment_layout.addWidget(self.payment_input)
        layout.addLayout(payment_layout)

        # Dropdown for payoff method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Payoff Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Debt Avalanche", "Debt Snowball", "Custom Priority"])
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        # Target payoff date inputs
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Payoff Date (optional):"))
        self.target_date_input = QLineEdit()
        self.target_date_input.setPlaceholderText("YYYY-MM-DD")
        target_layout.addWidget(self.target_date_input)
        layout.addLayout(target_layout)

        # Buttons
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Payoff Plan")
        generate_button.clicked.connect(self.generate_payoff_plan)
        button_layout.addWidget(generate_button)

        set_priority_button = QPushButton("Set Debt Priorities")
        set_priority_button.clicked.connect(self.set_debt_priorities)
        button_layout.addWidget(set_priority_button)

        clear_button = QPushButton("Clear Plan")
        clear_button.clicked.connect(self.clear_payoff_plan)
        button_layout.addWidget(clear_button)

        layout.addLayout(button_layout)

        # Table for payoff plan
        self.plan_table = QTableWidget()
        self.plan_table.setColumnCount(7)
        self.plan_table.setHorizontalHeaderLabels([
            "Debt", "Initial Balance", "Interest Rate", "Monthly Payment",
            "Months to Payoff", "Total Interest Paid", "Final Balance"
        ])
        self.plan_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.plan_table)

        self.debt_priorities = {}

    @pyqtSlot()
    def set_debt_priorities(self):
        debts = self.debt_model.get_all_debts()
        dialog = DebtPriorityDialog(debts, self)
        if dialog.exec():
            priorities = dialog.get_priorities()
            self.debt_priorities = {debt[1]: priority for debt, priority in zip(debts, priorities) if priority is not None}
            logger.debug(f"Set custom debt priorities: {self.debt_priorities}")

    @pyqtSlot()
    def generate_payoff_plan(self):
        logger.debug("Generating payoff plan")
        try:
            monthly_payment = float(self.payment_input.text())
        except ValueError:
            logger.warning("Invalid monthly payment input")
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid monthly payment amount.")
            return

        method = self.method_combo.currentText()
        all_debts = self.debt_model.get_all_debts()

        if not all_debts:
            logger.info("No debts found for payoff plan")
            QMessageBox.information(self, "No Debts", "There are no debts to create a payoff plan for.")
            return

        target_date = None
        if self.target_date_input.text():
            try:
                target_date = datetime.strptime(self.target_date_input.text(), "%Y-%m-%d").date()
            except ValueError:
                logger.warning("Invalid target date input")
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid target date (YYYY-MM-DD) or leave it blank.")
                return

        # Filter debts based on priorities
        if self.debt_priorities:
            debts = [debt for debt in all_debts if debt[1] in self.debt_priorities]
        else:
            debts = all_debts

        logger.debug(f"Payoff method: {method}")
        logger.debug(f"Number of debts considered: {len(debts)}")
        logger.debug(f"Monthly payment: ${monthly_payment}")
        logger.debug(f"Target date: {target_date}")

        try:
            if method == "Debt Avalanche":
                sorted_debts = sorted(debts, key=lambda x: (x[3], x[2]), reverse=True)  # Sort by interest rate, then balance
            elif method == "Debt Snowball":
                sorted_debts = sorted(debts, key=lambda x: (x[2], x[3]))  # Sort by balance, then interest rate
            else:  # Custom Priority
                sorted_debts = sorted(debts, key=lambda x: (self.debt_priorities.get(x[1], float('inf')), x[3], x[2]))

            if target_date:
                required_payment = self.calculate_required_payment(sorted_debts, target_date)
                if required_payment > monthly_payment:
                    logger.info(f"Increased monthly payment to meet target date: ${required_payment:.2f}")
                    QMessageBox.information(self, "Payment Increased",
                                            f"To meet the target date, the monthly payment has been increased to ${required_payment:.2f}")
                    monthly_payment = required_payment

            payoff_plan = self.calculate_payoff_plan(sorted_debts, monthly_payment)
            self.display_payoff_plan(payoff_plan)
            logger.info("Payoff plan generated and displayed successfully")
        except Exception as e:
            logger.error(f"Error generating payoff plan: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred while generating the payoff plan: {str(e)}")


    def calculate_required_payment(self, debts, target_date):
        total_debt = sum(debt[2] for debt in debts)
        months_until_target = (target_date - datetime.now().date()).days / 30.44  # Average days in a month

        # Simple calculation, doesn't account for interest
        required_payment = total_debt / months_until_target

        # Adjust for minimum payments on other debts if using priorities
        if self.debt_priorities:
            other_debts_min_payments = sum(min(debt[2] * (debt[3] / 100 / 12), 50) for debt in self.debt_model.get_all_debts() if debt[1] not in self.debt_priorities)
            required_payment += other_debts_min_payments

        return required_payment

    def calculate_payoff_plan(self, debts, monthly_payment):
        logger.debug("Calculating payoff plan")
        payoff_plan = []
        total_months = 0
        remaining_debts = [list(debt) for debt in debts]  # [id, name, balance, apr]

        while remaining_debts and total_months < 1200:  # Limit to 100 years to prevent infinite loop
            month_payment = monthly_payment
            for debt in remaining_debts:
                balance = debt[2]
                apr = debt[3]
                monthly_interest = balance * (apr / 100 / 12)

                if month_payment > balance + monthly_interest:
                    payment = balance + monthly_interest
                    month_payment -= payment
                    debt[2] = 0  # Set balance to 0
                else:
                    payment = month_payment
                    debt[2] = balance + monthly_interest - payment
                    month_payment = 0

                # Update the debt in payoff_plan or add it if it's not there yet
                debt_in_plan = next((d for d in payoff_plan if d["name"] == debt[1]), None)
                if debt_in_plan:
                    debt_in_plan["total_interest"] += monthly_interest
                    debt_in_plan["months"] = total_months + 1
                    debt_in_plan["monthly_payment"] = max(debt_in_plan["monthly_payment"], payment - monthly_interest)
                    debt_in_plan["final_balance"] = debt[2]
                else:
                    payoff_plan.append({
                        "name": debt[1],
                        "starting_balance": balance,
                        "interest_rate": apr,
                        "monthly_payment": payment - monthly_interest,
                        "months": total_months + 1,
                        "total_interest": monthly_interest,
                        "final_balance": debt[2]
                    })

            remaining_debts = [debt for debt in remaining_debts if debt[2] > 0]
            total_months += 1

        if total_months >= 1200:
            logger.warning("Payoff plan calculation stopped after 100 years")

        logger.debug(f"Payoff plan calculated. Total months: {total_months}")
        return payoff_plan


    def display_payoff_plan(self, payoff_plan):
        logger.debug("Displaying payoff plan")
        self.last_payoff_plan = payoff_plan
        currency_symbol = self.currency_manager.get_default_currency().symbol
        if not payoff_plan:
            self.plan_table.setRowCount(1)
            self.plan_table.setItem(0, 0, QTableWidgetItem("No valid payoff plan could be generated"))
            logger.warning("Attempted to display empty payoff plan")
            return

        self.plan_table.setRowCount(len(payoff_plan) + 1)  # +1 for the total row
        for row, debt in enumerate(payoff_plan):
            self.plan_table.setItem(row, 0, QTableWidgetItem(debt["name"]))
            self.plan_table.setItem(row, 1, QTableWidgetItem(f"${debt['starting_balance']:.2f}"))
            self.plan_table.setItem(row, 2, QTableWidgetItem(f"{debt['interest_rate']}%"))
            self.plan_table.setItem(row, 3, QTableWidgetItem(f"${debt['monthly_payment']:.2f}"))
            self.plan_table.setItem(row, 4, QTableWidgetItem(str(debt["months"])))
            self.plan_table.setItem(row, 5, QTableWidgetItem(f"${debt['total_interest']:.2f}"))
            self.plan_table.setItem(row, 6, QTableWidgetItem(f"${debt['final_balance']:.2f}"))

        # Add total row
        total_row = len(payoff_plan)
        self.plan_table.setItem(total_row, 0, QTableWidgetItem("Total"))
        self.plan_table.setItem(total_row, 1, QTableWidgetItem(f"${sum(debt['starting_balance'] for debt in payoff_plan):.2f}"))
        self.plan_table.setItem(total_row, 2, QTableWidgetItem("-"))
        self.plan_table.setItem(total_row, 3, QTableWidgetItem(f"${sum(debt['monthly_payment'] for debt in payoff_plan):.2f}"))
        self.plan_table.setItem(total_row, 4, QTableWidgetItem(str(max(debt['months'] for debt in payoff_plan))))
        self.plan_table.setItem(total_row, 5, QTableWidgetItem(f"${sum(debt['total_interest'] for debt in payoff_plan):.2f}"))
        self.plan_table.setItem(total_row, 6, QTableWidgetItem(f"${sum(debt['final_balance'] for debt in payoff_plan):.2f}"))

        logger.debug("Payoff plan displayed in table")


    @pyqtSlot()
    def clear_payoff_plan(self):
        self.plan_table.setRowCount(0)
        self.payment_input.clear()
        self.target_date_input.clear()
        self.method_combo.setCurrentIndex(0)
        self.debt_priorities.clear()
        logger.debug("Payoff plan cleared")

    def update_currency(self):
        currency_symbol = self.currency_manager.get_default_currency().symbol

        # Update the payment input placeholder
        self.payment_input.setPlaceholderText(f"Monthly Payment ({currency_symbol})")

        # Update the table headers
        self.plan_table.setHorizontalHeaderLabels([
            "Debt", f"Initial Balance ({currency_symbol})", "Interest Rate",
            f"Monthly Payment ({currency_symbol})", "Months to Payoff",
            f"Total Interest Paid ({currency_symbol})", f"Final Balance ({currency_symbol})"
        ])

        # If there's a last payoff plan, redisplay it with the new currency
        if self.last_payoff_plan:
            self.display_payoff_plan(self.last_payoff_plan)


class DebtRepaymentUI(QWidget):
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
        self.debts_table.setColumnCount(7)
        self.debts_table.setHorizontalHeaderLabels(
            ["Name", "Original Balance", "Current Balance", "APR", "Progress", "Actions", "Make Payment"])
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
            # Assuming debt structure is (id, name, original_balance, current_balance, apr)
            # Adjust these indices if the structure is different
            self.debts_table.setItem(row, 0, QTableWidgetItem(debt[1]))  # Name
            self.debts_table.setItem(row, 1, QTableWidgetItem(f"{currency_symbol}{debt[2]:,.2f}"))  # Original Balance

            # Check if current_balance exists, otherwise use original_balance
            current_balance = debt[3] if len(debt) > 3 else debt[2]
            self.debts_table.setItem(row, 2,
                                     QTableWidgetItem(f"{currency_symbol}{current_balance:,.2f}"))  # Current Balance

            # Check if APR exists
            apr = debt[4] if len(debt) > 4 else 0
            self.debts_table.setItem(row, 3, QTableWidgetItem(f"{apr:.2f}%"))  # APR

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

    def clear_inputs(self):
        self.name_input.clear()
        self.balance_input.clear()
        self.apr_input.clear()

    def update_currency(self):
        currency_symbol = self.currency_manager.get_default_currency().symbol

        # Update the balance input placeholder
        self.balance_input.setPlaceholderText(f"Balance ({currency_symbol})")

        # Update the table headers
        self.debts_table.setHorizontalHeaderLabels([
            "Name", f"Original Balance ({currency_symbol})",
            f"Current Balance ({currency_symbol})", "APR",
            "Progress", "Actions", "Make Payment"
        ])

        # Refresh the debts display to update all currency values
        self.update_debts_display()
