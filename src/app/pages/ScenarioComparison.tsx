import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Slider } from "../components/ui/slider";
import { Checkbox } from "../components/ui/checkbox";
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
  const [demandShockSeverity, setDemandShockSeverity] = useState([50]);
  const [visibleLines, setVisibleLines] = useState<VisibleLines>({
    baseline: true,
    best: true,
    expected: true,
    worst: true,
  });

  // Generate multi-scenario data (deterministic based on inputs)
  const generateScenarioData = (): ScenarioData[] => {
    const data: ScenarioData[] = [];
    const startingCash = 500000;
    const severityFactor = demandShockSeverity[0] / 100;

    for (let month = 0; month <= 24; month++) {
      // Baseline - no optimism or pessimism adjustments
      let baselineCash = startingCash + month * 3000 - month * 1500;
      
      // Best case scenario - optimistic revenue, lower costs
      let bestCash = startingCash + month * 18000 - month * 2000;
      
      // Expected case scenario - realistic projections
      let expectedCash = startingCash + month * 8000 - month * 5000;
      
      // Worst case scenario - affected by demand shock
      let worstCash = startingCash - month * 8000 * (1 + severityFactor);

      // Add some deterministic variability based on month
      if (month > 6) {
        baselineCash += (month - 6) * 500;
        bestCash += (month - 6) * 4000;
        expectedCash -= (month - 6) * 1500;
        worstCash -= (month - 6) * 5000 * severityFactor;
      }

      data.push({
        month,
        baseline: Math.round(baselineCash),
        best: Math.round(bestCash),
        expected: Math.round(expectedCash),
        worst: Math.round(worstCash),
      });
    }

    return data;
  };

  const scenarioData = generateScenarioData();

  const getRunway = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    const index = data.findIndex((d) => d[variant] < 0);
    return index === -1 ? 24 : index;
  };

  const getMinCash = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    return Math.min(...data.map((d) => d[variant]));
  };

  const getEndingCash = (data: ScenarioData[], variant: keyof Omit<ScenarioData, 'month'>) => {
    return data[data.length - 1][variant];
  };

  const getResilienceGrade = (runway: number, minCash: number) => {
    if (runway >= 18 && minCash >= 0) return "A";
    if (runway >= 12 && runway < 18) return "B";
    if (runway >= 6 && runway < 12) return "C";
    if (runway > 0 && runway < 6) return "D";
    return "F";
  };

  const toggleLineVisibility = (line: keyof VisibleLines) => {
    setVisibleLines((prev) => ({ ...prev, [line]: !prev[line] }));
  };

  // Calculate metrics for all scenarios
  const baselineMetrics = {
    runway: getRunway(scenarioData, "baseline"),
    minCash: getMinCash(scenarioData, "baseline"),
    endingCash: getEndingCash(scenarioData, "baseline"),
  };

  const bestMetrics = {
    runway: getRunway(scenarioData, "best"),
    minCash: getMinCash(scenarioData, "best"),
    endingCash: getEndingCash(scenarioData, "best"),
  };

  const expectedMetrics = {
    runway: getRunway(scenarioData, "expected"),
    minCash: getMinCash(scenarioData, "expected"),
    endingCash: getEndingCash(scenarioData, "expected"),
  };

  const worstMetrics = {
    runway: getRunway(scenarioData, "worst"),
    minCash: getMinCash(scenarioData, "worst"),
    endingCash: getEndingCash(scenarioData, "worst"),
  };

  // Calculate deltas (Expected vs Baseline)
  const runwayDelta = expectedMetrics.runway - baselineMetrics.runway;
  const endingCashDelta = expectedMetrics.endingCash - baselineMetrics.endingCash;

  const comparisonData = [
    {
      variant: "Baseline",
      minCash: baselineMetrics.minCash,
      runway: baselineMetrics.runway,
      endingCash: baselineMetrics.endingCash,
      resilienceGrade: getResilienceGrade(baselineMetrics.runway, baselineMetrics.minCash),
      delta: null,
    },
    {
      variant: "Best Case",
      minCash: bestMetrics.minCash,
      runway: bestMetrics.runway,
      endingCash: bestMetrics.endingCash,
      resilienceGrade: getResilienceGrade(bestMetrics.runway, bestMetrics.minCash),
      delta: null,
    },
    {
      variant: "Expected Case",
      minCash: expectedMetrics.minCash,
      runway: expectedMetrics.runway,
      endingCash: expectedMetrics.endingCash,
      resilienceGrade: getResilienceGrade(expectedMetrics.runway, expectedMetrics.minCash),
      delta: {
        runway: runwayDelta,
        endingCash: endingCashDelta,
      },
    },
    {
      variant: "Worst Case",
      minCash: worstMetrics.minCash,
      runway: worstMetrics.runway,
      endingCash: worstMetrics.endingCash,
      resilienceGrade: getResilienceGrade(worstMetrics.runway, worstMetrics.minCash),
      delta: null,
    },
  ];

  const riskDrivers = [
    {
      factor: "Hiring increased payroll",
      impact: "High",
      monthlyEffect: "-$15,000",
    },
    {
      factor: "Demand shock reduced revenue",
      impact: "Critical",
      monthlyEffect: `-$${Math.round(20000 * (demandShockSeverity[0] / 100)).toLocaleString()}`,
    },
    {
      factor: "Fundraising delay created cash gap",
      impact: "Medium",
      monthlyEffect: "-$10,000",
    },
  ];

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
                      : "Worst",
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
                    value === "best"
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
                        row.resilienceGrade === "A" || row.resilienceGrade === "B"
                          ? "bg-green-900/30 text-green-400 border-green-600"
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
        grade={getResilienceGrade(expectedMetrics.runway, expectedMetrics.minCash)}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Drivers */}
        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <CardTitle>Risk Drivers</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {riskDrivers.map((driver, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-3 border-b border-slate-700 last:border-b-0"
                >
                  <div className="flex-1">
                    <div className="font-medium text-slate-100">
                      {driver.factor}
                    </div>
                    <div className="text-sm text-slate-400 mt-1">
                      Monthly effect: {driver.monthlyEffect}
                    </div>
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
          </CardContent>
        </Card>

        {/* Interactive Demand Shock Slider */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Demand Shock Severity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-slate-400">
                  Adjust severity to see impact on projections
                </span>
                <span className="font-semibold text-lg text-slate-100">
                  {demandShockSeverity[0]}%
                </span>
              </div>
              <Slider
                value={demandShockSeverity}
                onValueChange={setDemandShockSeverity}
                max={100}
                step={5}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-2">
                <span>Mild</span>
                <span>Moderate</span>
                <span>Severe</span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-700">
              <div className="text-sm text-slate-400 mb-2">
                Current Impact Analysis
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Revenue reduction:</span>
                  <span className="font-medium text-red-400">
                    -{demandShockSeverity[0]}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Monthly loss:</span>
                  <span className="font-medium text-red-400">
                    -$
                    {Math.round(
                      20000 * (demandShockSeverity[0] / 100)
                    ).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Recovery timeline:</span>
                  <span className="font-medium text-slate-100">
                    {Math.round((demandShockSeverity[0] / 10) + 3)} months
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}