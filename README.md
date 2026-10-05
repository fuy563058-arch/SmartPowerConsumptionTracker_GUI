# Smart Power Consumption Tracker

A simple desktop app that shows how much electricity each appliance uses and how much it costs per month.

---

## Project Description

The Smart Power Consumption Tracker lets a user list their appliances, enter each appliance's wattage and daily hours of use, and then see the energy used (kWh) and the estimated monthly cost. It also gives a short tip on how much money can be saved by using an appliance 2 hours less per day.

**Problem it addresses:** Many households do not know which appliances use the most electricity, so they cannot tell where their bill comes from or what to reduce.

## Project Objectives

1. Save appliances with their wattage and hours used per day.
2. Compute daily kWh, monthly kWh and monthly cost automatically.
3. Let the user search, sort, update and delete appliances.
4. Show an energy-saving suggestion for each appliance.
5. Keep all data in a database so it is still there after closing the app.

## Features

| Feature | What it does |
|---|---|
| Add Appliance | Saves a new appliance and shows its daily kWh, monthly kWh and monthly cost |
| View All | Clears any search and shows every appliance |
| Search | Finds appliances by part of the name (not case-sensitive) |
| Sort by | Orders the table by date added, name, highest/lowest monthly cost, or highest wattage |
| Update Appliance | Edits the selected appliance |
| Delete Appliance | Removes the selected appliance after asking for confirmation |
| Cost calculation | Daily kWh, monthly kWh and monthly cost for each appliance, plus totals |
| Energy suggestion | Shows how much is saved if the selected appliance is used 2 hours less per day |
| Electricity rate | The price per kWh can be changed and is remembered the next time the app opens |

**Formulas used**
- Daily kWh = (watts × hours) ÷ 1000
- Monthly kWh = daily kWh × 30
- Monthly cost = monthly kWh × rate per kWh

## Technologies Used

| Item | Used |
|---|---|
| Programming language | Python 3.10 or newer |
| GUI framework | PyQt6 |
| Database | SQLite (built into Python, `sqlite3` module) |
| Other tools | `unittest` (testing), `dataclasses`, `contextlib` (all built into Python) |

## Project Structure

```
Smart_Power_Tracker/
├── main.py                     # Starts the application
├── style.qss                   # Colors and look of the window
├── requirements.txt            # Dependencies (PyQt6)
├── power.db                    # SQLite database (created automatically on first run)
├── database/
│   └── database.py             # Database class: connection, tables, saved settings
├── features/
│   └── Appliances/
│       ├── model.py            # Appliance class (data + validation)
│       ├── repository.py       # ApplianceRepository: all SQL queries
│       ├── service.py          # ApplianceService: calculations, search, sort
│       └── view.py             # ApplianceView: the PyQt window
├── tests/
│   └── test_service.py         # Automated tests for the database and logic
└── screenshots/                # Images used in this README
```

The code is split into layers. Each layer only talks to the next one:

**View (window) → Service (logic) → Repository (SQL) → Database (SQLite file)**

## Installation and Setup

1. **Install Python 3.10 or newer** from https://www.python.org (tick "Add Python to PATH" on Windows).
2. **Download the project** and open a terminal inside the `Smart_Power_Tracker` folder:
   ```
   git clone <your-repository-link>
   cd Smart_Power_Tracker
   ```
