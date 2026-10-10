"""The appliance table, shared by the Dashboard and the Appliance page so both
always show the same columns and the same numbers."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem,
)

HEADERS = [
    "ID", "Appliance", "Watts (W)", "Hours/day",
    "Daily kWh", "Monthly kWh", "Daily Cost", "Monthly Cost", "% of Bill",
]


def create_table(selectable: bool = True) -> QTableWidget:
    table = QTableWidget(0, len(HEADERS))
    table.setHorizontalHeaderLabels(HEADERS)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    if selectable:
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    else:
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    return table


def table_rows(appliances, service, rate: float):
    """Build the text of every table row (same numbers for the table and the CSV export).
    Returns (rows, total monthly kWh, total monthly cost)."""
    figures = []
    for a in appliances:
        daily_kwh = service.daily_consumption(a.watts, a.hours)
        monthly_kwh = service.monthly_consumption(daily_kwh)
        figures.append((
            daily_kwh, monthly_kwh,
            service.daily_cost(daily_kwh, rate), service.monthly_cost(monthly_kwh, rate),
        ))
    total_kwh = sum(f[1] for f in figures)
    total_cost = sum(f[3] for f in figures)
    rows = []
    for a, (daily_kwh, monthly_kwh, daily_cost, monthly_cost) in zip(appliances, figures):
        share = monthly_kwh / total_kwh if total_kwh else 0.0   # cost share = energy share
        rows.append([
            str(a.id), a.name, f"{a.watts:g}", f"{a.hours:g}",
            f"{daily_kwh:.3f}", f"{monthly_kwh:.2f}",
            f"₱ {daily_cost:,.2f}", f"₱ {monthly_cost:,.2f}", f"{share:.1%}",
        ])
    return rows, total_kwh, total_cost


def fill_table(table: QTableWidget, appliances, service, rate: float) -> tuple[float, float]:
    """Show the appliances using the given rate (PHP per kWh).
    Returns (total monthly kWh, total monthly cost)."""
    rows, total_kwh, total_cost = table_rows(appliances, service, rate)
    table.setRowCount(len(rows))
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col >= 2:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, col, item)
    return total_kwh, total_cost