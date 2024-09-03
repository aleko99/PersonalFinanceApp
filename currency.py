class Currency:
    def __init__(self, code, symbol, name):
        self.code = code
        self.symbol = symbol
        self.name = name

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class CurrencyManager:
    def __init__(self):
        self.currencies = [
            Currency("GBP", "£", "British Pound"),
            Currency("USD", "$", "US Dollar"),
            Currency("EUR", "€", "Euro"),
            # Add more currencies as needed
        ]
        self.default_currency = self.currencies[0]  # Set GBP as default

    def get_all_currencies(self):
        return self.currencies

    def get_currency_by_code(self, code):
        return next((c for c in self.currencies if c.code == code), None)

    def set_default_currency(self, currency_code):
        currency = self.get_currency_by_code(currency_code)
        if currency:
            self.default_currency = currency

    def get_default_currency(self):
        return self.default_currency

