import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { ChevronDown, ChevronUp, Loader2, Shield } from "lucide-react";
import { runSimulation as callApi } from "../../services/simulationApi";


interface FinancialInputs {
  startingCash: number;
  monthlyRevenue: number;
  revenueGrowth: number;
  fixedCosts: number;
  variableCostPercent: number;
  payroll: number;
}

interface MonthData {
  month: number;
  cash: number;
  scenarioCash: number;
  revenue: number;
  costs: number;
  burn: number;
}

export function FinancialDashboard() {
  const [inputs, setInputs] = useState<FinancialInputs>({
    startingCash: 0,
    monthlyRevenue: 0,
    revenueGrowth: 0,
    fixedCosts: 0,
    variableCostPercent: 0,
    payroll: 0,
  });

  const [simulationData, setSimulationData] = useState<MonthData[]>([]);
  const [showTable, setShowTable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inside your FinancialDashboard component in src/app/pages/FinancialDashboard.tsx

  // src/app/pages/FinancialDashboard.tsx

  useEffect(() => {
    const fetchAndSimulate = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');

        // 1. Fetch Latest Financial Inputs
        const inputRes = await fetch("http://localhost:8000/api/simulation/latest", {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const inputData = await inputRes.json();

        // 2. Fetch Active Scenario Events
        const scenarioRes = await fetch("http://localhost:8000/api/scenarios/active", {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const scenarioData = await scenarioRes.json();

        if (inputData.inputs) {
          const savedInputs = {
            startingCash: inputData.inputs.owner_equity,
            monthlyRevenue: inputData.inputs.monthly_unit_sales[0],
            revenueGrowth: inputData.inputs.revenue_growth_rate * 100,
            fixedCosts: inputData.inputs.rent,
            variableCostPercent: inputData.inputs.cost_per_unit * 100,
            payroll: inputData.inputs.payroll,
          };
          setInputs(savedInputs);

          // 3. Run simulation with inputs
          runSimulation(savedInputs);
        }
      } catch (err) {
        console.error("Initialization failed", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAndSimulate();
  }, []);


  const handleDeleteHistory = async () => {
    if (!window.confirm("Are you sure you want to clear your saved data?")) return;

    try {
      setLoading(true);
      await fetch("http://localhost:8000/api/simulation-runs/all", {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      // Reset local state to empty
      setInputs({
        startingCash: 0,
        monthlyRevenue: 0,
        revenueGrowth: 0,
        fixedCosts: 0,
        variableCostPercent: 0,
        payroll: 0,
      });
      setSimulationData([]);
    } catch (err) {
      setError("Failed to delete history");
    } finally {
      setLoading(false);
    }
  };


  const runSimulation = async (overrideInputs?: FinancialInputs) => {
    const currentInputs = overrideInputs || inputs;
    setLoading(true);
    setError(null);
    try {
      const result = await callApi({
        price_per_unit: 1,
        monthly_unit_sales: Array(12).fill(Math.round(currentInputs.monthlyRevenue)),
        cost_per_unit: currentInputs.variableCostPercent / 100,
        rent: currentInputs.fixedCosts,
        payroll: currentInputs.payroll,
        marketing: 0,
        utilities: 0,
        equipment_cost: 0,
        buildout_cost: 0,
        owner_equity: currentInputs.startingCash,
        loan_amount: 0,
        loan_interest_rate: 0,
        equipment_life_years: 5,
        revenue_growth_rate: currentInputs.revenueGrowth / 100,
        cost_growth_rate: 0,
        fixed_expense_growth_rate: 0,
      });

      // 1. Combine baseline years into one timeline
      const baselineTimeline = [
        ...result.year1,
        ...result.year2.map((d) => ({ ...d, month: d.month + 12 })),
        ...result.year3.map((d) => ({ ...d, month: d.month + 24 })),
      ];

      // 2. Combine scenario years into one timeline
      const scenarioTimeline = [
        ...result.scenario_year1,
        ...result.scenario_year2.map((d: any) => ({ ...d, month: d.month + 12 })),
        ...result.scenario_year3.map((d: any) => ({ ...d, month: d.month + 24 })),
      ];

      let currentBaselineCash = currentInputs.startingCash;
      let currentScenarioCash = currentInputs.startingCash;

      // 3. Map both timelines into the simulationData state
      const data: MonthData[] = baselineTimeline.map((d: any, idx: number) => {
        const s = scenarioTimeline[idx];
        const costs = Math.round(d.total_costs || 0);
        const burn = Math.round(d.operating_income < 0 ? Math.abs(d.operating_income) : 0);
        const row = {
          month: d.month,
          cash: Math.round(currentBaselineCash),
          scenarioCash: Math.round(currentScenarioCash), // Tracking scenario impact
          revenue: Math.round(d.revenue),
          costs,
          burn,
        };

        currentBaselineCash += d.operating_income;
        currentScenarioCash += s.operating_income;
        return row;
      });

      setSimulationData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  const currentData = simulationData.length > 0 ? simulationData[0] : null;
  const runway = currentData
    ? simulationData.findIndex((d) => d.cash < 0)
    : 0;
  const runwayMonths = runway === -1 ? 24 : runway;

  const getRunwayColor = (months: number) => {
    if (months > 12) return "text-green-400 bg-green-900/30 border-green-600";
    if (months >= 6) return "text-amber-400 bg-amber-900/30 border-amber-600";
    return "text-red-400 bg-red-900/30 border-red-600";
  };
  // Inside src/app/pages/FinancialDashboard.tsx

  const getResilienceMetrics = () => {
    if (simulationData.length === 0) return null;

    // Calculate Minimum Cash across the 24-36 month period
    const minCash = Math.min(...simulationData.map(d => d.cash));

    // Logic matches the reference screenshot: A, Excellent, 24+ mo, etc.
    let grade = "F";
    let label = "Critical";
    let color = "text-red-500 border-red-500/50 bg-red-500/10";
    let description = "High risk of insolvency. Immediate action required.";

    if (runwayMonths >= 24 && minCash > 100000) {
      grade = "A";
      label = "Excellent";
      color = "text-emerald-500 border-emerald-500/50 bg-emerald-500/10";
      description = "Strong financial position with solid runway";
    } else if (runwayMonths > 12) {
      grade = "B";
      label = "Good";
      color = "text-blue-500 border-blue-500/50 bg-blue-500/10";
      description = "Healthy runway with manageable risk levels";
    } else if (runwayMonths >= 6) {
      grade = "C";
      label = "Fair";
      color = "text-amber-500 border-amber-500/50 bg-amber-500/10";
      description = "Moderate risk. Plan for fundraising or cost reduction.";
    }

    return { grade, label, color, description, minCash };
  };

  const metrics = getResilienceMetrics();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-slate-100">
          Financial Model Dashboard
        </h2>
        <p className="text-slate-400 mt-1">
          Model your baseline financial state and project cash runway
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Input Panel */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Company Financial Model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="startingCash">Starting Cash ($)</Label>
              <Input
                id="startingCash"
                type="number"
                value={inputs.startingCash}
                onChange={(e) =>
                  setInputs({ ...inputs, startingCash: Number(e.target.value) })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="monthlyRevenue">Monthly Revenue ($)</Label>
              <Input
                id="monthlyRevenue"
                type="number"
                value={inputs.monthlyRevenue}
                onChange={(e) =>
                  setInputs({
                    ...inputs,
                    monthlyRevenue: Number(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="revenueGrowth">Revenue Growth (%)</Label>
              <Input
                id="revenueGrowth"
                type="number"
                value={inputs.revenueGrowth}
                onChange={(e) =>
                  setInputs({
                    ...inputs,
                    revenueGrowth: Number(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fixedCosts">Fixed Costs ($)</Label>
              <Input
                id="fixedCosts"
                type="number"
                value={inputs.fixedCosts}
                onChange={(e) =>
                  setInputs({ ...inputs, fixedCosts: Number(e.target.value) })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="variableCostPercent">Variable Cost (%)</Label>
              <Input
                id="variableCostPercent"
                type="number"
                value={inputs.variableCostPercent}
                onChange={(e) =>
                  setInputs({
                    ...inputs,
                    variableCostPercent: Number(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="payroll">Payroll ($)</Label>
              <Input
                id="payroll"
                type="number"
                value={inputs.payroll}
                onChange={(e) =>
                  setInputs({ ...inputs, payroll: Number(e.target.value) })
                }
              />
            </div>

            <Button
              onClick={() => runSimulation()}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Running…
                </>
              ) : (
                "Run Simulation"
              )}
            </Button>
            {error && (
              <p className="text-sm text-red-400 mt-2">{error}</p>
            )}
          </CardContent>
        </Card>

        {/* Main Area */}
        <div className="lg:col-span-3 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="shadow-sm">
              <CardContent className="pt-6">
                <div className="text-sm text-slate-400 mb-1">Current Cash</div>
                <div className="text-3xl font-semibold text-slate-100">
                  ${currentData?.cash.toLocaleString() ?? "—"}
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="pt-6">
                <div className="text-sm text-slate-400 mb-1">Monthly Burn</div>
                <div className="text-3xl font-semibold text-slate-100">
                  ${currentData?.burn.toLocaleString() ?? "—"}
                </div>
              </CardContent>
            </Card>

            <Card className={`shadow-sm border-2 ${getRunwayColor(runwayMonths)}`}>
              <CardContent className="pt-6">
                <div className="text-sm mb-1">Runway</div>
                <div className="text-3xl font-semibold">
                  {simulationData.length > 0
                    ? runwayMonths === 24
                      ? "24+ months"
                      : `${runwayMonths} months`
                    : "—"}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cash Projection Chart */}
          {simulationData.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>Projected Runway</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[400px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={simulationData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="month"
                        label={{
                          value: "Months",
                          position: "insideBottom",
                          offset: -5,
                          fill: "#94a3b8"
                        }}
                        stroke="#94a3b8"
                        tick={{ fill: "#94a3b8" }}
                      />
                      <YAxis
                        label={{
                          value: "Cash Balance ($)",
                          angle: -90,
                          position: "insideLeft",
                          fill: "#94a3b8"
                        }}
                        stroke="#94a3b8"
                        tick={{ fill: "#94a3b8" }}
                        tickFormatter={(value) =>
                          `$${(value / 1000).toFixed(0)}k`
                        }
                      />
                      <Tooltip
                        formatter={(value: number) => [
                          `$${value.toLocaleString()}`,
                          "Cash",
                        ]}
                        contentStyle={{
                          backgroundColor: "#1e293b",
                          border: "1px solid #475569",
                          borderRadius: "8px",
                          color: "#e4e7eb"
                        }}
                        labelStyle={{ color: "#e4e7eb" }}
                      />
                      <ReferenceLine
                        y={0}
                        stroke="#ef4444"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        label={{
                          value: "Insolvency",
                          position: "right",
                          fill: "#ef4444",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="cash"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="scenarioCash"
                        stroke="#10b981"
                        strokeWidth={3}
                        // strokeDasharray="5 5" // Dashed line to distinguish from baseline
                        name="Scenario Projection"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Resilience Score Section */}
          {metrics && (
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center gap-2 pb-2">
                <Shield className="w-5 h-5 text-blue-400" />
                <CardTitle className="text-lg font-medium text-slate-100">Resilience Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row items-center gap-8 py-4">
                  {/* Circular Grade Display */}
                  <div className="relative flex items-center justify-center">
                    <div className={`w-32 h-32 rounded-full border-8 flex flex-col items-center justify-center ${metrics.color.split(' ')[1]}`}>
                      <span className="text-4xl font-bold">{metrics.grade}</span>
                      <span className="text-[10px] uppercase tracking-wider opacity-70">{metrics.label}</span>
                    </div>
                    {/* Outer glow ring matching screenshot */}
                    <div className={`absolute inset-[-8px] rounded-full border-2 opacity-20 blur-sm ${metrics.color.split(' ')[1]}`} />
                  </div>

                  {/* Details and KPI stats */}
                  <div className="flex-1 space-y-6">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-slate-300">
                        <Shield className="w-4 h-4 text-emerald-500" />
                        <span>{metrics.description}</span>
                      </div>
                      <Badge className={`${metrics.color} border font-normal`}>
                        {metrics.label} Resilience
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-8 pt-4 border-t border-slate-800">
                      <div>
                        <div className="text-sm text-slate-500 mb-1">Runway</div>
                        <div className={`text-2xl font-bold ${metrics.color.split(' ')[0]}`}>
                          {runwayMonths === 24 ? "24+ mo" : `${runwayMonths} mo`}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-500 mb-1">Min Cash</div>
                        <div className={`text-2xl font-bold ${metrics.color.split(' ')[0]}`}>
                          ${(metrics.minCash / 1000).toFixed(0)}k
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Monthly Data Table */}
          {simulationData.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader>
                <button
                  onClick={() => setShowTable(!showTable)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <CardTitle>Monthly Data Breakdown</CardTitle>
                  {showTable ? (
                    <ChevronUp className="w-5 h-5 text-slate-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-slate-500" />
                  )}
                </button>
              </CardHeader>
              {showTable && (
                <CardContent>
                  <div className="max-h-[400px] overflow-y-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Month</TableHead>
                          <TableHead className="text-right">Cash Balance</TableHead>
                          <TableHead className="text-right text-green-400">Scenario Cash</TableHead> {/* New Header */}
                          <TableHead className="text-right">Revenue</TableHead>
                          <TableHead className="text-right">Total Costs</TableHead>
                          <TableHead className="text-right">Monthly Burn</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {simulationData.map((data) => (
                          <TableRow key={data.month}>
                            <TableCell>{data.month}</TableCell>
                            <TableCell className="text-right">
                              ${data.cash.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right text-green-400"> {/* New Cell */}
                              ${data.scenarioCash.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                              ${data.revenue.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                              ${data.costs.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                              ${data.burn.toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}