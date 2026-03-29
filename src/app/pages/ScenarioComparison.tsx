import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { ShieldCheck, Lightbulb, Loader2 } from "lucide-react";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
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
import { AlertTriangle, TrendingUp, TrendingDown } from "lucide-react";
import { ResilienceScore } from "../components/ResilienceScore";
import {
  getLatestSimulation,
  type SimulationResponse,
  type MonthData,
} from "../../services/simulationApi";

interface ScenarioData {
  month: number;
  baseline: number;
  best: number;
  expected: number;
  worst: number;
}

interface VisibleLines {
  baseline: boolean;
  best: boolean;
  expected: boolean;
  worst: boolean;
}

export function ScenarioComparison() {
  const [visibleLines, setVisibleLines] = useState<VisibleLines>({
    baseline: true,
    best: true,
    expected: true,
    worst: true,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simResult, setSimResult] = useState<SimulationResponse | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const latest = await getLatestSimulation();
        if (latest.result) {
          setSimResult(latest.result);
        } else {
          setError("No simulation data available. Run a simulation from the Dashboard first.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load simulation data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Build chart data from the real simulation response
  const scenarioData: ScenarioData[] = useMemo(() => {
    if (!simResult) return [];

    const baselineTimeline = simResult.baseline || [];
    const bestTimeline = simResult.best || [];
    const expectedTimeline = simResult.expected || [];
    const worstTimeline = simResult.worst || [];

    const length = Math.max(
      baselineTimeline.length,
      bestTimeline.length,
      expectedTimeline.length,
      worstTimeline.length
    );

    const data: ScenarioData[] = [];
    for (let i = 0; i < length; i++) {
      data.push({
        month: i + 1,
        baseline: baselineTimeline[i]?.cash_balance ?? 0,
        best: bestTimeline[i]?.cash_balance ?? 0,
        expected: expectedTimeline[i]?.cash_balance ?? 0,
        worst: worstTimeline[i]?.cash_balance ?? 0,
      });
    }
    return data;
  }, [simResult]);

  // Extract risk signals and mitigations from the API response
  const riskSignals = useMemo(() => {
    const raw = simResult?.risk_signals;
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;
    // Backend returns { baseline: [], scenario: [], worst: [] }
    const all: any[] = [];
    for (const key of Object.keys(raw)) {
      const arr = raw[key];
      if (Array.isArray(arr)) all.push(...arr);
    }
    return all;
  }, [simResult]);

  const mitigations = useMemo(() => {
    const raw = simResult?.mitigation_suggestions;
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;
    // Backend returns { baseline: [], scenario: [], worst: [] }
    const all: any[] = [];
    for (const key of Object.keys(raw as Record<string, any>)) {
      const arr = (raw as Record<string, any>)[key];
      if (Array.isArray(arr)) all.push(...arr);
    }
    return all;
  }, [simResult]);

  const getRunway = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    const index = data.findIndex((d) => d[variant] < 0);
    return index === -1 ? data.length : index;
  };

  const getMinCash = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    if (data.length === 0) return 0;
    return Math.min(...data.map((d) => d[variant]));
  };

  const getEndingCash = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    if (data.length === 0) return 0;
    return data[data.length - 1][variant];
  };

  const getResilienceGrade = (runway: number, minCash: number) => {
    if (runway >= 36 && minCash >= 0) return "A"; // Base grade for full survival
    if (runway >= 24) return "B";
    if (runway >= 12) return "C";
    if (runway > 0) return "D";
    return "F";
  };

  const toggleLineVisibility = (line: keyof VisibleLines) => {
    setVisibleLines((prev) => ({ ...prev, [line]: !prev[line] }));
  };

  // Use backend resilience data if available, else derive from chart data
  const baselineMetrics = useMemo(() => {
    if (simResult?.resilience?.baseline) {
      const r = simResult.resilience.baseline;
      return {
        runway: r.runway_months ?? getRunway(scenarioData, "baseline"),
        minCash: r.min_cash ?? getMinCash(scenarioData, "baseline"),
        endingCash: r.ending_cash ?? getEndingCash(scenarioData, "baseline"),
      };
    }
    return {
      runway: getRunway(scenarioData, "baseline"),
      minCash: getMinCash(scenarioData, "baseline"),
      endingCash: getEndingCash(scenarioData, "baseline"),
    };
  }, [scenarioData, simResult]);

  const bestMetrics = useMemo(() => ({
    runway: getRunway(scenarioData, "best"),
    minCash: getMinCash(scenarioData, "best"),
    endingCash: getEndingCash(scenarioData, "best"),
  }), [scenarioData]);

  const expectedMetrics = useMemo(() => ({
    runway: getRunway(scenarioData, "expected"),
    minCash: getMinCash(scenarioData, "expected"),
    endingCash: getEndingCash(scenarioData, "expected"),
  }), [scenarioData]);

  const worstMetrics = useMemo(() => ({
    runway: getRunway(scenarioData, "worst"),
    minCash: getMinCash(scenarioData, "worst"),
    endingCash: getEndingCash(scenarioData, "worst"),
  }), [scenarioData]);

  const runwayDelta = expectedMetrics.runway - baselineMetrics.runway;
  const endingCashDelta = expectedMetrics.endingCash - baselineMetrics.endingCash;

  const comparisonData = [
    {
      variant: "Baseline",
      ...baselineMetrics,
      // Use backend grade if it exists, otherwise use aligned local logic
      resilienceGrade: simResult?.resilience?.baseline?.grade || getResilienceGrade(baselineMetrics.runway, baselineMetrics.minCash),
      delta: null,
    },
    {
      variant: "Best Case",
      ...bestMetrics,
      resilienceGrade: simResult?.resilience?.best?.grade || getResilienceGrade(bestMetrics.runway, bestMetrics.minCash),
      delta: null,
    },
    {
      variant: "Expected Case",
      ...expectedMetrics,
      resilienceGrade: simResult?.resilience?.expected?.grade || getResilienceGrade(expectedMetrics.runway, expectedMetrics.minCash),
      delta: { runway: runwayDelta, endingCash: endingCashDelta },
    },
    {
      variant: "Worst Case",
      ...worstMetrics,
      resilienceGrade: simResult?.resilience?.worst?.grade || getResilienceGrade(worstMetrics.runway, worstMetrics.minCash),
      delta: null,
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        <span className="ml-3 text-slate-400">Loading simulation data…</span>
      </div>
    );
  }

  if (error || scenarioData.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-semibold text-slate-100">Scenario Comparison</h2>
          <p className="text-slate-400 mt-1">
            Compare best, expected, and worst case scenarios under uncertainty
          </p>
        </div>
        <Card className="shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-amber-400">
              <AlertCircle className="w-5 h-5" />
              <p>{error || "No simulation data yet. Run a simulation from the Dashboard to see comparisons."}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-slate-100">
          Scenario Comparison
        </h2>
        <p className="text-slate-400 mt-1">
          Compare best, expected, and worst case scenarios under uncertainty
        </p>
      </div>

      {/* Variant Selector */}
      <div className="flex gap-3">
        <Button
          onClick={() => toggleLineVisibility("best")}
          variant={visibleLines.best ? "default" : "outline"}
          className={
            visibleLines.best
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : ""
          }
        >
          Best Case
        </Button>
        <Button
          onClick={() => toggleLineVisibility("expected")}
          variant={visibleLines.expected ? "default" : "outline"}
          className={
            visibleLines.expected
              ? "bg-amber-600 hover:bg-amber-700 text-white"
              : ""
          }
        >
          Expected Case
        </Button>
        <Button
          onClick={() => toggleLineVisibility("worst")}
          variant={visibleLines.worst ? "default" : "outline"}
          className={
            visibleLines.worst
              ? "bg-red-600 hover:bg-red-700 text-white"
              : ""
          }
        >
          Worst Case
        </Button>
      </div>

      {/* Multi-line Chart */}
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
                    value >= 0
                      ? `$${(value / 1000).toFixed(0)}k`
                      : `-$${Math.abs(value / 1000).toFixed(0)}k`
                  }
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `$${value.toLocaleString()}`,
                    name === "best"
                      ? "Best"
                      : name === "expected"
                        ? "Expected"
                        : name === "worst"
                          ? "Worst"
                          : "Baseline",
                  ]}
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #475569",
                    borderRadius: "8px",
                    color: "#e4e7eb"
                  }}
                  labelStyle={{ color: "#e4e7eb" }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: "20px", color: "#94a3b8" }}
                  formatter={(value) =>
                    value === "baseline"
                      ? "Baseline"
                      : value === "best"
                        ? "Best Case"
                        : value === "expected"
                          ? "Expected Case"
                          : "Worst Case"
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
                {visibleLines.baseline && (
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="baseline"
                  />
                )}
                {visibleLines.best && (
                  <Line
                    type="monotone"
                    dataKey="best"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    dot={false}
                    name="best"
                  />
                )}
                {visibleLines.expected && (
                  <Line
                    type="monotone"
                    dataKey="expected"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={false}
                    name="expected"
                  />
                )}
                {visibleLines.worst && (
                  <Line
                    type="monotone"
                    dataKey="worst"
                    stroke="#ef4444"
                    strokeWidth={3}
                    dot={false}
                    name="worst"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Table */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Scenario Metrics with Delta Analysis</CardTitle>
          <p className="text-sm text-slate-400 mt-1">
            Delta shows difference between Expected Case and Baseline
          </p>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Variant</TableHead>
                <TableHead className="text-right">Minimum Cash</TableHead>
                <TableHead className="text-right">Runway (months)</TableHead>
                <TableHead className="text-right">Ending Cash</TableHead>
                <TableHead className="text-right">Resilience Grade</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {comparisonData.map((row) => (
                <TableRow key={row.variant}>
                  <TableCell className="font-medium">{row.variant}</TableCell>
                  <TableCell className="text-right">
                    ${row.minCash.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span>{row.runway}</span>
                      {row.delta && (
                        <span className={`text-xs flex items-center ${row.delta.runway >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {row.delta.runway >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                          {row.delta.runway >= 0 ? '+' : ''}{row.delta.runway}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span>${row.endingCash.toLocaleString()}</span>
                      {row.delta && (
                        <span className={`text-xs flex items-center ${row.delta.endingCash >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {row.delta.endingCash >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                          ${Math.abs(row.delta.endingCash).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant="outline"
                      className={
                        row.resilienceGrade === "O" || row.resilienceGrade === "A" || row.resilienceGrade === "B"
                          ? "bg-emerald-900/30 text-emerald-400 border-emerald-600"
                          : row.resilienceGrade === "C"
                            ? "bg-amber-900/30 text-amber-400 border-amber-600"
                            : "bg-red-900/30 text-red-400 border-red-600"
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

      {/* Resilience Score Card */}
      <ResilienceScore
        minCashBalance={expectedMetrics.minCash}
        runwayMonths={expectedMetrics.runway}
        grade={simResult?.resilience?.expected?.grade}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Signals from Backend */}
        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <CardTitle>Risk Signals</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {riskSignals.length === 0 ? (
              <p className="text-slate-400 text-sm">No risk signals detected for current scenario.</p>
            ) : (
              <div className="space-y-4">
                {riskSignals.map((signal: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-3 border-b border-slate-700 last:border-b-0"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-slate-100">
                        {signal.title || signal.signal || "Risk Signal"}
                      </div>
                      <div className="text-sm text-slate-400 mt-1">
                        {signal.message || signal.detail || ""}
                      </div>
                    </div>
                    <Badge
                      variant={
                        signal.level === "critical" || signal.severity === "critical"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {signal.level || signal.severity || "warning"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Mitigation Suggestions from Backend */}
        <Card className="border-blue-900/30 bg-blue-950/10 shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-blue-400" />
              <CardTitle>Automated Mitigation & Recovery</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {mitigations.length === 0 ? (
              <p className="text-slate-400 text-sm">No mitigation suggestions available yet.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mitigations.map((sug: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg bg-slate-900/50 border border-slate-700">
                    <h4 className="font-bold text-blue-400 mb-1">
                      {sug.strategy || sug.title || "Suggestion"}
                    </h4>
                    <p className="text-sm text-slate-100 mb-2">
                      {sug.impact || sug.description || ""}
                    </p>
                    {(sug.tradeOff || sug.trade_off) && (
                      <div className="flex items-start gap-2 text-xs text-slate-400 italic">
                        <ShieldCheck className="w-3 h-3 mt-0.5 text-amber-500" />
                        <span>Trade-off: {sug.tradeOff || sug.trade_off}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}