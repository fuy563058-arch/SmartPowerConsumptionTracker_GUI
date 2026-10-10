from SmartPowerConsumptionTracker_GUI.database.database import Database
from .model import Appliance
from .repository import ApplianceRepository

DAYS_PER_MONTH = 30   # monthly = daily x 30
SAVING_HOURS = 2      # energy tip compares the cost at -2 hrs/day

# ---- electricity rate options (PHP per kWh) ----
PH_RATE = 12.0        # default "Philippines (PH) Rate": change this number to update the default
RATE_MODES = {        # choices shown in the "Electricity Rate for All Appliances" dropdown
    "custom": "Custom Rate",
    "ph": "Philippines (PH) Rate",
    "other": "Other Rates",
}
OTHER_RATES = {       # extra choices for "Other Rates": add or edit lines as needed
    "Low rate": 10.0,
    "Standard rate": 12.0,
    "High rate": 14.0,
}

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
    def daily_cost(daily_kwh: float, rate: float) -> float:
        """daily kWh x rate  ->  daily cost (PHP)"""
        return daily_kwh * rate

    @staticmethod
    def monthly_cost(monthly_kwh: float, rate: float) -> float:
        """monthly kWh x rate  ->  monthly cost (PHP)"""
        return monthly_kwh * rate

    @staticmethod
    def overall_totals(appliances: list[Appliance], rate: float) -> dict:
        """Add up all appliances: watts, hours/day, daily & monthly kWh, daily & monthly cost."""
        daily_kwh = sum(
            ApplianceService.daily_consumption(a.watts, a.hours) for a in appliances
        )
        monthly_kwh = ApplianceService.monthly_consumption(daily_kwh)
        return {
            "watts": sum(a.watts for a in appliances),
            "hours": sum(a.hours for a in appliances),
            "daily_kwh": daily_kwh,
            "monthly_kwh": monthly_kwh,
            "daily_cost": ApplianceService.daily_cost(daily_kwh, rate),
            "monthly_cost": ApplianceService.monthly_cost(monthly_kwh, rate),
        }

    @staticmethod
    def total_saving(appliances: list[Appliance], rate: float) -> float:
        """Monthly saving (PHP) if every appliance is used SAVING_HOURS less per day."""
        return sum(
            a.watts * min(SAVING_HOURS, a.hours) * DAYS_PER_MONTH / 1000 * rate
            for a in appliances
        )

    @staticmethod
    def overall_suggestion(appliances: list[Appliance], rate: float) -> str:
        """Short summary + saving advice for ALL appliances (shown by the Overall Suggestion button)."""
        if not appliances:
            return "No appliances yet. Add one in the Appliances tab."
        totals = ApplianceService.overall_totals(appliances, rate)
        top = max(appliances, key=lambda a: a.watts * a.hours)       # cost is proportional to W x h
        top_kwh = ApplianceService.monthly_consumption(
            ApplianceService.daily_consumption(top.watts, top.hours)
        )
        share = top_kwh / totals["monthly_kwh"] if totals["monthly_kwh"] else 0.0

        def cut_hours(a):
            return min(SAVING_HOURS, a.hours)

        def saved_kwh(a):
            return a.watts * cut_hours(a) * DAYS_PER_MONTH / 1000

        best = max(appliances, key=saved_kwh)
        all_kwh = sum(saved_kwh(a) for a in appliances)
        return "\n".join([
            f"Overall: {len(appliances)} appliance(s) use {totals['monthly_kwh']:,.2f} kWh per month, "
            f"about ₱ {totals['monthly_cost']:,.2f}.",
            f"Highest consumer: {top.name} ({share:.1%} of the bill, "
            f"₱ {ApplianceService.monthly_cost(top_kwh, rate):,.2f} per month).",
            f"Biggest saving: using {best.name} {cut_hours(best):g} h less per day saves "
            f"₱ {saved_kwh(best) * rate:,.2f} per month.",
            f"Tip: using every appliance {SAVING_HOURS:g} h less per day would save about "
            f"₱ {all_kwh * rate:,.2f} ({all_kwh:.1f} kWh) every month.",
        ])

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

    # ---------- electricity rate for ALL appliances (remembered between runs) ----------
    # The selected rate is saved in the settings table:
    #   rate_mode   -> "custom", "ph" or "other"
    #   rate_per_kwh-> the custom rate (same key older versions used)
    #   rate_other  -> name of the chosen entry in OTHER_RATES
    def get_rate_mode(self) -> str:
        mode = self.database.get_setting("rate_mode", "")
        if mode in RATE_MODES:
            return mode
        # data saved by an older version only has "rate_per_kwh": keep using it as the custom rate
        has_old_rate = self.database.get_setting("rate_per_kwh", "") != ""
        return "custom" if has_old_rate else "ph"

    def set_rate_mode(self, mode: str) -> None:
        if mode not in RATE_MODES:
            raise ValueError(f"Unknown rate option: {mode}")
        self.database.set_setting("rate_mode", mode)

    def get_custom_rate(self) -> float:
        return float(self.database.get_setting("rate_per_kwh", str(self.get_ph_rate())))

    def set_rate(self, rate: float) -> None:
        """Save the custom rate typed by the user."""
        if rate < 0:
            raise ValueError("Rate cannot be negative.")
        self.database.set_setting("rate_per_kwh", str(rate))

    def get_ph_rate(self) -> float:
        # default comes from PH_RATE above; a "rate_ph" setting can override it
        return float(self.database.get_setting("rate_ph", str(PH_RATE)))

    def get_other_name(self) -> str:
        name = self.database.get_setting("rate_other", "")
        return name if name in OTHER_RATES else next(iter(OTHER_RATES))

    def set_other_name(self, name: str) -> None:
        if name not in OTHER_RATES:
            raise ValueError(f"Unknown rate: {name}")
        self.database.set_setting("rate_other", name)

    def get_rate(self) -> float:
        """The rate (PHP per kWh) that applies to every appliance right now."""
        mode = self.get_rate_mode()
        if mode == "ph":
            return self.get_ph_rate()
        if mode == "other":
            return OTHER_RATES[self.get_other_name()]
        return self.get_custom_rate()

    def describe_rate(self) -> str:
        """Short text such as 'Philippines (PH) Rate: ₱ 12.00 / kWh'."""
        mode = self.get_rate_mode()
        label = RATE_MODES[mode]
        if mode == "other":
            label = f"{label} - {self.get_other_name()}"
        return f"{label}: ₱ {self.get_rate():,.2f} / kWh"