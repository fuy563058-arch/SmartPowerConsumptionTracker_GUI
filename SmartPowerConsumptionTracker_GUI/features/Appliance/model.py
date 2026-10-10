from dataclasses import dataclass


@dataclass
class Appliance:
    name: str
    watts: float
    hours: float  # hours used per day
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if len(self.name) < 2:
            raise ValueError("Appliance name must have at least 2 characters.")
        try:
            self.watts = float(self.watts)
            self.hours = float(self.hours)
        except (TypeError, ValueError):
            raise ValueError("Wattage and hours must be numbers.") from None
        if self.watts <= 0:
            raise ValueError("Wattage must be greater than 0.")
        if not 0 < self.hours <= 24:
            raise ValueError("Hours per day must be between 0 and 24.")
