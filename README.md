# Smart Power Consumption Tracker

A small desktop app that shows you which of your appliances is quietly eating your electric bill.

---

## 1. Project Description

Most of us have no idea how much a single appliance adds to our monthly bill. We only see one big number when the bill arrives, and by then it's too late to do anything about it.

The Smart Power Consumption Tracker fixes that. You type in each appliance, how many watts it uses, and how many hours a day you run it. The app then works out how much electricity it uses per day and per month, and how much that costs you in pesos. It also gives you simple tips on how to save.

Everything is saved on your computer, so your appliances are still there the next time you open the app.

## 2. Project Objectives

What we wanted this project to do:

- Let a user **add, view, search, update and delete** appliances (full CRUD).
- **Calculate** daily and monthly energy use (kWh) and cost (₱) for each appliance and for all appliances together.
- Let the user choose the **electricity rate** that applies to every appliance, and recalculate everything when it changes.
- Give **energy-saving suggestions** in plain language.
- **Save data** so nothing is lost when the app closes.
- Practice clean, layered code using **object-oriented programming**.

## 3. Features

| Feature | What it does |
|---|---|
| **Add / Update / Delete** | Manage appliances with a simple form. Bad input (like 0 watts or 30 hours a day) is rejected with a clear message. |
| **Search and sort** | Find an appliance by name. Sort by date added, name, highest or lowest cost, or highest wattage. |
| **Daily and monthly figures** | Daily kWh, monthly kWh, daily cost, monthly cost and each appliance's share (%) of the bill. |
| **Electricity Rate for All Appliances** | Pick *Custom Rate*, *Philippines (PH) Rate* or *Other Rates*. Click **Apply Rate** and every cost updates. |
| **Dashboard** | Overall totals (wattage, hours, kWh, cost), the full appliance table and a sort option. |
| **Energy tips** | Click an appliance to see how much you'd save by using it 2 hours less per day. The **Overall Suggestion** button gives advice for all appliances together. |
| **Saved settings** | The chosen rate is remembered between runs. |

## 4. Technologies Used

