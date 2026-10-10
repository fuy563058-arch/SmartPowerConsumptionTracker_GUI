import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QTabWidget

from SmartPowerConsumptionTracker_GUI.database.database import Database
from SmartPowerConsumptionTracker_GUI.features.Appliance.dashboard import DashboardView
from SmartPowerConsumptionTracker_GUI.features.Appliance.services import ApplianceService
from SmartPowerConsumptionTracker_GUI.features.Appliance.view import ApplianceView

def main():
    db = Database()
    db.create_tables()

    app = QApplication(sys.argv)
    qss = Path(__file__).with_name("style.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))

    service = ApplianceService(db)
    dashboard = DashboardView(service)
    appliances = ApplianceView(service)

    tabs = QTabWidget()
    tabs.addTab(dashboard, "Dashboard")
    tabs.addTab(appliances, "Appliances")
    # data is edited in the Appliances tab, so re-read it whenever Dashboard is shown
    tabs.currentChanged.connect(lambda index: dashboard.refresh() if index == 0 else None)

    tabs.setWindowTitle("Smart Power Consumption Tracker")
    tabs.resize(1000, 700)
    tabs.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()