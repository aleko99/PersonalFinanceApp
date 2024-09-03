from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QDialogButtonBox, QComboBox)
from PyQt6.QtCore import pyqtSignal

class ConfigDialog(QDialog):
    currency_changed = pyqtSignal(str)  # Signal to emit when currency is changed

    def __init__(self, category_model, currency_manager, parent=None):
        super().__init__(parent)
        self.category_model = category_model
        self.currency_manager = currency_manager
        self.setWindowTitle("Configuration")
        self.layout = QVBoxLayout(self)

        self.category_input = QLineEdit(self)
        self.add_category_button = QPushButton("Add Category", self)
        self.add_category_button.clicked.connect(self.add_category)

        self.category_list = QTableWidget(self)
        self.category_list.setColumnCount(2)
        self.category_list.setHorizontalHeaderLabels(["Category", "Action"])

        self.layout.addWidget(QLabel("Add New Category:"))
        self.layout.addWidget(self.category_input)
        self.layout.addWidget(self.add_category_button)
        self.layout.addWidget(QLabel("Existing Categories:"))
        self.layout.addWidget(self.category_list)

        self.currency_combo = QComboBox(self)
        for currency in self.currency_manager.get_all_currencies():
            self.currency_combo.addItem(str(currency), currency.code)
        self.currency_combo.setCurrentText(str(self.currency_manager.get_default_currency()))
        self.currency_combo.currentIndexChanged.connect(self.update_currency)

        self.layout.addWidget(QLabel("Default Currency:"))
        self.layout.addWidget(self.currency_combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.load_categories()

    def add_category(self):
        category = self.category_input.text().strip()
        if category:
            self.category_model.add_category(category)
            self.category_input.clear()
            self.load_categories()

    def load_categories(self):
        categories = self.category_model.get_all_categories()

        self.category_list.setRowCount(len(categories))
        for row, category in enumerate(categories):
            self.category_list.setItem(row, 0, QTableWidgetItem(category[1]))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, cid=category[0]: self.delete_category(cid))
            self.category_list.setCellWidget(row, 1, delete_button)

    def delete_category(self, category_id):
        self.category_model.delete_category(category_id)
        self.load_categories()

    def update_currency(self):
        selected_currency_code = self.currency_combo.currentData()
        self.currency_manager.set_default_currency(selected_currency_code)
        self.currency_changed.emit(selected_currency_code)  # Emit the signal with the new currency code

    def exec(self):
        result = super().exec()
        if result:
            # Emit the currency_changed signal when the dialog is accepted
            self.currency_changed.emit(self.currency_manager.get_default_currency().code)
        return result