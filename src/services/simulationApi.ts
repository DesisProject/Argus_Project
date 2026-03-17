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
  year1: MonthData[];
  year2: MonthData[];
  year3: MonthData[];
}

const API_BASE = "";

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.statusText}`);
  }

  return response.json();
}