3. **(Optional) create a virtual environment:**
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```
4. **Install the dependency:**
   ```
   pip install -r requirements.txt
   ```
5. **Run the app:**
   ```
   python main.py
   ```
   The file `power.db` is created automatically the first time the app runs.

## How to Use the System

1. **Add an appliance:** type the name, set the wattage and hours used per day, then click **Add Appliance**. A message shows its daily kWh, monthly kWh and monthly cost.
2. **Set the electricity rate:** change the "Electricity rate" box (default ₱12.00 per kWh). Costs update right away.
3. **View all appliances:** click **View All** to show the full list.
4. **Search:** type part of a name in the search box and click **Search** (or press Enter).
5. **Sort:** choose an option in the **Sort by** box.
6. **See an energy tip:** click a row in the table. The green panel at the bottom shows the suggestion.
7. **Update:** click a row, change the values in the form, then click **Update Appliance**.
8. **Delete:** click a row, click **Delete Appliance**, then confirm with Yes.
9. **Clear:** click **Clear** to empty the form.

## OOP Implementation

| Class | Purpose |
|---|---|
| `Appliance` (`model.py`) | A `@dataclass` that holds name, watts, hours and id, and checks its own values |
| `Database` (`database.py`) | Opens connections, creates tables, saves settings |
| `ApplianceRepository` (`repository.py`) | Runs all SQL for the `appliances` table |
| `ApplianceService` (`service.py`) | Calculations, search, sorting, energy tip, electricity rate |
| `ApplianceView` (`view.py`) | The window and its buttons, fields and table |

**Objects:** `main.py` creates a `Database`, passes it to an `ApplianceService`, and passes that service to an `ApplianceView`. Each `Appliance` row is an object created from the form or from the database.

**Encapsulation:** each class keeps its own job and details inside it.
- `Appliance` cleans and validates its own data in `__post_init__`.
- Only `ApplianceRepository` contains SQL.
- The view calls service methods and never touches the database directly.

**Inheritance:** `ApplianceView` inherits from PyQt's `QWidget`, so it gets all the window behavior and calls `super().__init__()`.

**Polymorphism:** the entries in `SORT_OPTIONS` (in `service.py`) are different functions, but `sorted()` calls every one of them in the same way. PyQt widgets are also used through the same methods (for example `setEnabled`). The project does not define its own class hierarchy, so polymorphism here is limited.

## Database

The app uses SQLite. The file `power.db` is created automatically.

**Table `appliances`**

| Column | Type | Rule |
|---|---|---|
| id | INTEGER | Primary key, auto-increment |
| name | TEXT | Required |
| watts | REAL | Required, must be greater than 0 |
| hours | REAL | Required, greater than 0 and at most 24 |

**Table `settings`** stores the electricity rate.

| Column | Type | Rule |
|---|---|---|
| key | TEXT | Primary key (for example `rate_per_kwh`) |
| value | TEXT | Required |

**Database operations**

| Operation | SQL | Method |
|---|---|---|
| Create | `INSERT INTO appliances (name, watts, hours) VALUES (?, ?, ?)` | `ApplianceRepository.add` |
| Read | `SELECT id, name, watts, hours FROM appliances` | `ApplianceRepository.list_all` |
| Search | `... WHERE name LIKE ?` | `ApplianceRepository.search` |
| Update | `UPDATE appliances SET name=?, watts=?, hours=? WHERE id=?` | `ApplianceRepository.update` |
| Delete | `DELETE FROM appliances WHERE id=?` | `ApplianceRepository.delete` |
| Save rate | `INSERT ... ON CONFLICT DO UPDATE` on `settings` | `Database.set_setting` |

Notes:
- Queries use `?` placeholders so user input cannot break the SQL.
- Each database action is wrapped in `with connection:`, which saves on success and undoes the change if an error happens.
- Kilowatt-hours, cost and sort order are calculated in Python and are not stored, so they never go out of date when the rate changes.
- If `power.db` is corrupted, the app renames it to `power.db.corrupt-<time>` and creates a new one.

## Screenshots

> Screenshots are stored in the `screenshots/` folder.

**1. Main window** – the form, buttons, search and sort row, table and tip panel.



**2. Adding an appliance** – the message shown after clicking Add Appliance, with daily kWh, monthly kWh and monthly cost.



**3. Search and sort** – the table filtered by a search keyword and sorted by highest monthly cost.



**4. Selected appliance and energy tip** – a selected row loaded into the form, with the energy-saving tip at the bottom.



**5. Database** – the `appliances` table inside `power.db`, showing the data is saved.



## Testing

**Automated tests** check the database and logic layers (no window needed). Run them with:

```
python -m unittest -v
```

| Test | Expected result | Actual result |
|---|---|---|
| Add three appliances, then view | All three are listed in the order added | Passed |
| 1200 W for 8 h at ₱12/kWh | 9.6 kWh/day, 288 kWh/month, ₱3,456 | Passed |
| Search "air" / search "zzz" | One match (Air Conditioner) / no results | Passed |
| Sort by highest monthly cost | Air Conditioner, Fan, TV | Passed |
| Update hours from 8 to 6 | Saved appliance shows 6 hours | Passed |
| Delete one appliance | Only two appliances remain | Passed |
| Name "A", watts 0, hours 25 | Each is rejected with an error | Passed |
| Set rate to 15.5 | Rate is saved and read back as 15.5 | Passed |
| Energy tip for 1200 W, 8 h | Says ₱864.00 is saved per month | Passed |

**Manual tests of the window** (done by running `python main.py`):

| Test | Expected result | Actual result |
|---|---|---|
| Click Add with a valid appliance | Message shows the cost, row appears in the table | _fill in_ |
| Click Add with a one-letter name | Warning message, nothing saved | _fill in_ |
| Click Add with wattage 0 | Warning message, nothing saved | _fill in_ |
| Search "fan" then click View All | Table filters, then shows all rows again | _fill in_ |
| Change the Sort by box | Table order changes | _fill in_ |
| Select a row, change hours, click Update | Row shows the new hours and cost | _fill in_ |
| Select a row, click Delete, choose Yes | Row is removed | _fill in_ |
| Change the electricity rate | All costs change | _fill in_ |
| Close and reopen the app | Appliances and rate are still there | _fill in_ |

## Known Issues / Limitations

- Each appliance has one fixed "hours per day" value. Daily changes in usage cannot be recorded.
- A month is always counted as 30 days.
- There is only one flat electricity rate (no tiered pricing).
- Two appliances can have the same name.
- Sorting uses the **Sort by** box only, not the column headers.
- Delete cannot be undone.
- There are no charts, no CSV export and no user login.
- The automated tests cover the logic and database only. The window is tested by hand.

## Author

- **Name:** _Your Name_
- **Section:** _Your Section_
