import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Slider } from "../components/ui/slider";
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
import { AlertTriangle } from "lucide-react";

interface ScenarioData {
  month: number;
  best: number;
  expected: number;
  worst: number;
}

type Variant = "best" | "expected" | "worst";

export function ScenarioComparison() {
  const [selectedVariant, setSelectedVariant] = useState<Variant>("expected");
  const [demandShockSeverity, setDemandShockSeverity] = useState([50]);

  // Generate scenario data based on demand shock severity
  const generateScenarioData = (): ScenarioData[] => {
    const data: ScenarioData[] = [];
    const startingCash = 500000;
    const severityFactor = demandShockSeverity[0] / 100;

    for (let month = 0; month <= 24; month++) {
      // Best case scenario
      let bestCash = startingCash + month * 15000;
      
      // Expected case scenario
      let expectedCash = startingCash + month * 5000 - month * 2000;
      
      // Worst case scenario - affected by demand shock
      let worstCash = startingCash - month * 8000 * (1 + severityFactor);

      // Add some variability
      if (month > 6) {
        bestCash += (month - 6) * 3000;
        expectedCash -= (month - 6) * 1000;
        worstCash -= (month - 6) * 5000 * severityFactor;
      }

      data.push({
        month,
        best: Math.round(bestCash),
        expected: Math.round(expectedCash),
        worst: Math.round(worstCash),
      });
    }

    return data;
  };

  const scenarioData = generateScenarioData();

  const getRunway = (data: ScenarioData[], variant: Variant) => {
    const index = data.findIndex((d) => d[variant] < 0);
    return index === -1 ? "24+" : index.toString();
  };

  const getMinCash = (data: ScenarioData[], variant: Variant) => {
    return Math.min(...data.map((d) => d[variant]));
  };

  const getInsolvencyRisk = (runway: string) => {
    if (runway === "24+") return "Low";
    const months = parseInt(runway);
    if (months > 12) return "Low";
    if (months > 6) return "Medium";
    return "High";
  };

  const getResilienceGrade = (runway: string, minCash: number) => {
    if (runway === "24+" && minCash > 200000) return "A";
    if (runway === "24+" || minCash > 100000) return "B";
    if (parseInt(runway) > 12) return "C";
    if (parseInt(runway) > 6) return "D";
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
          onClick={() => setSelectedVariant("best")}
          variant={selectedVariant === "best" ? "default" : "outline"}
          className={
            selectedVariant === "best"
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : ""
          }
        >
          Best Case
        </Button>
        <Button
          onClick={() => setSelectedVariant("expected")}
          variant={selectedVariant === "expected" ? "default" : "outline"}
          className={
            selectedVariant === "expected"
              ? "bg-amber-600 hover:bg-amber-700 text-white"
              : ""
          }
        >
          Expected Case
        </Button>
        <Button
          onClick={() => setSelectedVariant("worst")}
          variant={selectedVariant === "worst" ? "default" : "outline"}
          className={
            selectedVariant === "worst"
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
                <Line
                  type="monotone"
                  dataKey="best"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={false}
                  name="best"
                />
                <Line
                  type="monotone"
                  dataKey="expected"
                  stroke="#f59e0b"
                  strokeWidth={3}
                  dot={false}
                  name="expected"
                />
                <Line
                  type="monotone"
                  dataKey="worst"
                  stroke="#ef4444"
                  strokeWidth={3}
                  dot={false}
                  name="worst"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Table */}
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
                  <TableCell className="text-right">
                    ${row.minCash.toLocaleString()}
                  </TableCell>
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