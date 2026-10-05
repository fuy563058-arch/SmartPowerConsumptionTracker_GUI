from database.database import Database
from .model import Appliance


def _to_appliance(row) -> Appliance:
    return Appliance(id=row[0], name=row[1], watts=row[2], hours=row[3])


class ApplianceRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, appliance: Appliance) -> Appliance:
        with self.database.connect() as c:
            cur = c.execute(
                "INSERT INTO appliances (name, watts, hours) VALUES (?, ?, ?)",
                (appliance.name, appliance.watts, appliance.hours),
            )
            appliance.id = cur.lastrowid
        return appliance

    def list_all(self) -> list[Appliance]:
        with self.database.connect() as c:
            rows = c.execute(
                "SELECT id, name, watts, hours FROM appliances ORDER BY id"
            ).fetchall()
        return [_to_appliance(r) for r in rows]

    def search(self, keyword: str) -> list[Appliance]:
        # escape LIKE wildcards so a keyword such as "50%" is matched literally
        escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self.database.connect() as c:
            rows = c.execute(
                "SELECT id, name, watts, hours FROM appliances "
                "WHERE name LIKE ? ESCAPE '\\' ORDER BY id",
                (f"%{escaped}%",),
            ).fetchall()
        return [_to_appliance(r) for r in rows]

    def update(self, appliance: Appliance) -> Appliance:
        if appliance.id is None:
            raise ValueError("Cannot update an appliance without an id.")
        with self.database.connect() as c:
            cur = c.execute(
                "UPDATE appliances SET name = ?, watts = ?, hours = ? WHERE id = ?",
                (appliance.name, appliance.watts, appliance.hours, appliance.id),
            )
        if cur.rowcount == 0:
            raise ValueError(f"No appliance found with id {appliance.id}.")
        return appliance

    def delete(self, appliance_id: int) -> None:
        with self.database.connect() as c:
            cur = c.execute("DELETE FROM appliances WHERE id = ?", (appliance_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No appliance found with id {appliance_id}.")
