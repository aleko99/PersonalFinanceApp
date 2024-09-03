import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
from models.smart_savings_advisor import EnhancedSmartSavingsAdvisor

logger = logging.getLogger(__name__)


class SmartSavingsAdvisorUI(QWidget):
    def __init__(self, transaction_model, debt_model, savings_model, investment_model):
        super().__init__()
        self.transaction_model = transaction_model
        self.debt_model = debt_model
        self.savings_goal_model = savings_model
        self.investment_model = investment_model

        self.advisor = EnhancedSmartSavingsAdvisor(
            self.transaction_model,
            self.debt_model,
            self.savings_goal_model,
            self.investment_model
        )

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        layout.addWidget(self.advice_text)

        refresh_button = QPushButton("Get Comprehensive Financial Advice")
        refresh_button.clicked.connect(self.update_advice)
        layout.addWidget(refresh_button)

    def update_advice(self):
        try:
            logger.info("Starting to generate comprehensive advice")
            advice = self.advisor.generate_comprehensive_advice()
            logger.info("Comprehensive advice generated successfully")
            self.advice_text.setPlainText("\n\n".join(advice))
        except Exception as e:
            logger.exception("An error occurred while generating comprehensive advice")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

        logger.info("Comprehensive advice update complete")