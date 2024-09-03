import sys
import logging
import argparse
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database import init_db


def setup_logging(debug_mode=False):
    # Create a logger
    logger = logging.getLogger('ExpenseTracker')

    # Set the logging level based on debug_mode
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler('expense_tracker.log')
    fh.setLevel(logging.DEBUG)

    # Create console handler with a level based on debug_mode
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def parse_arguments():
    parser = argparse.ArgumentParser(description="Expense Tracker Application")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = setup_logging(debug_mode=args.debug)

    if args.debug:
        logger.info("Debug mode enabled")

    logger.info("Starting Expense Tracker application")

    app = QApplication(sys.argv)
    logger.debug("QApplication instance created")

    init_db()
    logger.debug("Database initialized")

    window = MainWindow()
    logger.debug("MainWindow instance created")

    window.show()
    logger.info("Main window displayed")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()