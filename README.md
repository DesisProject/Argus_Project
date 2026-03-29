# Argus — Startup Financial Simulator

Argus is a full-stack financial simulation engine that stress-tests startup strategies across four parallel 3-year timelines — Baseline, Expected, Best Case, and Worst Case. Founders input their financial assumptions, layer in business decisions like hiring or marketing, and get back a resilience grade, runway forecast, and automated mitigation strategies — all behind a secure, per-user account.

> **Design reference:** [Figma — App Design](https://www.figma.com/design/LvBrVgKLx6b82jpYRNVmrT/App-design)

---

## Table of Contents

- [Project Summary](#project-summary)
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Frontend Pages](#frontend-pages)
- [Environment Variables](#environment-variables)
- [Docker Compose](#docker-compose-full-stack)
- [UI Previews](#ui-previews)
- [Future Scope](#future-scope)
- [References](#references)
- [Attributions](#attributions)

---

## Problem Statement

Most early-stage startups rely on static spreadsheets that fail to account for optimism bias or the compounding impact of individual business decisions. When a marketing campaign underperforms or a hiring plan runs over budget, founders have no way to anticipate the downstream effect on cash flow — leading to unexpected runway exhaustion and avoidable failure.

---

## Solution Overview

Argus replaces single-path projections with parallel 36-month simulations. Business events like hiring, marketing, and expansion are applied with standardized cost and timing assumptions across every scenario, removing guesswork. The engine then returns a resilience grade and risk signals so founders can see the consequences of a decision before committing capital.

- **Multi-Scenario Branching**: simultaneously generates four parallel 36-month financial timelines (Baseline, Expected, Best Case, Worst Case) to evaluate varying risk levels
- **Event Simulation Engine**: mathematically calculates the impact of business events such as marketing campaigns, hiring, and capital expansion on the overall financial ledger
- **Standardized Event Assumptions**: applies consistent backend-defined assumptions for event timing, cash burn, delayed revenue impact, and scenario branching to reduce optimism bias
- **Resilience Scoring**: computes a standardized resilience grade (O / A / B / C / F) from simulated cash behaviour, including runway duration, insolvency timing, and cash stability
- **Automated Mitigation Strategies**: surfaces actionable recovery recommendations when risk signals such as critical runway or sustained negative cash flow are detected
- **Interactive Dashboard**: dynamic charts track cash balances, net income, and revenue trajectories across all simulated timelines with side-by-side scenario comparison
- **Secure Per-User Accounts**: JWT-based authentication ensures each founder's scenarios and simulation history are private and persisted across sessions

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
│   ├── resilience.py             # Financial resilience grading logic (O, A, B, C, F)
│   ├── risk_signals.py           # Runway and fragility detection
│   ├── mitigation_engine.py      # Automated strategy generation
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
docker compose up -d db
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

## UI Previews

### Step 1: Define Financial Baseline
Input your starting cash, revenue, costs, and growth assumptions through the Financial Model Dashboard.
<p align="center">
  <img src="src/app/assets/image1.png" width="80%" />
</p>

### Step 2: Add Business Decisions
Layer in hiring, marketing, expansion, or other strategic moves using the Decision Library.
<p align="center">
  <img src="src/app/assets/image2.png" width="80%" />
</p>

### Step 3: Compare Outcomes Under Uncertainty
See how different scenarios affect your runway and cash position across the Baseline, Expected, Best Case, and Worst Case timelines.
<p align="center">
  <img src="src/app/assets/image3.png" width="80%" />
</p>

### Step 4: View Risk Metrics & Mitigation
Get resilience grades (O / A / B / C / F), insolvency risk signals, and actionable automated recommendations.
<p align="center">
  <img src="src/app/assets/image4.png" width="80%" />
</p>

---

## Future Scope

### 1. AI-Based Financial Advisory
The system can be extended with an AI-driven advisory layer to provide insights, risk analysis, and strategic recommendations based on simulation outputs. This would enable natural language interaction and automated interpretation of financial results.

### 2. Automated Data Extraction
The platform can incorporate document processing capabilities to automatically extract financial assumptions from pitch decks, bank statements, and P&L sheets, reducing manual input.

### 3. Advanced Risk Modelling
Enhancements such as correlated Monte Carlo simulations can be introduced to model realistic dependencies between revenue and cost variables, improving prediction accuracy.

### 4. API Integration
Exposing the simulation engine as a REST API would allow integration with third-party financial tools and services.

---

## Attributions

- UI components from [shadcn/ui](https://ui.shadcn.com/) — MIT License
- Photos from [Unsplash](https://unsplash.com) — [Unsplash License](https://unsplash.com/license)