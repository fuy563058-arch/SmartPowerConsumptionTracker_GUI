from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .model import Appliance
from .service import SORT_OPTIONS

DEFAULT_TIP = "Select an appliance in the table to see an energy-saving tip."


class ApplianceView(QWidget):
    def __init__(self, service):
        super().__init__()
        self.setObjectName("applianceView")
        self.service = service
        self.selected_id: int | None = None
        self.appliances: list[Appliance] = []   # appliances currently in the table
        self.keyword = ""                       # current search keyword ("" = show all)
        self.build_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def build_ui(self):
        layout = QVBoxLayout(self)

        # --- input form ---
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Air conditioner")

        self.watts_input = QDoubleSpinBox()
        self.watts_input.setRange(0.0, 100000.0)
        self.watts_input.setDecimals(1)
        self.watts_input.setSuffix(" W")

        self.hours_input = QDoubleSpinBox()
        self.hours_input.setRange(0.0, 24.0)
        self.hours_input.setDecimals(2)
        self.hours_input.setSingleStep(0.5)
        self.hours_input.setSuffix(" h/day")

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.0, 10000.0)
        self.rate_input.setDecimals(2)
        self.rate_input.setPrefix("₱ ")
        self.rate_input.setSuffix(" / kWh")
        self.rate_input.setValue(self.service.get_rate())
        self.rate_input.valueChanged.connect(self.rate_changed)

        form.addRow("Appliance name", self.name_input)
        form.addRow("Wattage", self.watts_input)
        form.addRow("Hours used per day", self.hours_input)
        form.addRow("Electricity rate", self.rate_input)
        layout.addLayout(form)

        # --- CRUD buttons ---
        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add Appliance")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_appliance)
        self.update_button = QPushButton("Update Appliance")
        self.update_button.clicked.connect(self.update_appliance)
        self.delete_button = QPushButton("Delete Appliance")
        self.delete_button.clicked.connect(self.delete_appliance)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_form)
        for b in (self.add_button, self.update_button, self.delete_button, self.clear_button):
            buttons.addWidget(b)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        layout.addLayout(buttons)

        # --- search row ---
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search appliance by name…")
        self.search_input.returnPressed.connect(self.search_appliance)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_appliance)
        self.show_all_button = QPushButton("View All")
        self.show_all_button.clicked.connect(self.view_appliances)
        self.sort_combo = QComboBox()
        for key, (label, _, _) in SORT_OPTIONS.items():
            self.sort_combo.addItem(label, key)
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.show_all_button)
        search_row.addWidget(QLabel("Sort by"))
        search_row.addWidget(self.sort_combo)
        layout.addLayout(search_row)

        # --- table ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Appliance", "Watts", "Hours/day", "Daily kWh", "Monthly kWh", "Monthly Cost"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.load_selected)
        layout.addWidget(self.table)

        # --- totals + energy suggestion panel ---
        self.totals_label = QLabel()
        self.totals_label.setObjectName("totalsLabel")
        layout.addWidget(self.totals_label)

        self.tip_label = QLabel(DEFAULT_TIP)
        self.tip_label.setObjectName("tipPanel")
        self.tip_label.setWordWrap(True)
        layout.addWidget(self.tip_label)

    # ------------------------------------------------------------ helpers
    def _figures(self, a: Appliance, rate: float) -> tuple[float, float, float]:
        """Return (daily kWh, monthly kWh, monthly cost) for one appliance."""
        daily = self.service.daily_consumption(a.watts, a.hours)
        monthly = self.service.monthly_consumption(daily)
        cost = self.service.monthly_cost(monthly, rate)
        return daily, monthly, cost

    # ------------------------------------------------------------ actions
    def add_appliance(self):
        try:
            appliance = Appliance(
                self.name_input.text(), self.watts_input.value(), self.hours_input.value()
            )
            self.service.add_appliance(appliance)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Appliance", str(error))
            return
        daily, monthly, cost = self._figures(appliance, self.rate_input.value())
        QMessageBox.information(
            self,
            "Appliance Added",
            f"{appliance.name} was added.\n\n"
            f"Daily use: {daily:.3f} kWh\n"
            f"Monthly use: {monthly:.2f} kWh\n"
            f"Estimated monthly cost: ₱ {cost:,.2f}",
        )
        self.keyword = ""
        self.search_input.clear()
        self.clear_form()
        self.refresh()

    def view_appliances(self):
        self.keyword = ""
        self.search_input.clear()
        self.refresh()

    def search_appliance(self):
        self.keyword = self.search_input.text().strip()
        self.refresh()

    def update_appliance(self):
        if self.selected_id is None:
            return
        try:
            appliance = Appliance(
                self.name_input.text(), self.watts_input.value(),
                self.hours_input.value(), id=self.selected_id,
            )
            self.service.update_appliance(appliance)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Appliance", str(error))
            return
        self.clear_form()
        self.refresh()
        QMessageBox.information(self, "Appliance Updated", f"{appliance.name} was updated.")

    def delete_appliance(self):
        if self.selected_id is None:
            return
        name = next((a.name for a in self.appliances if a.id == self.selected_id), "Appliance")
        confirm = QMessageBox.question(
            self, "Delete Appliance", f"Are you sure you want to delete '{name}'?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_appliance(self.selected_id)
        except ValueError as error:
            QMessageBox.warning(self, "Delete Failed", str(error))
            return
        self.clear_form()
        self.refresh()
        QMessageBox.information(self, "Appliance Deleted", f"'{name}' was deleted.")

    def rate_changed(self, value: float):
        self.service.set_rate(value)
        self.refresh()

    # --------------------------------------------------- selection / form
    def load_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self.appliances):
            self.selected_id = None
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.tip_label.setText(DEFAULT_TIP)
            return
        appliance = self.appliances[rows[0].row()]
        self.selected_id = appliance.id
        self.name_input.setText(appliance.name)
        self.watts_input.setValue(appliance.watts)
        self.hours_input.setValue(appliance.hours)
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        _, _, cost = self._figures(appliance, self.rate_input.value())
        self.tip_label.setText(
            self.service.energy_suggestion(appliance.watts, appliance.hours, cost)
        )

    def clear_form(self):
        self.selected_id = None
        self.name_input.clear()
        self.watts_input.setValue(0)
        self.hours_input.setValue(0)
        self.table.clearSelection()
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.tip_label.setText(DEFAULT_TIP)

    # ------------------------------------------------------------ refresh
    def refresh(self, *_):
        self.table.clearSelection()
        sort_by = self.sort_combo.currentData()
        if self.keyword:
            self.appliances = self.service.search_appliance(self.keyword, sort_by)
        else:
            self.appliances = self.service.view_appliances(sort_by)

        rate = self.rate_input.value()
        self.table.setRowCount(len(self.appliances))
        total_kwh = total_cost = 0.0
        for row, a in enumerate(self.appliances):
            daily, monthly, cost = self._figures(a, rate)
            total_kwh += monthly
            total_cost += cost
            values = [a.id, a.name, f"{a.watts:g}", f"{a.hours:g}",
                      f"{daily:.3f}", f"{monthly:.2f}", f"₱ {cost:,.2f}"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col >= 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row, col, item)

        if not self.appliances:
            self.totals_label.setText(
                f"No appliance matches '{self.keyword}'." if self.keyword
                else "No appliances yet. Add one above."
            )
        else:
            self.totals_label.setText(
                f"{len(self.appliances)} appliance(s)  |  "
                f"Total: {total_kwh:,.2f} kWh/month  |  "
                f"Estimated bill: ₱ {total_cost:,.2f}"
            )
