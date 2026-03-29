# Argus — Startup Financial Simulator

Argus is a full-stack financial simulation platform for startups. It lets founders model revenue, expenses, and cash-flow over a 3-year horizon, build "what-if" scenarios with configurable decisions, and compare outcomes side-by-side — all behind a secure, per-user account.

> **Design reference:** [Figma — App Design](https://www.figma.com/design/LvBrVgKLx6b82jpYRNVmrT/App-design)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 · TypeScript · Vite 6 · Tailwind CSS 4 · Recharts · React Router 7 |
| **Backend** | Python 3 · FastAPI · SQLAlchemy · Alembic · Pydantic |
| **Database** | PostgreSQL 15 |
| **Auth** | JWT (PyJWT) · bcrypt (passlib) |
| **Infra** | Docker Compose |

---

## Project Structure

```
Argus_Project/
├── src/                          # Frontend source
│   ├── main.tsx                  # React entry point
│   ├── app/
│   │   ├── routes.ts             # Client-side routing
│   │   ├── pages/                # Landing, Dashboard, Scenario Builder, Comparison
│   │   ├── components/           # Shared / layout components
│   │   └── services/             # API service layer
│   ├── imports/                  # Shared UI primitives
│   └── styles/                   # Global styles
│
├── startup_financial_engine/     # Backend source
│   ├── api.py                    # FastAPI application & routes
│   ├── auth.py                   # Password hashing & JWT helpers
│   ├── config.py                 # Environment / DB config
│   ├── database.py               # SQLAlchemy engine & session
│   ├── main.py                   # Cash-flow metric calculations
│   ├── event_calculators.py      # Event dispatcher for simulations
│   ├── year_simulator.py         # Year-level simulation runner
│   ├── models/                   # ORM & domain models
│   │   ├── user.py
│   │   ├── scenario.py
│   │   ├── scenario_decision.py
│   │   ├── simulation_run.py
│   │   ├── assumptions.py
│   │   ├── forecast.py
│   │   ├── year_simulator.py
│   │   ├── revenue.py / expenses.py / cashflow.py
│   │   ├── income_statement.py / balance_sheet.py
│   │   └── funding.py / decisions.py
│   ├── alembic/                  # Database migrations
│   ├── requirements.txt
│   └── .env                      # DB connection string (git-ignored)
│
├── docker-compose.yml            # App + PostgreSQL services
├── vite.config.ts                # Vite dev server + API proxy
├── package.json
└── index.html
```

---

## Prerequisites

- **Node.js** ≥ 18 and **npm**
- **Python** ≥ 3.11
- **PostgreSQL** 15 (or use Docker Compose — see below)

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd Argus_Project
```

### 2. Start the database

**Option A — Docker Compose (recommended)**

```bash
docker-compose up -d db
```

This spins up PostgreSQL 15 on `localhost:5432` with:
- Database: `argus_dev`
- User / Password: `postgres` / `postgres`

**Option B — Local PostgreSQL**

Create the database manually and make sure the connection string in `startup_financial_engine/.env` matches:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/argus_dev
```

### 3. Backend setup

```bash
cd startup_financial_engine
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell)
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Run database migrations:**

```bash
alembic upgrade head
```

**Start the API server:**

```bash
uvicorn api:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 4. Frontend setup

```bash
# From the project root
npm install
npm run dev
```

Vite starts at `http://localhost:5173` and automatically proxies `/api/*` requests to the backend.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/register` | — | Create a new user account |
| `POST` | `/api/login` | — | Obtain a JWT access token |
| `POST` | `/api/simulate` | 🔒 | Run a 3-year financial simulation |
| `GET` | `/api/simulation/latest` | 🔒 | Get the latest simulation run |
| `GET` | `/api/simulation-runs` | 🔒 | List past simulation runs |
| `DELETE`| `/api/simulation-runs/all` | 🔒 | Delete all past simulation runs |
| `DELETE`| `/api/simulation-runs/:id` | 🔒 | Delete a specific simulation run |
| `GET` | `/api/scenarios` | 🔒 | List user's saved scenarios |
| `POST` | `/api/scenarios` | 🔒 | Create a new scenario with decisions |
| `GET` | `/api/scenarios/:id` | 🔒 | Get a single scenario |
| `PUT` | `/api/scenarios/:id` | 🔒 | Update a scenario |
| `DELETE`| `/api/scenarios/:id` | 🔒 | Delete a scenario |
| `POST` | `/api/scenarios/decisions` | 🔒 | Add a decision to the active scenario |
| `GET` | `/api/scenarios/active/decisions` | 🔒 | List decisions for the active scenario |
| `DELETE`| `/api/scenarios/decisions/:id` | 🔒 | Delete a specific scenario decision |

---

## Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing Page | Marketing / intro page |
| `/login` | Login | User authentication |
| `/signup` | Sign Up | New account registration |
| `/dashboard` | Financial Dashboard | Core simulation charts & metrics |
| `/dashboard/scenario-builder` | Scenario Builder | Create & edit what-if scenarios |
| `/dashboard/scenario-comparison` | Scenario Comparison | Compare scenario outcomes |

---

## Environment Variables

| Variable | Location | Default |
|----------|----------|---------|
| `DATABASE_URL` | `startup_financial_engine/.env` | `postgresql://postgres:postgres@localhost:5432/argus_dev` |

> **Note:** The `.env` file is git-ignored. Copy the value above or set your own connection string.

---

## Docker Compose (Full Stack)

To run **both** the app container and PostgreSQL together:

```bash
docker-compose up -d
```

The app container exposes port **8000** and automatically connects to the `db` service.

---

## Attributions

- UI components from [shadcn/ui](https://ui.shadcn.com/) — MIT License
- Photos from [Unsplash](https://unsplash.com) — [Unsplash License](https://unsplash.com/license)