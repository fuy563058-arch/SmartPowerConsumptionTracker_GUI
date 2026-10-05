import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from database.database import Database
from features.Appliances.service import ApplianceService
from features.Appliances.view import ApplianceView


def main():
    db = Database()
    db.create_tables()

    app = QApplication(sys.argv)
    qss = Path(__file__).with_name("style.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))

    window = ApplianceView(ApplianceService(db))
    window.setWindowTitle("Smart Power Consumption Tracker")
    window.resize(900, 650)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
