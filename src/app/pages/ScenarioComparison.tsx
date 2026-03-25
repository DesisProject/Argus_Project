import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
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
  Legend,
} from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { AlertTriangle, RefreshCw } from "lucide-react";
import {
  listScenarios,
  listSimulationRuns,
  type Scenario,
  type SimulationRun,
} from "../../services/simulationApi";

interface ScenarioData {
  month: number;
  best: number;
  expected: number;
  worst: number;
}

type Variant = "best" | "expected" | "worst";

const defaultChartData: ScenarioData[] = Array.from({ length: 24 }, (_, index) => ({
  month: index + 1,
  best: 0,
  expected: 0,
  worst: 0,
}));

export function ScenarioComparison() {
  const [selectedVariant, setSelectedVariant] = useState<Variant>("expected");
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [runData, scenarioData] = await Promise.all([
        listSimulationRuns(50),
        listScenarios(),
      ]);
      setRuns(runData);
      setScenarios(scenarioData);
      setSelectedRunId((current) => {
        if (current !== null && runData.some((run) => run.id === current)) {
          return current;
        }
        return runData[0]?.id ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load simulation runs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshData();
  }, []);

  const scenarioNameById = useMemo(() => {
    return new Map<number, string>(scenarios.map((scenario) => [scenario.id, scenario.name]));
  }, [scenarios]);

  const selectedRun = useMemo(() => {
    if (!runs.length) {
      return null;
    }
    if (selectedRunId === null) {
      return runs[0];
    }
    return runs.find((run) => run.id === selectedRunId) ?? runs[0];
  }, [runs, selectedRunId]);

  const scenarioData = useMemo<ScenarioData[]>(() => {
    if (!selectedRun) {
      return defaultChartData;
    }

    const byMonth = new Map<number, ScenarioData>();

    for (const point of selectedRun.result.best) {
      byMonth.set(point.month, {
        month: point.month,
        best: Math.round(point.cash_balance ?? 0),
        expected: 0,
        worst: 0,
      });
    }

    for (const point of selectedRun.result.expected) {
      const current = byMonth.get(point.month) ?? {
        month: point.month,
        best: 0,
        expected: 0,
        worst: 0,
      };
      current.expected = Math.round(point.cash_balance ?? 0);
      byMonth.set(point.month, current);
    }

    for (const point of selectedRun.result.worst) {
      const current = byMonth.get(point.month) ?? {
        month: point.month,
        best: 0,
        expected: 0,
        worst: 0,
      };
      current.worst = Math.round(point.cash_balance ?? 0);
      byMonth.set(point.month, current);
    }

    return [...byMonth.values()].sort((a, b) => a.month - b.month);
  }, [selectedRun]);

  const getRunway = (data: ScenarioData[], variant: Variant) => {
    const index = data.findIndex((item) => item[variant] < 0);
    return index === -1 ? "24+" : index.toString();
  };

  const getMinCash = (data: ScenarioData[], variant: Variant) => {
    return Math.min(...data.map((item) => item[variant]));
  };

  const getInsolvencyRisk = (runway: string) => {
    if (runway === "24+") return "Low";
    const months = parseInt(runway, 10);
    if (months > 12) return "Low";
    if (months > 6) return "Medium";
    return "High";
  };

  const getResilienceGrade = (runway: string, minCash: number) => {
    if (runway === "24+" && minCash > 200000) return "A";
    if (runway === "24+" || minCash > 100000) return "B";
    if (parseInt(runway, 10) > 12) return "C";
    if (parseInt(runway, 10) > 6) return "D";
    return "F";
  };

  const comparisonData = [
    {
      variant: "Best Case",
      minCash: getMinCash(scenarioData, "best"),
      runway: getRunway(scenarioData, "best"),
      insolvencyRisk: getInsolvencyRisk(getRunway(scenarioData, "best")),
      resilienceGrade: getResilienceGrade(
        getRunway(scenarioData, "best"),
        getMinCash(scenarioData, "best")
      ),
    },
    {
      variant: "Expected Case",
      minCash: getMinCash(scenarioData, "expected"),
      runway: getRunway(scenarioData, "expected"),
      insolvencyRisk: getInsolvencyRisk(getRunway(scenarioData, "expected")),
      resilienceGrade: getResilienceGrade(
        getRunway(scenarioData, "expected"),
        getMinCash(scenarioData, "expected")
      ),
    },
    {
      variant: "Worst Case",
      minCash: getMinCash(scenarioData, "worst"),
      runway: getRunway(scenarioData, "worst"),
      insolvencyRisk: getInsolvencyRisk(getRunway(scenarioData, "worst")),
      resilienceGrade: getResilienceGrade(
        getRunway(scenarioData, "worst"),
        getMinCash(scenarioData, "worst")
      ),
    },
  ];

  const riskDrivers = selectedRun
    ? [
        {
          factor: "Payroll",
          impact: selectedRun.inputs.payroll > 7000 ? "High" : "Medium",
          monthlyEffect: `-$${Math.round(selectedRun.inputs.payroll).toLocaleString()}`,
        },
        {
          factor: "Rent",
          impact: selectedRun.inputs.rent > 3000 ? "High" : "Medium",
          monthlyEffect: `-$${Math.round(selectedRun.inputs.rent).toLocaleString()}`,
        },
        {
          factor: "Marketing",
          impact: selectedRun.inputs.marketing > 3000 ? "High" : "Low",
          monthlyEffect: `-$${Math.round(selectedRun.inputs.marketing).toLocaleString()}`,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold text-slate-100">Scenario Comparison</h2>
          <p className="text-slate-400 mt-1">
            Compare best, expected, and worst trajectories from saved simulation runs
          </p>
        </div>
        <Button variant="outline" onClick={() => void refreshData()} disabled={loading}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="shadow-sm">
          <CardContent className="pt-6">
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Simulation Run</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <p className="text-sm text-slate-400">Loading simulation runs...</p>
          ) : runs.length === 0 ? (
            <p className="text-sm text-slate-400">No simulation runs found yet. Run a simulation from the dashboard first.</p>
          ) : (
            <>
              <Select
                value={selectedRun ? String(selectedRun.id) : undefined}
                onValueChange={(value) => setSelectedRunId(Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a simulation run" />
                </SelectTrigger>
                <SelectContent>
                  {runs.map((run) => (
                    <SelectItem key={run.id} value={String(run.id)}>
                      #{run.id} | {new Date(run.created_at).toLocaleString()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedRun && (
                <div className="flex flex-wrap gap-2 text-xs">
                  <Badge variant="outline">Run ID: {selectedRun.id}</Badge>
                  <Badge variant="outline">
                    Scenario: {selectedRun.scenario_id ? scenarioNameById.get(selectedRun.scenario_id) ?? `#${selectedRun.scenario_id}` : "None"}
                  </Badge>
                  <Badge variant="outline">User: {selectedRun.result.user_email}</Badge>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button
          onClick={() => setSelectedVariant("best")}
          variant={selectedVariant === "best" ? "default" : "outline"}
          className={selectedVariant === "best" ? "bg-blue-600 hover:bg-blue-700 text-white" : ""}
        >
          Best Case
        </Button>
        <Button
          onClick={() => setSelectedVariant("expected")}
          variant={selectedVariant === "expected" ? "default" : "outline"}
          className={selectedVariant === "expected" ? "bg-amber-600 hover:bg-amber-700 text-white" : ""}
        >
          Expected Case
        </Button>
        <Button
          onClick={() => setSelectedVariant("worst")}
          variant={selectedVariant === "worst" ? "default" : "outline"}
          className={selectedVariant === "worst" ? "bg-red-600 hover:bg-red-700 text-white" : ""}
        >
          Worst Case
        </Button>
      </div>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Cash Under Uncertainty</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[450px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={scenarioData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="month"
                  label={{
                    value: "Months",
                    position: "insideBottom",
                    offset: -5,
                    fill: "#94a3b8",
                  }}
                  stroke="#94a3b8"
                  tick={{ fill: "#94a3b8" }}
                />
                <YAxis
                  label={{
                    value: "Cash Balance ($)",
                    angle: -90,
                    position: "insideLeft",
                    fill: "#94a3b8",
                  }}
                  stroke="#94a3b8"
                  tick={{ fill: "#94a3b8" }}
                  tickFormatter={(value) =>
                    value >= 0 ? `$${(value / 1000).toFixed(0)}k` : `-$${Math.abs(value / 1000).toFixed(0)}k`
                  }
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `$${value.toLocaleString()}`,
                    name === "best" ? "Best" : name === "expected" ? "Expected" : "Worst",
                  ]}
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #475569",
                    borderRadius: "8px",
                    color: "#e4e7eb",
                  }}
                  labelStyle={{ color: "#e4e7eb" }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: "20px", color: "#94a3b8" }}
                  formatter={(value) =>
                    value === "best" ? "Best Case" : value === "expected" ? "Expected Case" : "Worst Case"
                  }
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
                <Line type="monotone" dataKey="best" stroke="#3b82f6" strokeWidth={3} dot={false} name="best" />
                <Line
                  type="monotone"
                  dataKey="expected"
                  stroke="#f59e0b"
                  strokeWidth={3}
                  dot={false}
                  name="expected"
                />
                <Line type="monotone" dataKey="worst" stroke="#ef4444" strokeWidth={3} dot={false} name="worst" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Scenario Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Variant</TableHead>
                <TableHead className="text-right">Minimum Cash</TableHead>
                <TableHead className="text-right">Runway (months)</TableHead>
                <TableHead className="text-right">Insolvency Risk</TableHead>
                <TableHead className="text-right">Resilience Grade</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {comparisonData.map((row) => (
                <TableRow key={row.variant}>
                  <TableCell className="font-medium">{row.variant}</TableCell>
                  <TableCell className="text-right">${row.minCash.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{row.runway}</TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant={
                        row.insolvencyRisk === "Low"
                          ? "default"
                          : row.insolvencyRisk === "Medium"
                          ? "secondary"
                          : "destructive"
                      }
                    >
                      {row.insolvencyRisk}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant="outline"
                      className={
                        row.resilienceGrade === "A" || row.resilienceGrade === "B"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : row.resilienceGrade === "C"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-red-50 text-red-700 border-red-200"
                      }
                    >
                      {row.resilienceGrade}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <CardTitle>Risk Drivers (From Selected Run Inputs)</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {selectedRun ? (
            <div className="space-y-4">
              {riskDrivers.map((driver, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-3 border-b border-slate-700 last:border-b-0"
                >
                  <div className="flex-1">
                    <div className="font-medium text-slate-100">{driver.factor}</div>
                    <div className="text-sm text-slate-400 mt-1">Monthly effect: {driver.monthlyEffect}</div>
                  </div>
                  <Badge
                    variant={
                      driver.impact === "Critical"
                        ? "destructive"
                        : driver.impact === "High"
                        ? "secondary"
                        : "outline"
                    }
                  >
                    {driver.impact}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Select a simulation run to inspect its risk profile.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
