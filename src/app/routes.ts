import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { LandingPage } from "./pages/LandingPage";
import { FinancialDashboard } from "./pages/FinancialDashboard";
import { ScenarioBuilder } from "./pages/ScenarioBuilder";
import { ScenarioComparison } from "./pages/ScenarioComparison";
import { RedirectToScenarioBuilder } from "./components/RedirectToScenarioBuilder";
import { RedirectToScenarioComparison } from "./components/RedirectToScenarioComparison";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginForm } from "./components/LoginForm";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: LandingPage,
    ErrorBoundary: ErrorBoundary,
  },
  {
    path: "/login",
    Component: LoginForm, 
  },
  {
    path: "/signup",
    Component: LoginForm, 
  },
  {
    path: "/dashboard",
    Component: ProtectedRoute,
    ErrorBoundary: ErrorBoundary,
    children: [
      {
        path: "",
        Component: Layout,
        children: [
          { index: true, Component: FinancialDashboard },
          { path: "scenario-builder", Component: ScenarioBuilder },
          { path: "scenario-comparison", Component: ScenarioComparison },
        ]
      }
    ],
  },
  {
    path: "/scenario-builder",
    Component: RedirectToScenarioBuilder,
  },
  {
    path: "/scenario-comparison",
    Component: RedirectToScenarioComparison,
  },
]);
