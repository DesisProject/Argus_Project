import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { LandingPage } from "./pages/LandingPage";
import { FinancialDashboard } from "./pages/FinancialDashboard";
import { ScenarioBuilder } from "./pages/ScenarioBuilder";
import { ScenarioComparison } from "./pages/ScenarioComparison";
import { RedirectToScenarioBuilder } from "./components/RedirectToScenarioBuilder";
import { RedirectToScenarioComparison } from "./components/RedirectToScenarioComparison";
import { ErrorBoundary } from "./components/ErrorBoundary";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: LandingPage,
    ErrorBoundary: ErrorBoundary,
  },
  {
    path: "/dashboard",
    Component: Layout,
    ErrorBoundary: ErrorBoundary,
    children: [
      { index: true, Component: FinancialDashboard },
      { path: "scenario-builder", Component: ScenarioBuilder },
      { path: "scenario-comparison", Component: ScenarioComparison },
    ],
  },
  // Redirect old paths to new dashboard paths
  {
    path: "/scenario-builder",
    Component: RedirectToScenarioBuilder,
  },
  {
    path: "/scenario-comparison",
    Component: RedirectToScenarioComparison,
  },
]);