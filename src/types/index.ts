// Shared types used by the simulation API layer

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
  decisions: ScenarioDecisionPayload[];
}