- **Language:** Python 3
- **GUI framework:** PyQt6
- **Database:** SQLite (through Python's built-in `sqlite3`)
- **Styling:** Qt style sheet (`style.qss`)
- No other libraries are needed.

## 5. Project Structure

```
SmartPowerTracker_GUI/
├── main.py                      # Starts the app: opens the database, loads the style, shows the window
├── style.qss                    # Colors and look of the app
├── database/
│   ├── database.py              # Connects to SQLite, creates the tables, saves settings
│   └── power.db                 # The database file (created automatically)
└── features/
    └── Appliance/
        ├── model.py             # The Appliance class and its validation rules
        ├── repository.py        # All the SQL for appliances (add, list, search, update, delete)
        ├── services.py          # The calculations, the rate options and the energy tips
        ├── appliance_table.py   # The table shared by the Dashboard and the Appliances page
        ├── view.py              # The Appliances page (form, rate box, list)
        └── dashboard.py         # The Dashboard page (totals, table, suggestions)
```

The code is split into layers so each file has one job:

**View → Service → Repository → Database**

The screens only talk to the service. The service does the thinking. The repository is the only place that writes SQL.

## 6. Installation and Setup

1. Install **Python 3.10 or newer** (the code uses the `int | None` type style).
2. Install PyQt6:
   ```
   pip install PyQt6
   ```
3. Open a terminal in the folder that **contains** `SmartPowerTracker_GUI` and run:
   ```
   python -m SmartPowerTracker_GUI.main
   ```
4. The database file is created automatically on the first run. You don't need to set anything up.

## 7. How to Use the System

1. Open the **Appliances** tab.
2. Under **Appliance Details**, type the name, wattage and hours used per day, then click **Add Appliance**.
3. Under **Electricity Rate for All Appliances**, choose a rate type. If you pick *Custom Rate*, type your rate per kWh. Then click **Apply Rate**. Nothing changes until you click it.
4. To change or remove an appliance, click it in the **Appliance List**, then use **Update Appliance** or **Delete Appliance**. Use **Clear Form** to start over.
5. To find something, type in the search box, or use **Sort by**. **View All** brings back the full list.
6. Open the **Dashboard** tab to see the overall totals. Click a row for a tip about that appliance, or press **Overall Suggestion** for advice about everything.

## 8. OOP Implementation

**Important classes**

| Class | Role |
|---|---|
| `Appliance` (model.py) | One appliance: name, watts, hours and id |
| `Database` (database.py) | Opens connections, creates tables, stores settings |
| `ApplianceRepository` (repository.py) | Talks to the `appliances` table |
| `ApplianceService` (services.py) | Calculations, rate options, tips |
| `ApplianceView` (view.py) | The Appliances page |
| `DashboardView` (dashboard.py) | The Dashboard page |

**Encapsulation:** each class keeps its own job to itself. `Appliance` checks its own data when it is created, so an appliance with 0 watts can never exist. Only `ApplianceRepository` writes SQL. Only `ApplianceService` knows the formulas and the rate rules. The screens never touch the database directly.

**Inheritance:** `ApplianceView` and `DashboardView` both inherit from PyQt's `QWidget`, so they get all the window and layout behavior for free.

**Polymorphism:** this is used only lightly. Both pages are `QWidget`s, so the tab widget can show either one without knowing which is which. We did not write our own overridden methods, so we don't want to overstate it.

## 9. Database

The app uses one SQLite file, `power.db`, with two tables.

**`appliances`**

| Column | Type | Rule |
|---|---|---|
| `id` | INTEGER | Primary key, automatic |
| `name` | TEXT | Required |
| `watts` | REAL | Required, must be greater than 0 |
| `hours` | REAL | Required, greater than 0 and at most 24 |

**`settings`** is a small key/value table for the chosen electricity rate (`rate_mode`, `rate_per_kwh`, `rate_other`, optionally `rate_ph`).

**How each operation works** (all in `repository.py`)

| Operation | What happens |
|---|---|
| **Create** | `INSERT INTO appliances ...` when you click Add Appliance |
| **Read** | `SELECT ... FROM appliances ORDER BY id`, then the service sorts the list |
| **Update** | `UPDATE appliances SET ... WHERE id = ?` |
| **Delete** | `DELETE FROM appliances WHERE id = ?` (after a confirmation question) |
| **Search** | `WHERE name LIKE ?`. Characters like `%` and `_` are escaped, so searching "50%" really looks for "50%" |

If the database file is ever corrupted, the app moves it aside as a backup and creates a fresh one instead of crashing.

## 10. Screenshots

> Replace the image paths below with your own screenshots.

| Screenshot | What it shows |
|---|---|
| <img width="1363" height="719" alt="Image" src="https://github.com/user-attachments/assets/874377c3-8191-41ea-9c16-bc0b7984ec24" /> | The Dashboard with the overall totals, the table and the suggestion box |
| <img width="1357" height="686" alt="Image" src="https://github.com/user-attachments/assets/0fd51156-cba0-4b6d-ba86-ebeafccf0fe2" /> | The Appliances page with the form, the rate box and the list |
| <img width="655" height="350" alt="Image" src="https://github.com/user-attachments/assets/4a8e8f10-4910-4bcb-ae54-213e49cab664" />| Adding a new appliance |
| <img width="526" height="229" alt="Image" src="https://github.com/user-attachments/assets/1fdffa15-a2c9-49e2-8e1b-59ec9bc837fa" /> | Choosing a rate and the "Not applied yet" note before clicking Apply Rate |
| <img width="731" height="229" alt="Screenshot 2026-10-10 225906" src="https://github.com/user-attachments/assets/77275caf-0f47-4d3e-8429-a9d7b9bd01d4" /> | The error message when the input is not valid |

## 11. Testing

**Calculations.** Test appliance: Laptop, 200 W, 8 hours a day. The formulas are: daily kWh = (W × hours) ÷ 1000, monthly = daily × 30, cost = kWh × rate.

| Test | Expected | Actual | Result |
|---|---|---|---|
| PH rate (₱ 12.00) | 1.600 kWh/day, 48.00 kWh/month, ₱ 19.20/day, ₱ 576.00/month | Same | Pass |
| Custom rate ₱ 15.00 | ₱ 24.00/day, ₱ 720.00/month | Same | Pass |
| Other rate "High rate" (₱ 14.00) | ₱ 22.40/day, ₱ 672.00/month | Same | Pass |
| Energy tip for the laptop at ₱ 12.00 | 8 h → 6 h, saves ₱ 144.00 (12.0 kWh) a month | Same | Pass |
| Energy tip for a 1-hour appliance | Says it can only be switched off completely | "Switching it off completely would save about ₱ 360.00 per month" (1000 W) | Pass |

**Input validation.**

| Input | Expected | Actual | Result |
|---|---|---|---|
| Name with 1 character | Rejected | "Appliance name must have at least 2 characters." | Pass |
| Wattage 0 | Rejected | "Wattage must be greater than 0." | Pass |
| Hours 0 | Rejected | "Hours per day must be between 0 and 24." | Pass |
| Hours 25 | Rejected | "Hours per day must be between 0 and 24." | Pass |
| Wattage typed as text | Rejected | "Wattage and hours must be numbers." | Pass |

**Rate behavior.** In a test run with the sample data, the saved rate stayed the same until Apply Rate was clicked. After that, the table and totals changed, and the new rate was still there when the app was started again. A rate saved by an older version of the app was kept as the Custom Rate.

> The results above come from running the app's own model and service code. Please also do a quick manual run through each screen and add your own notes here.

## 12. Known Issues / Limitations

- **No history.** The app only stores the current list of appliances. It can't show how your usage changed from month to month.
- **A month is always 30 days.** Monthly numbers are daily numbers × 30.
- **"Other Rates" are examples** (Low ₱ 10, Standard ₱ 12, High ₱ 14). Edit `OTHER_RATES` in `services.py` to use real values. The PH rate is also a fixed number (`PH_RATE`, ₱ 12.00) and is not downloaded from any online source.
- **"Total hours/day" adds every appliance's hours together**, so it can be more than 24.
- **Names can repeat.** Two appliances can have the same name.
- **Tips use one simple rule only:** use the appliance 2 hours less per day.
- **Search works on the name only.**
- **One user, one computer.** There are no accounts, and no way to export the data.

## 13. Author

- **Name:** Floro Jerome A. Uy
- **Section:** CS26L(3581)
