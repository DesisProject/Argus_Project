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
}

export interface MonthData {
  month: number;
  revenue: number;
  cogs: number;
  gross_profit: number;
  operating_income: number;
}

export interface SimulationResponse {
  baseline: MonthData[]; // Full 36-month baseline
  scenario: MonthData[];
  year1: MonthData[];
  year2: MonthData[];
  year3: MonthData[];
  scenario_year1: MonthData[];
  scenario_year2: MonthData[];
  scenario_year3: MonthData[];
  best: MonthData[];
  expected: MonthData[];
  worst: MonthData[];
}

const API_BASE = "http://localhost:8000";

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResponse> {
  const token = localStorage.getItem("token");

  const response = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}` // Ensure this is here from our previous fix!
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 401) {
       throw new Error("Session expired. Please log in again.");
    }
    throw new Error(`Simulation failed: ${response.statusText}`);
  }

  return response.json();
}