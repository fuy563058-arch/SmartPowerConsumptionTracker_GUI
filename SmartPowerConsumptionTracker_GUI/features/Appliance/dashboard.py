from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from .appliance_table import create_table, fill_table
from .services import SORT_OPTIONS

DEFAULT_HINT = ("Click a row to see an energy-saving tip for that appliance, "
                "or press \"Overall Suggestion\" for all appliances.")


class DashboardView(QWidget):
    """Overview: overall totals, the appliance table and an energy tip.
    The electricity rate is changed on the Appliances page; call refresh()
    to show the latest data and rate."""

    def __init__(self, service):
        super().__init__()
        self.setObjectName("dashboardView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # lets the .qss color the page
        self.service = service
        self.appliances = []          # appliances currently in the table
        self.rate = service.get_rate()
        self.overall_mode = False     # True after "Overall Suggestion" is pressed
        self.build_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.rate_label = QLabel()
        layout.addWidget(self.rate_label)
        note = QLabel("Monthly figures = daily figures × 30 days.")
        note.setObjectName("hintLabel")
        layout.addWidget(note)

        # --- overall totals box ---
        self.totals_box = QGroupBox("Overall Totals")
        grid = QGridLayout(self.totals_box)
        self.total_values = {}
        tiles = [   # key, caption, style name (colors are set in style.qss)
            ("watts", "Total wattage", "valPower"),
            ("hours", "Total hours/day", "valPower"),
            ("daily_kwh", "Daily kWh", "valEnergy"),
            ("monthly_kwh", "Monthly kWh", "valEnergy"),
            ("daily_cost", "Daily cost", "valCost"),
            ("monthly_cost", "Monthly cost", "valCost"),
        ]
        for col, (key, caption, style) in enumerate(tiles):
            caption_label = QLabel(caption)
            caption_label.setObjectName("totalCaption")
            value_label = QLabel("–")
            if key == "hours":
                tip = "All appliances' hours added together, so it can be more than 24."
                caption_label.setToolTip(tip)
                value_label.setToolTip(tip)
            value_label.setObjectName(style)
            grid.addWidget(caption_label, 0, col)
            grid.addWidget(value_label, 1, col)
            grid.setColumnStretch(col, 1)
            self.total_values[key] = value_label
        layout.addWidget(self.totals_box)

        # --- table ---
        title_row = QHBoxLayout()
        table_title = QLabel("Appliance list")
        table_title.setObjectName("sectionLabel")
        self.sort_combo = QComboBox()
        for key, (label, _, _) in SORT_OPTIONS.items():
            self.sort_combo.addItem(label, key)
        self.sort_combo.setCurrentIndex(self.sort_combo.findData("cost_desc"))  # biggest cost first
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        title_row.addWidget(table_title, 1)
        title_row.addWidget(QLabel("Sort by"))
        title_row.addWidget(self.sort_combo)
        layout.addLayout(title_row)
        self.table = create_table()
        self.table.itemSelectionChanged.connect(self.show_tip)
        layout.addWidget(self.table, 1)

        # --- overall suggestion button (below the table) ---
        button_row = QHBoxLayout()
        self.overall_button = QPushButton("Overall Suggestion")
        self.overall_button.setObjectName("suggestButton")
        self.overall_button.setToolTip("Show a summary and saving advice for all appliances.")
        self.overall_button.clicked.connect(self.show_overall)
        button_row.addWidget(self.overall_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        # --- energy tip (below the table) ---
        self.tip_label = QLabel()
        self.tip_label.setObjectName("tipPanel")
        self.tip_label.setWordWrap(True)
        layout.addWidget(self.tip_label)

    # ------------------------------------------------------------ helpers
    def _tip_for(self, appliance) -> str:
        daily = self.service.daily_consumption(appliance.watts, appliance.hours)
        cost = self.service.monthly_cost(self.service.monthly_consumption(daily), self.rate)
        return self.service.energy_suggestion(appliance.watts, appliance.hours, cost)

    def show_overall(self):
        """Overall Suggestion button: tip for all appliances together."""
        self.overall_mode = True
        self.table.clearSelection()
        self.show_tip()

    def show_tip(self):
        if not self.appliances:
            self.tip_label.setText("No appliances yet. Add one in the Appliances tab.")
            return
        rows = self.table.selectionModel().selectedRows()
        if rows and rows[0].row() < len(self.appliances):
            self.overall_mode = False
            a = self.appliances[rows[0].row()]
            self.tip_label.setText(f"{a.name}\n{self._tip_for(a)}")
        elif self.overall_mode:
            self.tip_label.setText(self.service.overall_suggestion(self.appliances, self.rate))
        else:
            self.tip_label.setText(DEFAULT_HINT)

    # ------------------------------------------------------------ refresh
    def refresh(self, *_):
        self.rate = self.service.get_rate()
        self.table.clearSelection()
        self.appliances = self.service.view_appliances(self.sort_combo.currentData())
        fill_table(self.table, self.appliances, self.service, self.rate)

        self.rate_label.setText(
            f"Electricity rate for all appliances: {self.service.describe_rate()}   (change it in the Appliances tab)"
        )
        totals = self.service.overall_totals(self.appliances, self.rate)
        self.totals_box.setTitle(f"Overall Totals - all {len(self.appliances)} appliance(s) combined")
        text = {
            "watts": f"{totals['watts']:,.0f} W",
            "hours": f"{totals['hours']:g} h",
            "daily_kwh": f"{totals['daily_kwh']:,.3f} kWh",
            "monthly_kwh": f"{totals['monthly_kwh']:,.2f} kWh",
            "daily_cost": f"₱ {totals['daily_cost']:,.2f}",
            "monthly_cost": f"₱ {totals['monthly_cost']:,.2f}",
        }
        for key, label in self.total_values.items():
            label.setText(text[key])
        self.show_tip()