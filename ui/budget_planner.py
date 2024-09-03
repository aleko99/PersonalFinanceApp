import sys
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QScrollArea, QFrame,
                             QGridLayout, QSizePolicy, QMessageBox, QTableWidget, QTableWidgetItem, QInputDialog,
                             QDialogButtonBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from dateutil.relativedelta import relativedelta
import logging
import models.budget_models

logger = logging.getLogger(__name__)
class BudgetUpdateDialog(QDialog):
    def __init__(self, current_budget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Budget")
        self.current_budget = current_budget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.category_inputs = {}

        for category, amount in self.current_budget.items():
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(category))
            amount_input = QLineEdit(str(amount))
            self.category_inputs[category] = amount_input
            row_layout.addWidget(amount_input)
            layout.addLayout(row_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_updated_budget(self):
        updated_budget = {}
        for category, input_widget in self.category_inputs.items():
            try:
                updated_budget[category] = float(input_widget.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Please enter a valid number for {category}")
                return None
        return updated_budget


class BudgetItemWidget(QFrame):
    deleted = pyqtSignal(object)

    def __init__(self, name, amount, category, item_type):
        super().__init__()
        self.name = name
        self.amount = amount
        self.category = category
        self.type = item_type
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(f"{self.name}: ${self.amount} ({self.type})"))
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_item)
        layout.addWidget(delete_button)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"background-color: {self.get_category_color()};")

    def delete_item(self):
        self.deleted.emit(self)

    def get_category_color(self):
        colors = {
            "Mandatory": "#FFCCCB",  # Light Red
            "Flexible": "#FFFACD",  # Light Yellow
            "Optional": "#E0FFFF"  # Light Cyan
        }
        return colors.get(self.type, "white")


