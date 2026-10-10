from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .appliance_table import create_table, fill_table
from .model import Appliance
from .services import OTHER_RATES, RATE_MODES, SORT_OPTIONS

DEFAULT_TIP = "Select an appliance in the table to see an energy-saving tip."


class ApplianceView(QWidget):
    def __init__(self, service):
        super().__init__()
        self.setObjectName("applianceView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # lets the .qss color the page
        self.service = service
        self.selected_id: int | None = None
        self.appliances: list[Appliance] = []   # appliances currently in the table
        self.keyword = ""                       # current search keyword ("" = show all)
        self.build_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Appliances")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # --- top row: appliance details (left) + electricity rate (right) ---
        top = QHBoxLayout()
        top.addWidget(self.build_details_box(), 3)
        top.addWidget(self.build_rate_box(), 2)
        layout.addLayout(top)

        # --- appliance list: search, table, totals, tip ---
        layout.addWidget(self.build_list_box(), 1)

    def build_details_box(self) -> QGroupBox:
        box = QGroupBox("Appliance Details")
        box_layout = QVBoxLayout(box)

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

        self.watts_input.setToolTip("Power rating of the appliance in watts (usually printed on its label).")
        self.hours_input.setToolTip("How many hours per day the appliance is used (0 to 24).")

        form.addRow("Appliance name", self.name_input)
        form.addRow("Wattage", self.watts_input)
        form.addRow("Hours used per day", self.hours_input)
        box_layout.addLayout(form)

        # --- CRUD buttons ---
        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add Appliance")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_appliance)
        self.update_button = QPushButton("Update Appliance")
        self.update_button.setObjectName("updateButton")
        self.update_button.clicked.connect(self.update_appliance)
        self.delete_button = QPushButton("Delete Appliance")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.delete_appliance)
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        for b in (self.add_button, self.update_button, self.delete_button, self.clear_button):
            buttons.addWidget(b)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        box_layout.addLayout(buttons)

        hint = QLabel("To update or delete an appliance, click it in the Appliance List below first.")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        box_layout.addWidget(hint)
        return box

    def build_rate_box(self) -> QGroupBox:
        box = QGroupBox("Electricity Rate for All Appliances")
        box_layout = QVBoxLayout(box)
        form = QFormLayout()

        # 1) dropdown: Custom / Philippines / Other
        self.rate_mode_combo = QComboBox()
        for key, label in RATE_MODES.items():
            self.rate_mode_combo.addItem(label, key)
        form.addRow("Rate type", self.rate_mode_combo)

        # 2) custom rate box: shown only for "Custom Rate"
        self.custom_label = QLabel("Custom rate")
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.0, 10000.0)
        self.rate_input.setDecimals(2)
        self.rate_input.setPrefix("₱ ")
        self.rate_input.setSuffix(" / kWh")
        form.addRow(self.custom_label, self.rate_input)

        # 3) list of extra rates: shown only for "Other Rates"
        self.other_label = QLabel("Choose rate")
        self.rate_other_combo = QComboBox()
        for name, value in OTHER_RATES.items():
            self.rate_other_combo.addItem(f"{name} (₱ {value:,.2f} / kWh)", name)
        form.addRow(self.other_label, self.rate_other_combo)
        box_layout.addLayout(form)

        # The new rate is used only after "Apply Rate" is clicked.
        apply_row = QHBoxLayout()
        self.rate_pending_label = QLabel()
        self.rate_pending_label.setObjectName("pendingLabel")
        self.rate_pending_label.setWordWrap(True)
        self.rate_pending_label.setFixedHeight(self.rate_pending_label.fontMetrics().lineSpacing() * 2)
        self.apply_rate_button = QPushButton("Apply Rate")
        self.apply_rate_button.setObjectName("applyButton")
        self.apply_rate_button.clicked.connect(self.apply_rate)
        apply_row.addWidget(self.rate_pending_label, 1)
        apply_row.addWidget(self.apply_rate_button)
        box_layout.addLayout(apply_row)

        # The custom / other rows are hidden when not used. Keep their space when hidden
        # so the box never changes size when the rate type is changed.
        for widget in (self.custom_label, self.rate_input,
                       self.other_label, self.rate_other_combo):
            policy = widget.sizePolicy()
            policy.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(policy)

        self.rate_note = QLabel()
        self.rate_note.setWordWrap(True)
        self.rate_note.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.rate_note.setFixedHeight(self.rate_note.fontMetrics().lineSpacing() * 3)  # room for 3 lines
        box_layout.addWidget(self.rate_note)
        box_layout.addStretch(1)

        # show the saved choice first, then start listening for changes
        self.rate_mode_combo.setCurrentIndex(
            self.rate_mode_combo.findData(self.service.get_rate_mode())
        )
        self.rate_input.setValue(self.service.get_custom_rate())
        self.rate_other_combo.setCurrentIndex(
            self.rate_other_combo.findData(self.service.get_other_name())
        )
        # changing the choice only marks it as "not applied yet"; Apply Rate saves it
        self.rate_mode_combo.currentIndexChanged.connect(self.update_rate_widgets)
        self.rate_input.valueChanged.connect(self.update_rate_widgets)
        self.rate_other_combo.currentIndexChanged.connect(self.update_rate_widgets)
        self.update_rate_widgets()
        return box

    def build_list_box(self) -> QGroupBox:
        box = QGroupBox("Appliance List")
        box_layout = QVBoxLayout(box)

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
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.show_all_button)
        search_row.addWidget(QLabel("Sort by"))
        search_row.addWidget(self.sort_combo)
        box_layout.addLayout(search_row)

        # --- table ---
        self.table = create_table()
        self.table.itemSelectionChanged.connect(self.load_selected)
        box_layout.addWidget(self.table)

        # --- totals + energy suggestion ---
        self.totals_label = QLabel()
        self.totals_label.setObjectName("totalsLabel")
        box_layout.addWidget(self.totals_label)

        self.tip_label = QLabel(DEFAULT_TIP)
        self.tip_label.setObjectName("tipPanel")
        self.tip_label.setWordWrap(True)
        box_layout.addWidget(self.tip_label)
        return box

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
        rate = self.service.get_rate()
        daily, monthly, cost = self._figures(appliance, rate)
        QMessageBox.information(
            self,
            "Appliance Added",
            f"{appliance.name} was added.\n\n"
            f"Daily use: {daily:.3f} kWh\n"
            f"Monthly use: {monthly:.2f} kWh\n"
            f"Estimated daily cost: ₱ {self.service.daily_cost(daily, rate):,.2f}\n"
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

    # ---------------------------------------------- electricity rate changes
    def _selected_rate(self) -> float:
        """The rate currently chosen in the dropdown (not necessarily applied yet)."""
        mode = self.rate_mode_combo.currentData()
        if mode == "ph":
            return self.service.get_ph_rate()
        if mode == "other":
            return OTHER_RATES[self.rate_other_combo.currentData()]
        return self.rate_input.value()

    def rate_is_pending(self) -> bool:
        """True when the dropdown shows a choice that has not been applied yet."""
        mode = self.rate_mode_combo.currentData()
        if mode != self.service.get_rate_mode():
            return True
        if mode == "custom":
            return abs(self.rate_input.value() - self.service.get_custom_rate()) > 1e-9
        if mode == "other":
            return self.rate_other_combo.currentData() != self.service.get_other_name()
        return False

    def update_rate_widgets(self, *_):
        """Show only the input that belongs to the chosen rate type and the Apply state."""
        mode = self.rate_mode_combo.currentData()
        self.custom_label.setVisible(mode == "custom")
        self.rate_input.setVisible(mode == "custom")
        self.other_label.setVisible(mode == "other")
        self.rate_other_combo.setVisible(mode == "other")
        self.rate_note.setText(f"Used for all appliances: {self.service.describe_rate()}")
        pending = self.rate_is_pending()
        self.apply_rate_button.setEnabled(pending)
        self.rate_pending_label.setText(
            f"Not applied yet: ₱ {self._selected_rate():,.2f} / kWh" if pending else ""
        )

    def apply_rate(self):
        """Save the chosen rate and recalculate everything with it."""
        mode = self.rate_mode_combo.currentData()
        try:
            if mode == "custom":
                self.service.set_rate(self.rate_input.value())
            elif mode == "other":
                self.service.set_other_name(self.rate_other_combo.currentData())
            self.service.set_rate_mode(mode)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Rate", str(error))
            return
        self.rate_changed()

    def rate_changed(self):
        """Recalculate every cost in the table (and the tip) with the new rate."""
        self.update_rate_widgets()
        selected = self.selected_id
        self.refresh()
        if selected is not None:               # keep the selected appliance selected
            for row, a in enumerate(self.appliances):
                if a.id == selected:
                    self.table.selectRow(row)
                    break

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
        _, _, cost = self._figures(appliance, self.service.get_rate())
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
        self.refresh()

    # ------------------------------------------------------------ refresh
    def refresh(self, *_):
        self.table.clearSelection()
        sort_by = self.sort_combo.currentData()
        if self.keyword:
            self.appliances = self.service.search_appliance(self.keyword, sort_by)
        else:
            self.appliances = self.service.view_appliances(sort_by)

        total_kwh, total_cost = fill_table(
            self.table, self.appliances, self.service, self.service.get_rate()
        )

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