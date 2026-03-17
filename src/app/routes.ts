import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { LandingPage } from "./pages/LandingPage";
import { FinancialDashboard } from "./pages/FinancialDashboard";
import { ScenarioBuilder } from "./pages/ScenarioBuilder";
import { ScenarioComparison } from "./pages/ScenarioComparison";
import { RedirectToScenarioBuilder } from "./components/RedirectToScenarioBuilder";
import { RedirectToScenarioComparison } from "./components/RedirectToScenarioComparison";
import { ErrorBoundary } from "./components/ErrorBoundary";

// Import our new security components
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginForm } from "./components/LoginForm";

export const router = createBrowserRouter([
  // 1. Public Route: Everyone can see the Landing Page
  {
    path: "/",
    Component: LandingPage,
    ErrorBoundary: ErrorBoundary,
  },
  // 2. Public Route: The Login/Signup Screen
  {
    path: "/login",
    Component: LoginForm, 
  },
  // 3. Protected Routes: Locked behind the Bouncer
  {
    path: "/dashboard",
    Component: ProtectedRoute, // <--- The Bouncer is placed here
    ErrorBoundary: ErrorBoundary,
    children: [
      {
        path: "", // This empty path applies the Layout to all children
        Component: Layout,
        children: [
          { index: true, Component: FinancialDashboard },
          { path: "scenario-builder", Component: ScenarioBuilder },
          { path: "scenario-comparison", Component: ScenarioComparison },
        ]
      }
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