class BudgetPlanner(QWidget):
    def __init__(self, category_model, budget_model, transaction_model):
        super().__init__()
        self.category_model = category_model
        self.budget_model = budget_model
        self.transaction_model = transaction_model
        self.current_month = datetime.now().replace(day=1)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Month selection
        month_layout = QHBoxLayout()
        self.month_selector = QComboBox()
        month_layout.addWidget(QLabel("Select Month:"))
        month_layout.addWidget(self.month_selector)
        main_layout.addLayout(month_layout)

        # Income input
        income_layout = QHBoxLayout()
        self.income_input = QLineEdit()
        self.income_input.setPlaceholderText("Enter your total income")
        self.income_input.editingFinished.connect(self.save_total_income)
        income_layout.addWidget(QLabel("Total Income:"))
        income_layout.addWidget(self.income_input)
        main_layout.addLayout(income_layout)

        # Input fields for budget items
        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.category_input = QComboBox()
        self.type_input = QComboBox()
        self.type_input.addItems(["Mandatory", "Flexible", "Optional"])
        add_button = QPushButton("Add Item")
        add_button.clicked.connect(self.add_budget_item)

        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.amount_input)
        input_layout.addWidget(self.category_input)
        input_layout.addWidget(self.type_input)
        input_layout.addWidget(add_button)
        main_layout.addLayout(input_layout)

        # Budget table
        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(6)
        self.budget_table.setHorizontalHeaderLabels(["Category", "Budgeted", "Type", "Actual", "Remaining", "Actions"])
        main_layout.addWidget(self.budget_table)

        # Budget items display (consider if this is still needed with the table view)
        sections_layout = QVBoxLayout()
        self.mandatory_section = CollapsibleSection("Mandatory Items")
        self.flexible_section = CollapsibleSection("Flexible Items")
        self.optional_section = CollapsibleSection("Optional Items")

        sections_layout.addWidget(self.mandatory_section)
        sections_layout.addWidget(self.flexible_section)
        sections_layout.addWidget(self.optional_section)

        main_layout.addLayout(sections_layout)

        # Totals and remaining display
        totals_layout = QHBoxLayout()
        self.total_budgeted = QLabel("Total Budgeted: $0")
        self.total_actual = QLabel("Total Actual: $0")
        self.total_remaining = QLabel("Total Remaining: $0")
        totals_layout.addWidget(self.total_budgeted)
        totals_layout.addWidget(self.total_actual)
        totals_layout.addWidget(self.total_remaining)
        main_layout.addLayout(totals_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.new_month_button = QPushButton("Create Next Month's Budget")
        self.new_month_button.clicked.connect(self.create_next_month_budget)
        self.update_button = QPushButton("Update Budget")
        self.update_button.clicked.connect(self.update_current_budget)
        button_layout.addWidget(self.new_month_button)
        button_layout.addWidget(self.update_button)
        main_layout.addLayout(button_layout)

        # Initialize data
        self.load_categories()
        self.update_month_selector()
        self.load_current_month_budget()

        # Connect signals
        self.income_input.textChanged.connect(self.update_budget_remaining)
        self.month_selector.currentIndexChanged.connect(self.load_selected_month_budget)

    def load_categories(self):
        categories = self.category_model.get_category_names()
        self.category_input.clear()
        self.category_input.addItems(categories)
        #self.update_budget_table()

    def save_total_income(self):
        try:
            total_income = float(self.income_input.text() or 0)
            self.budget_model.update_total_income(self.current_month, total_income)
            logger.info(f"Saved total income: {total_income}")
            self.update_budget_remaining()  # Update the display immediately
        except ValueError:
            logger.warning("Invalid total income entered")
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for total income.")

    def update_month_selector(self):
        self.month_selector.clear()
        months = self.budget_model.get_available_months()
        for month in months:
            self.month_selector.addItem(month.strftime("%B %Y"), month)
        self.month_selector.setCurrentIndex(self.month_selector.count() - 1)
        self.month_selector.currentIndexChanged.connect(self.load_selected_month_budget)

    def load_current_month_budget(self):
        budget = self.budget_model.get_budget(self.current_month)
        total_income = self.budget_model.get_total_income(self.current_month)
        self.income_input.setText(str(total_income))
        self.display_budget(budget)

    def load_selected_month_budget(self):
        selected_month = self.month_selector.currentData()
        budget = self.budget_model.get_budget(selected_month)
        total_income = self.budget_model.get_total_income(selected_month)
        self.income_input.setText(str(total_income))
        self.display_budget(budget)

    def display_budget(self, budget):
        # Filter out the TotalIncome entry from the budget display
        filtered_budget = {k: v for k, v in budget.items() if k != 'TotalIncome'}

        self.budget_table.setRowCount(len(filtered_budget))
        for row, (category, item) in enumerate(filtered_budget.items()):
            self.budget_table.setItem(row, 0, QTableWidgetItem(category))

            if isinstance(item, dict):
                amount = item['amount']
                item_type = item.get('type', 'Mandatory')
            else:
                amount = item
                item_type = 'Mandatory'

            self.budget_table.setItem(row, 1, QTableWidgetItem(f"${amount:.2f}"))
            self.budget_table.setItem(row, 2, QTableWidgetItem(item_type))

            actual = self.transaction_model.get_category_spending(self.current_month, category)
            self.budget_table.setItem(row, 3, QTableWidgetItem(f"${actual:.2f}"))

            remaining = amount - actual
            self.budget_table.setItem(row, 4, QTableWidgetItem(f"${remaining:.2f}"))

            # Create a widget to hold both Edit and Delete buttons
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda _, c=category, a=amount: self.edit_budget_item(c, a))
            button_layout.addWidget(edit_button)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, c=category: self.delete_budget_item(c))
            button_layout.addWidget(delete_button)

            self.budget_table.setCellWidget(row, 5, button_widget)

        self.budget_table.resizeColumnsToContents()
        self.update_totals()
        self.update_budget_remaining()

        # Update the income input field
        total_income = self.budget_model.get_total_income(self.current_month)
        self.income_input.setText(f"{total_income:.2f}")


    def edit_budget_item(self, category, current_amount):
        new_amount, ok = QInputDialog.getDouble(self, f"Edit {category}",
                                                "Enter new amount:",
                                                current_amount, 0, 1000000, 2)
        if ok:
            current_budget = self.budget_model.get_budget(self.current_month)
            if isinstance(current_budget[category], dict):
                current_budget[category]['amount'] = new_amount
            else:
                current_budget[category] = {'amount': new_amount, 'type': 'Mandatory'}
            self.budget_model.update_budget(self.current_month, current_budget)
            self.load_current_month_budget()

    def update_section(self, section, items):
        try:
            logger.info(f"Updating section {section.title} with {len(items)} items")
            # Clear existing items in the layout
            for i in reversed(range(section.content_layout.count())):
                widget = section.content_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Add updated items to the layout
            for category, item in items:
                if isinstance(item, dict):
                    amount = item['amount']
                else:
                    amount = item

                item_widget = QLabel(f"{category}: ${amount:.2f}")
                item_widget.setStyleSheet("""
                     background-color: #f0f0f0;
                     border: 1px solid #ddd;
                     border-radius: 5px;
                     padding: 5px;
                     margin: 2px;
                 """)
                font = QFont()
                font.setPointSize(10)
                item_widget.setFont(font)
                item_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                section.add_item(item_widget)

            logger.info(f"Section {section.title} updated successfully")
        except Exception as e:
            logger.exception(f"Error updating section {section.title}: {str(e)}")
            QMessageBox.warning(self, "Warning", f"An error occurred while updating {section.title}: {str(e)}")

    def refresh_budget_display(self):
        try:
            logger.info("Starting to refresh budget display")
            # Reload all budget items from the database
            all_items = self.budget_model.get_budget(self.current_month)
            total_income = self.budget_model.get_total_income(self.current_month)
            logger.debug(f"Retrieved budget items: {all_items}")
            logger.debug(f"Retrieved total income: {total_income}")

            # Update main table
            self.display_budget(all_items)

            # Set total income
            self.income_input.setText(f"{total_income:.2f}")

            # Update Mandatory, Flexible, and Optional sections
            self.update_category_sections(all_items)

            # Update totals
            self.update_totals()
            self.update_budget_remaining()

            logger.info("Budget display refreshed successfully")
        except Exception as e:
            logger.exception(f"Error refreshing budget display: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while refreshing the budget display: {str(e)}")

    def update_category_sections(self, items):
        try:
            logger.info("Updating category sections")
            mandatory_items = []
            flexible_items = []
            optional_items = []

            for category, item in items.items():
                if isinstance(item, dict):
                    item_type = item.get('type', 'Mandatory')
                else:
                    item_type = 'Mandatory'

                if item_type == 'Mandatory':
                    mandatory_items.append((category, item))
                elif item_type == 'Flexible':
                    flexible_items.append((category, item))
                elif item_type == 'Optional':
                    optional_items.append((category, item))

            self.update_section(self.mandatory_section, mandatory_items)
            self.update_section(self.flexible_section, flexible_items)
            self.update_section(self.optional_section, optional_items)
            logger.info("Category sections updated successfully")
        except Exception as e:
            logger.exception(f"Error updating category sections: {str(e)}")
            raise

    def get_item_type(self, category):
        # Implement logic to determine the type of the category
        # This could be based on a predefined mapping or some other logic
        # For now, let's assume all items are "Mandatory"
        return "Mandatory"


    def update_totals(self):
        total_budgeted = 0
        total_actual = 0
        for row in range(self.budget_table.rowCount()):
            try:
                budgeted = float(self.budget_table.item(row, 1).text().replace('$', ''))
                actual = float(self.budget_table.item(row, 3).text().replace('$', ''))
                total_budgeted += budgeted
                total_actual += actual
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing row {row} in update_totals: {str(e)}")

        total_remaining = total_budgeted - total_actual

        self.total_budgeted.setText(f"Total Budgeted: ${total_budgeted:.2f}")
        self.total_actual.setText(f"Total Actual: ${total_actual:.2f}")
        self.total_remaining.setText(f"Total Remaining: ${total_remaining:.2f}")

        logger.info(
            f"Updated totals: Budgeted ${total_budgeted:.2f}, Actual ${total_actual:.2f}, Remaining ${total_remaining:.2f}")

    def clear_inputs(self):
        self.name_input.clear()
        self.amount_input.clear()
        self.category_input.setCurrentIndex(0)

    def create_next_month_budget(self):
        next_month = self.current_month + relativedelta(months=1)
        current_budget = self.budget_model.get_budget(self.current_month)
        self.budget_model.create_budget(next_month, current_budget)
        self.current_month = next_month
        self.update_month_selector()
        self.load_current_month_budget()

    def update_current_budget(self):
        current_budget = self.budget_model.get_budget(self.current_month)
        dialog = BudgetUpdateDialog(current_budget, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_budget = dialog.get_updated_budget()
            if updated_budget:
                self.budget_model.update_budget(self.current_month, updated_budget)
                self.load_current_month_budget()

    def add_budget_category(self):
        category, ok = QInputDialog.getText(self, "Add Category", "Enter new category name:")
        if ok and category:
            self.category_model.add_category(category)
            self.load_categories()
            current_budget = self.budget_model.get_budget(self.current_month)
            current_budget[category] = 0
            self.budget_model.update_budget(self.current_month, current_budget)
            self.load_current_month_budget()

    def delete_budget_item(self, category):
        reply = QMessageBox.question(self, 'Delete Budget Item',
                                     f"Are you sure you want to delete the budget item '{category}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.budget_model.delete_budget_item(self.current_month, category)
                if success:
                    logger.info(f"Deleted budget item: {category}")
                    QMessageBox.information(self, "Success", f"Budget item '{category}' has been deleted.")
                    self.refresh_budget_display()  # Refresh the display after deletion
                else:
                    logger.warning(f"Failed to delete budget item: {category}")
                    QMessageBox.warning(self, "Warning", f"Failed to delete budget item '{category}'.")
            except Exception as e:
                logger.exception(f"Error deleting budget item {category}: {str(e)}")
                QMessageBox.critical(self, "Error", f"An error occurred while deleting the budget item: {str(e)}")

    def add_budget_item(self):
        logger.info("Attempting to add a new budget item")

        category = self.category_input.currentText()
        if not category:
            QMessageBox.warning(self, "Invalid Input", "Please select a category.")
            logger.warning("Attempt to add budget item without selecting a category")
            return

        try:
            amount = float(self.amount_input.text())
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Please enter a valid positive amount. Error: {str(e)}")
            logger.warning(f"Invalid amount entered: {self.amount_input.text()}")
            return

        item_type = self.type_input.currentText()  # Get the selected item type

        try:
            current_budget = self.budget_model.get_budget(self.current_month)
            total_income = self.budget_model.get_total_income(self.current_month)
            logger.debug(f"Current budget: {current_budget}")

            if category not in current_budget:
                current_budget[category] = {'amount': 0, 'type': item_type}

            if isinstance(current_budget[category], dict):
                current_budget[category]['amount'] += amount
                current_budget[category]['type'] = item_type
            else:
                current_budget[category] = {'amount': current_budget[category] + amount, 'type': item_type}

            logger.info(f"Updating budget for {category}: adding {amount} of type {item_type}")
            self.budget_model.update_budget(self.current_month, current_budget)
            self.budget_model.update_total_income(self.current_month, total_income)  # Preserve total income

            self.load_current_month_budget()
            self.clear_inputs()
            QMessageBox.information(self, "Success", f"Added ${amount:.2f} to {category} as {item_type}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding the budget item: {str(e)}")
            logger.exception("Error in add_budget_item")

        try:
            self.refresh_budget_display()
        except Exception as e:
            logger.exception(f"Error refreshing budget display after adding item: {str(e)}")
            QMessageBox.warning(self, "Warning",
                                f"The item was added, but there was an error refreshing the display: {str(e)}")

    def update_budget_remaining(self):
        total_income = self.budget_model.get_total_income(self.current_month)

        total_budgeted = 0
        for row in range(self.budget_table.rowCount()):
            try:
                budgeted = float(self.budget_table.item(row, 1).text().replace('$', ''))
                total_budgeted += budgeted
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing row {row} in update_budget_remaining: {str(e)}")

        remaining = total_income - total_budgeted

        self.total_remaining.setText(f"Total Remaining: ${remaining:.2f}")

        if remaining < 0:
            self.total_remaining.setStyleSheet("color: red;")
        else:
            self.total_remaining.setStyleSheet("color: green;")

        logger.info(f"Updated budget remaining: ${remaining:.2f}")

    @pyqtSlot()
    def load_budget_categories(self):
        categories = self.category_model.get_all_categories()
        self.budget_table.setRowCount(len(categories))
        for row, category in enumerate(categories):
            self.budget_table.setItem(row, 0, QTableWidgetItem(category[1]))
            amount_item = QTableWidgetItem("0")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.budget_table.setItem(row, 1, amount_item)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(self.create_delete_category_function(row))
            self.budget_table.setCellWidget(row, 2, delete_button)
        self.budget_table.itemChanged.connect(self.update_budget_remaining)

    def create_delete_category_function(self, row):
        return lambda: self.delete_budget_category(row)


class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content.setLayout(self.content_layout)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedWidth(30)
        self.toggle_button.clicked.connect(self.toggle_content)
        header_layout.addWidget(self.toggle_button)

        header_label = QLabel(self.title)
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Scrollable content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content)
        self.scroll_area.setMaximumHeight(300)  # Set a default max height
        layout.addWidget(self.scroll_area)

    def toggle_content(self):
        if self.scroll_area.isVisible():
            self.scroll_area.hide()
            self.toggle_button.setText("▶")
        else:
            self.scroll_area.show()
            self.toggle_button.setText("▼")

    def add_item(self, item):
        self.content_layout.addWidget(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from models.category import CategoryModel
    from models.budget_models import BudgetModel, TransactionModel

    category_model = CategoryModel()
    budget_model = BudgetModel()
    transaction_model = TransactionModel()
    budget_planner = BudgetPlanner(category_model, budget_model, transaction_model)
    budget_planner.show()
    sys.exit(app.exec())

