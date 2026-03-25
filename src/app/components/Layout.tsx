import { Outlet, Link, useLocation,useNavigate } from "react-router";
import { TrendingUp, Layers, GitCompare,LogOut } from "lucide-react";
import { useEffect } from "react";
import { logoutUser } from "../services/auth";

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate(); // Initialize navigation
  // Apply dark theme when entering dashboard
  useEffect(() => {
    document.documentElement.classList.add('dark');
    
    // Cleanup when leaving dashboard
    return () => {
      document.documentElement.classList.remove('dark');
    };
  }, []);
  const handleLogout = () => {
    logoutUser(); // Clears the token from localStorage
    navigate("/"); // Redirects to the landing page
  };
  
  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: TrendingUp },
    { path: "/dashboard/scenario-builder", label: "Scenario Builder", icon: Layers },
    { path: "/dashboard/scenario-comparison", label: "Comparison", icon: GitCompare },
  ];

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Top Navigation */}
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-semibold text-white">Argus</h1>
              </div>
              
              <nav className="flex items-center gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                        isActive
                          ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="flex items-center gap-6">
              <div className="hidden md:block text-xs text-slate-500 uppercase tracking-wider font-medium">
                Risk-Aware Decision Simulator
              </div>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}