import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
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
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
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
  revenue: number;
  costs: number;
  burn: number;
}

export function FinancialDashboard() {
  const [inputs, setInputs] = useState<FinancialInputs>({
    startingCash: 500000,
    monthlyRevenue: 50000,
    revenueGrowth: 10,
    fixedCosts: 20000,
    variableCostPercent: 30,
    payroll: 40000,
  });

  const [simulationData, setSimulationData] = useState<MonthData[]>([]);
  const [showTable, setShowTable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await callApi({
        price_per_unit: 1,
        monthly_unit_sales: Array(12).fill(Math.round(inputs.monthlyRevenue)),
        cost_per_unit: inputs.variableCostPercent / 100,
        rent: inputs.fixedCosts,
        payroll: inputs.payroll,
        marketing: 0,
        utilities: 0,
        equipment_cost: 0,
        buildout_cost: 0,
        owner_equity: inputs.startingCash,
        loan_amount: 0,
        loan_interest_rate: 0,
        equipment_life_years: 5,
        revenue_growth_rate: inputs.revenueGrowth / 100,
        cost_growth_rate: 0,
        fixed_expense_growth_rate: 0,
      });

      const data: MonthData[] = result.baseline.map((d) => {
        const costs = Math.round(d.revenue - d.operating_income);
        const burn = Math.round(-d.operating_income);
        return {
          month: d.month,
          cash: Math.round(d.cash_balance ?? 0),
          revenue: Math.round(d.revenue),
          costs,
          burn,
        };
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
              onClick={runSimulation}
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
                    </LineChart>
                  </ResponsiveContainer>
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