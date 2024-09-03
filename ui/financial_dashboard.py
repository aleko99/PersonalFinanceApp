from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QComboBox, QStackedWidget, QLabel)
from PyQt6.QtCore import Qt
import numpy as np
from matplotlib import dates as mdates


class ChartWidget(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        layout = QVBoxLayout(self)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def update_chart(self):
        raise NotImplementedError("Subclasses must implement update_chart method")


class SpendingBreakdownChart(ChartWidget):
    def update_chart(self):
        spending_data = self.model.get_spending_by_category()
        self.ax.clear()
        categories = list(spending_data.keys())
        amounts = list(spending_data.values())
        self.ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
        self.ax.axis('equal')
        self.ax.set_title('Spending Breakdown by Category')
        self.canvas.draw()


class IncomeVsExpensesChart(ChartWidget):
    def update_chart(self):
        data = self.model.get_income_vs_expenses()
        self.ax.clear()
        months = list(data.keys())
        income = [d['income'] for d in data.values()]
        expenses = [d['expenses'] for d in data.values()]
        x = range(len(months))
        width = 0.35
        self.ax.bar([i - width / 2 for i in x], income, width, label='Income')
        self.ax.bar([i + width / 2 for i in x], expenses, width, label='Expenses')
        self.ax.set_ylabel('Amount')
        self.ax.set_title('Income vs Expenses')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(months, rotation=45)
        self.ax.legend()
        self.canvas.draw()


class NetWorthTrendChart(ChartWidget):
    def update_chart(self):
        data = self.model.get_net_worth_trend()
        self.ax.clear()

        dates = [datetime.strptime(date, '%Y-%m') for date in data.keys()]
        net_worth = list(data.values())

        self.ax.plot(dates, net_worth)
        self.ax.set_ylabel('Net Worth')
        self.ax.set_title('Net Worth Trend')

        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.ax.xaxis.set_major_locator(mdates.MonthLocator())

        # Rotate and align the tick labels so they look better
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Use a more appropriate date range
        self.ax.set_xlim([min(dates), max(dates)])

        # Adjust the subplot layout to make room for the rotated labels
        self.figure.tight_layout()

        self.canvas.draw()


class DebtRepaymentProgressChart(ChartWidget):
    def update_chart(self):
        data = self.model.get_debt_repayment_progress()
        self.ax.clear()
        debts = list(data.keys())
        progress = list(data.values())
        y_pos = np.arange(len(debts))
        self.ax.barh(y_pos, progress)
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(debts)
        self.ax.invert_yaxis()
        self.ax.set_xlabel('Repayment Progress (%)')
        self.ax.set_title('Debt Repayment Progress')
        for i, v in enumerate(progress):
            self.ax.text(v, i, f'{v}%', va='center')
        self.canvas.draw()


class FinancialDashboard(QWidget):
    def __init__(self, transaction_model, debt_model, investment_model):
        super().__init__()
        self.transaction_model = transaction_model
        self.debt_model = debt_model
        self.investment_model = investment_model
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Chart selection dropdown
        self.chart_selector = QComboBox()
        self.chart_selector.addItems([
            "Spending Breakdown",
            "Income vs Expenses",
            "Net Worth Trend",
            "Debt Repayment Progress"
        ])
        self.chart_selector.currentIndexChanged.connect(self.change_chart)
        layout.addWidget(self.chart_selector)

        # Stacked widget to hold different charts
        self.chart_stack = QStackedWidget()
        self.spending_chart = SpendingBreakdownChart(self.transaction_model)
        self.income_expenses_chart = IncomeVsExpensesChart(self.transaction_model)
        self.net_worth_chart = NetWorthTrendChart(self.investment_model)
        self.debt_progress_chart = DebtRepaymentProgressChart(self.debt_model)

        self.chart_stack.addWidget(self.spending_chart)
        self.chart_stack.addWidget(self.income_expenses_chart)
        self.chart_stack.addWidget(self.net_worth_chart)
        self.chart_stack.addWidget(self.debt_progress_chart)

        layout.addWidget(self.chart_stack)

        # Refresh button
        refresh_button = QPushButton("Refresh Charts")
        refresh_button.clicked.connect(self.refresh_charts)
        layout.addWidget(refresh_button)

    def change_chart(self, index):
        self.chart_stack.setCurrentIndex(index)
        self.refresh_charts()

    def refresh_charts(self):
        current_chart = self.chart_stack.currentWidget()
        if current_chart:
            current_chart.update_chart()