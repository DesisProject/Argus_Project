import { Navigate } from "react-router";

export function RedirectToScenarioBuilder() {
  return <Navigate to="/dashboard/scenario-builder" replace />;
}
