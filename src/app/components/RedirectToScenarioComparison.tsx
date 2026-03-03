import { Navigate } from "react-router";

export function RedirectToScenarioComparison() {
  return <Navigate to="/dashboard/scenario-comparison" replace />;
}
