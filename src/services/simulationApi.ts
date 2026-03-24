export interface SimulationRequest {
  price_per_unit: number;
  monthly_unit_sales: number[];
  cost_per_unit: number;
  rent: number;
  payroll: number;
  marketing: number;
  utilities: number;
  equipment_cost: number;
  buildout_cost: number;
  owner_equity: number;
  loan_amount: number;
  loan_interest_rate: number;
  equipment_life_years: number;
  revenue_growth_rate: number;
  cost_growth_rate: number;
  fixed_expense_growth_rate: number;
  event_type?: string | null;
  event_payload?: Record<string, unknown> | null;
  scenario_id?: number | null;
}

export interface MonthData {
  month: number;
  revenue: number;
  cogs: number;
  gross_profit: number;
  operating_income: number;
  net_cash_flow?: number;
  cash_balance?: number;
  runway_months?: number;
}

export interface SimulationResponse {
  user_email: string;
  baseline: MonthData[];
  best: MonthData[];
  expected: MonthData[];
  worst: MonthData[];
  simulation_run_id?: number;
}

export interface ScenarioDecisionPayload {
  type: string;
  name: string;
  impact: number;
  start_month: number;
  lag_months?: number;
  ramp_months?: number;
  duration_months?: number | null;
}

export interface ScenarioPayload {
  name: string;
  description?: string | null;
  decisions?: ScenarioDecisionPayload[];
}

export interface Scenario extends ScenarioPayload {
  id: number;
  created_at: string;
  updated_at: string;
  decisions: Array<ScenarioDecisionPayload & { id: number; scenario_id: number; created_at: string }>;
}

export interface SimulationRun {
  id: number;
  scenario_id: number | null;
  inputs: SimulationRequest;
  result: SimulationResponse;
  created_at: string;
}

const API_BASE = "/api";

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

async function readJsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    if (response.status === 401) {
      throw new Error("Session expired. Please log in again.");
    }
    const detail =
      errorBody && typeof errorBody.detail === "string"
        ? errorBody.detail
        : response.statusText;
    throw new Error(detail || "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: buildAuthHeaders(),
    body: JSON.stringify(request),
  });

  return readJsonOrThrow<SimulationResponse>(response);
}

export async function listScenarios(): Promise<Scenario[]> {
  const response = await fetch(`${API_BASE}/scenarios`, {
    headers: buildAuthHeaders(),
  });

  return readJsonOrThrow<Scenario[]>(response);
}

export async function createScenario(payload: ScenarioPayload): Promise<Scenario> {
  const response = await fetch(`${API_BASE}/scenarios`, {
    method: "POST",
    headers: buildAuthHeaders(),
    body: JSON.stringify(payload),
  });

  return readJsonOrThrow<Scenario>(response);
}

export async function updateScenario(
  scenarioId: number,
  payload: Partial<ScenarioPayload>
): Promise<Scenario> {
  const response = await fetch(`${API_BASE}/scenarios/${scenarioId}`, {
    method: "PUT",
    headers: buildAuthHeaders(),
    body: JSON.stringify(payload),
  });

  return readJsonOrThrow<Scenario>(response);
}

export async function deleteScenario(scenarioId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/scenarios/${scenarioId}`, {
    method: "DELETE",
    headers: buildAuthHeaders(),
  });

  if (!response.ok && response.status !== 204) {
    const errorBody = await response.json().catch(() => null);
    const detail =
      errorBody && typeof errorBody.detail === "string"
        ? errorBody.detail
        : response.statusText;
    throw new Error(detail || "Failed to delete scenario");
  }
}

export async function listSimulationRuns(limit = 20): Promise<SimulationRun[]> {
  const response = await fetch(`${API_BASE}/simulation-runs?limit=${limit}`, {
    headers: buildAuthHeaders(),
  });

  return readJsonOrThrow<SimulationRun[]>(response);
}
