## Data Streaming and Visualization Workshop

**Use case: Manufacturing robot predictive maintenance**

This project is a hands-on lab for building a **Predictive Maintenance Dashboard**: the visibility layer of an anomaly-detection and response workflow in a manufacturing facility. The notebooks simulate and process robot joint current measurements, persist streaming data to a cloud database, and apply simple ML (linear regression) plus rule-based thresholds to detect anomalous behavior and raise alerts.

The overall goal is to move from **reactive** maintenance (fix after failure) to **proactive** maintenance by identifying abnormal power consumption patterns before they cause downtime.

---

## Project summary

- **Problem**: Unplanned downtime in industrial robots due to latent mechanical or electrical issues, observable as changes in joint current over time.
- **Approach**: Use historical robot current traces to learn a baseline per-axis relationship between **Time** and **Axis current**, then monitor new data for statistically significant deviations.
- **Key capabilities**:
  - Ingest CSV exports of robot telemetry and stream them into a **Neon PostgreSQL** database.
  - Train **per-axis linear regression models** to estimate expected current.
  - Compute **residuals** (actual − predicted) and apply **threshold rules** to classify Alert/Error events.
  - Visualize trends, residuals, and events in notebooks and dashboards.
  - Log events back to CSV and/or database for traceability.

---

## Repository contents

| Item | Description |
|------|-------------|
| `DataStreamVisualization_Workshop.ipynb` | Streaming simulation: load CSV → insert into Neon PostgreSQL → optional dashboard; includes `StreamingSimulator` and time-series plots. |
| `PredictiveMaintenance.ipynb` | Predictive maintenance pipeline: train per-axis regression (Time → Axis #1–#8), analyze residuals, set MinC/MaxC/T, generate synthetic test data, detect Alert/Error events, visualize and log to CSV/DB. |
| `database.py` | Neon (PostgreSQL) connection utilities, `TraitMeasurement` ORM, and helpers to bulk-load CSV data and query trait measurements. |
| `data/` | Input CSVs (e.g. robot export), synthetic test data, and optional `alerts_errors_log.csv`. |
| `documents/` | ER and schema documentation (e.g. `CAT_DataCollectionDatabase_ER_v1.xlsx`). |
| `images/` | Workshop and use-case figures (architecture, dashboards, Kawasaki examples, etc.). |
| `requirements.txt` | Python package dependencies for the lab environment. |

---

## Setup and environment

1. **Clone the repository**

   ```bash
   git clone <your-fork-or-repo-url>
   cd "Predictive Maintenance_Lab1"
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   Use the provided `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Neon database connection**

   - Create a project at [`neon.tech`](https://neon.tech/) (free tier is sufficient).
   - Obtain your PostgreSQL connection string.
   - In the project root, create a `.env` file:

     ```text
     NEON_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
     ```

   - Keep `.env` private; it should not be committed to version control.

5. **Set up Jupyter environment**

   If you don’t already have Jupyter:

   ```bash
   pip install jupyter
   ```

   You can also use VS Code / Cursor notebooks instead of the classic Jupyter UI.

---

## Running the notebooks

- **Streaming and visualization**
  - Open `DataStreamVisualization_Workshop.ipynb`.
  - Configure the database connection (reads from `.env`).
  - Run the cells to:
    - Load CSV data from `data/` (e.g. `RMBR4-2_export_test.csv`).
    - Stream records into the Neon PostgreSQL instance via `database.py`.
    - Generate basic time-series plots and (optionally) dashboard-like views.

- **Predictive maintenance and alerts**
  - Open `PredictiveMaintenance.ipynb`.
  - Run the notebook to:
    - Train per-axis linear regression models.
    - Compute residuals for training and synthetic test data.
    - Apply alert/error rules (see next section).
    - Visualize results and write events to `data/alerts_errors_log.csv` or to a database table.

---

## Regression model and alert rules

The predictive maintenance logic combines a simple statistical model (linear regression) with rule-based alerting:

- **Baseline model**
  - For each robot axis (`Axis #1`, `Axis #2`, …), fit a **linear regression** model:
    - Input: **Time** (or sample index).
    - Output: **Axis current** for that joint.
  - The fitted line represents the *expected* current profile under normal conditions.

- **Residuals**
  - For each new observation, compute the residual:
    \[
    \text{residual} = I_{\text{actual}} - I_{\text{predicted}}
    \]
  - Large positive residuals indicate that the axis is drawing more current than expected for that point in the cycle, which can be a sign of friction, binding, or other issues.

- **Threshold parameters (per axis)**
  - **`MinC` / `MaxC`**: Lower and upper bounds for acceptable current (or residual) values under normal operation.
  - **`T` (duration)**: Minimum time (or number of consecutive samples) that the current must remain outside `[MinC, MaxC]` before raising an event.

- **Alert vs Error logic**
  - **Alert**: Current or residual exceeds a *warning* threshold and stays out of bounds for at least `T` units, but within a higher, more conservative limit.
  - **Error**: Current or residual exceeds a *critical* threshold and remains there for at least `T` units, indicating high likelihood of imminent failure or unsafe operation.

In `PredictiveMaintenance.ipynb`, these rules are applied to both historical and synthetic data to:

- Mark individual samples or intervals as **Alert** or **Error**.
- Aggregate events by axis, time window, and severity.
- Persist a structured log (e.g. `alerts_errors_log.csv`) for downstream monitoring tools or dashboards.

---

## Results and visualizations

The `images/` folder contains representative figures used in the workshop and in the notebooks:

- **Architecture and dashboards**
  - `PM_Architecture.png` – Overall predictive maintenance architecture (data flow from robot to database to dashboard).
  - `PM_SampleDashboard.png` – Example dashboard view showing trends, alerts, and KPIs.

- **Robot and failure context**
  - `KawasakiMaterialsHandling.png` – Example Kawasaki materials handling robot.
  - `KawasakiFailureCondition.png` – Illustration of failure conditions related to current draw.

- **Trend and alert examples**
  - `KawasakiMajorCurrentIncrease.png` – Example of major current increase on a joint.
  - `KawasakiTrendAndAlert.png` – Trend lines with overlaid Alert/Error indicators.

Within the notebooks, additional plots are generated dynamically, including:

- Time-series plots of current by axis.
- Regression fits and residual distributions.
- Highlighted segments where Alert/Error rules are triggered.

You can extend these visualizations (e.g. via Plotly or a BI tool) to build richer dashboards on top of the logged events and database tables.

---

## Data

- **Input data**
  - Example training and streaming input: `data/RMBR4-2_export_test.csv` — robot trait and axis readings with timestamps. Expected columns include `Trait`, `Axis #1`–`Axis #14`, and `Time`.
  - Synthetic datasets (e.g. `data/synthetic_test.csv`) can be used to simulate fault conditions and validate alert rules.

- **Output data**
  - `database.py` creates and uses a `trait_measurements` table in Neon for time-series storage.
  - Predictive maintenance notebooks can write Alert/Error events to:
    - `data/alerts_errors_log.csv`, and/or
    - A dedicated events table in the PostgreSQL database.

---

## License and attribution

- Add your **team name or names** and **dataset source/license** here if you submit this as coursework or share the repository.
- Workshop use case and imagery: manufacturing robot predictive maintenance (materials handling, current monitoring, and failure prediction scenarios).