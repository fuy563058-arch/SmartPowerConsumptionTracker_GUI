from database.database import Database
from .model import Appliance
from .repository import ApplianceRepository

DAYS_PER_MONTH = 30   # monthly = daily x 30
SAVING_HOURS = 2      # energy tip compares the cost at -2 hrs/day

# sort choices shown in the GUI: key -> (label, sort function, reverse?)
SORT_OPTIONS = {
    "id":         ("Date added",             lambda a: a.id,             False),
    "name":       ("Name (A–Z)",             lambda a: a.name.lower(),   False),
    "cost_desc":  ("Highest monthly cost",   lambda a: a.watts * a.hours, True),
    "cost_asc":   ("Lowest monthly cost",    lambda a: a.watts * a.hours, False),
    "watts_desc": ("Highest wattage",        lambda a: a.watts,          True),
}


class ApplianceService:
    def __init__(self, database: Database):
        self.database = database
        self.repository = ApplianceRepository(database)

    # ---------- appliance management (CRUD) ----------
    def add_appliance(self, appliance: Appliance) -> Appliance:
        return self.repository.add(appliance)

    def view_appliances(self, sort_by: str = "id") -> list[Appliance]:
        return self.sort_appliances(self.repository.list_all(), sort_by)

    def search_appliance(self, keyword: str, sort_by: str = "id") -> list[Appliance]:
        keyword = keyword.strip()
        if not keyword:
            return self.view_appliances(sort_by)
        return self.sort_appliances(self.repository.search(keyword), sort_by)

    @staticmethod
    def sort_appliances(appliances: list[Appliance], sort_by: str = "id") -> list[Appliance]:
        """Order a list of appliances. Monthly cost is proportional to
        watts x hours, so sorting by that is the same as sorting by cost."""
        _, key, reverse = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["id"])
        return sorted(appliances, key=key, reverse=reverse)

    def update_appliance(self, appliance: Appliance) -> Appliance:
        return self.repository.update(appliance)

    def delete_appliance(self, appliance_id: int) -> None:
        self.repository.delete(appliance_id)

    # ---------- calculations ----------
    @staticmethod
    def daily_consumption(watts: float, hours: float) -> float:
        """(W x h) / 1000  ->  daily kWh"""
        return watts * hours / 1000

    @staticmethod
    def monthly_consumption(daily_kwh: float) -> float:
        """daily kWh x 30  ->  monthly kWh"""
        return daily_kwh * DAYS_PER_MONTH

    @staticmethod
    def monthly_cost(monthly_kwh: float, rate: float) -> float:
        """monthly kWh x rate  ->  monthly cost (PHP)"""
        return monthly_kwh * rate

    @staticmethod
    def energy_suggestion(watts: float, hours: float, cost: float) -> str:
        """Compare the monthly cost now vs. using the appliance 2 hrs less per day."""
        cut = min(SAVING_HOURS, hours)
        new_hours = hours - cut
        new_cost = cost * new_hours / hours      # cost is proportional to hours
        saving = cost - new_cost
        saved_kwh = watts * cut * DAYS_PER_MONTH / 1000
        if new_hours == 0:
            return (
                f"Tip: This appliance runs only {hours:g} h/day. Switching it off "
                f"completely would save about ₱ {saving:,.2f} per month "
                f"({saved_kwh:.1f} kWh)."
            )
        return (
            f"Tip: Using it {cut:g} hours less per day ({hours:g} h → {new_hours:g} h) "
            f"lowers the monthly cost from ₱ {cost:,.2f} to ₱ {new_cost:,.2f}, "
            f"saving ₱ {saving:,.2f} ({saved_kwh:.1f} kWh) every month."
        )

    # ---------- electricity rate (remembered between runs) ----------
    def get_rate(self) -> float:
        return float(self.database.get_setting("rate_per_kwh", "12.0"))

    def set_rate(self, rate: float) -> None:
        if rate < 0:
            raise ValueError("Rate cannot be negative.")
        self.database.set_setting("rate_per_kwh", str(rate))
