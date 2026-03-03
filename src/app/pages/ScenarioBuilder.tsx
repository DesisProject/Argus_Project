import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  UserPlus,
  Megaphone,
  TrendingDown,
  DollarSign,
  Calendar,
  Target,
  Edit2,
  Trash2,
} from "lucide-react";

interface Decision {
  id: string;
  type: string;
  name: string;
  impact: number;
  startMonth: number;
  lag: number;
  ramp: number;
  duration: string;
}

const decisionLibrary = [
  {
    type: "hire",
    name: "Hire Employees",
    icon: UserPlus,
    defaultImpact: -15000,
    color: "bg-blue-900/30 border-blue-600 hover:bg-blue-900/50 text-blue-300",
  },
  {
    type: "marketing",
    name: "Marketing Campaign",
    icon: Megaphone,
    defaultImpact: 10000,
    color: "bg-green-900/30 border-green-600 hover:bg-green-900/50 text-green-300",
  },
  {
    type: "demand",
    name: "Demand Shock",
    icon: TrendingDown,
    defaultImpact: -20000,
    color: "bg-red-900/30 border-red-600 hover:bg-red-900/50 text-red-300",
  },
  {
    type: "reduce",
    name: "Reduce Costs",
    icon: DollarSign,
    defaultImpact: -8000,
    color: "bg-green-900/30 border-green-600 hover:bg-green-900/50 text-green-300",
  },
  {
    type: "fundraising",
    name: "Delay Fundraising",
    icon: Calendar,
    defaultImpact: -25000,
    color: "bg-amber-900/30 border-amber-600 hover:bg-amber-900/50 text-amber-300",
  },
  {
    type: "expand",
    name: "Expand to New Market",
    icon: Target,
    defaultImpact: 15000,
    color: "bg-purple-900/30 border-purple-600 hover:bg-purple-900/50 text-purple-300",
  },
];

export function ScenarioBuilder() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  
  const [config, setConfig] = useState({
    impact: 0,
    startMonth: 1,
    lag: 0,
    ramp: 1,
    duration: "permanent",
  });

  const selectDecisionType = (type: string) => {
    const decision = decisionLibrary.find((d) => d.type === type);
    if (decision) {
      setSelectedType(type);
      setConfig({
        ...config,
        impact: decision.defaultImpact,
      });
    }
  };

  const addDecision = () => {
    if (!selectedType) return;
    
    const decision = decisionLibrary.find((d) => d.type === selectedType);
    if (!decision) return;

    const newDecision: Decision = {
      id: Date.now().toString(),
      type: selectedType,
      name: decision.name,
      impact: config.impact,
      startMonth: config.startMonth,
      lag: config.lag,
      ramp: config.ramp,
      duration: config.duration,
    };

    setDecisions([...decisions, newDecision]);
    setSelectedType(null);
    setConfig({
      impact: 0,
      startMonth: 1,
      lag: 0,
      ramp: 1,
      duration: "permanent",
    });
  };

  const deleteDecision = (id: string) => {
    setDecisions(decisions.filter((d) => d.id !== id));
  };

  const selectedDecision = decisionLibrary.find((d) => d.type === selectedType);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-slate-100">
          Create Scenario
        </h2>
        <p className="text-slate-400 mt-1">
          Define internal decisions and external events to simulate their impact
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Decision Library */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">
            Decision Library
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {decisionLibrary.map((decision) => {
              const Icon = decision.icon;
              return (
                <button
                  key={decision.type}
                  onClick={() => selectDecisionType(decision.type)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    decision.color
                  } ${
                    selectedType === decision.type
                      ? "ring-2 ring-blue-500"
                      : ""
                  }`}
                >
                  <Icon className="w-6 h-6 mb-2" />
                  <div className="font-medium">
                    {decision.name}
                  </div>
                  <div className="text-sm opacity-80 mt-1">
                    Default: ${Math.abs(decision.defaultImpact).toLocaleString()}{" "}
                    {decision.defaultImpact > 0 ? "revenue" : "cost"}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column - Configuration */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">
            Decision Configuration
          </h3>
          <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-4">
              {selectedDecision && (
                <div className="pb-4 border-b border-slate-700">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <selectedDecision.icon className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="font-medium text-slate-100">
                      {selectedDecision.name}
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="impact">Impact Amount ($)</Label>
                <Input
                  id="impact"
                  type="number"
                  value={config.impact}
                  onChange={(e) =>
                    setConfig({ ...config, impact: Number(e.target.value) })
                  }
                  disabled={!selectedType}
                />
                <p className="text-xs text-slate-400">
                  Positive for revenue increase, negative for costs
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="startMonth">Start Month</Label>
                <Input
                  id="startMonth"
                  type="number"
                  min="1"
                  max="24"
                  value={config.startMonth}
                  onChange={(e) =>
                    setConfig({ ...config, startMonth: Number(e.target.value) })
                  }
                  disabled={!selectedType}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="lag">Lag (months)</Label>
                <Input
                  id="lag"
                  type="number"
                  min="0"
                  value={config.lag}
                  onChange={(e) =>
                    setConfig({ ...config, lag: Number(e.target.value) })
                  }
                  disabled={!selectedType}
                />
                <p className="text-xs text-slate-400">
                  Delay before impact takes effect
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="ramp">Ramp (months)</Label>
                <Input
                  id="ramp"
                  type="number"
                  min="1"
                  value={config.ramp}
                  onChange={(e) =>
                    setConfig({ ...config, ramp: Number(e.target.value) })
                  }
                  disabled={!selectedType}
                />
                <p className="text-xs text-slate-400">
                  Months to reach full impact
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="duration">Duration</Label>
                <Select
                  value={config.duration}
                  onValueChange={(value) =>
                    setConfig({ ...config, duration: value })
                  }
                  disabled={!selectedType}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="permanent">Permanent</SelectItem>
                    <SelectItem value="3">3 months</SelectItem>
                    <SelectItem value="6">6 months</SelectItem>
                    <SelectItem value="12">12 months</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={addDecision}
                disabled={!selectedType}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                Add to Scenario
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Timeline Visualization */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Timeline View (12 Months)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative h-24 bg-slate-900/50 rounded-lg border border-slate-700 overflow-x-auto">
            <div className="absolute inset-0 flex">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                <div
                  key={month}
                  className="flex-1 border-r border-slate-700 last:border-r-0 relative"
                >
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-slate-400">
                    M{month}
                  </div>
                  
                  {/* Show decision markers */}
                  {decisions
                    .filter((d) => d.startMonth === month)
                    .map((d, idx) => (
                      <div
                        key={d.id}
                        className="absolute top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-blue-500"
                        style={{ top: `${8 + idx * 16}px` }}
                        title={d.name}
                      />
                    ))}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Decisions */}
      {decisions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">
            Active Decisions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decisions.map((decision) => {
              const decisionDef = decisionLibrary.find(
                (d) => d.type === decision.type
              );
              const Icon = decisionDef?.icon || Target;

              return (
                <Card key={decision.id} className="shadow-sm">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-slate-300" />
                        </div>
                        <div>
                          <div className="font-medium text-slate-100">
                            {decision.name}
                          </div>
                          <div className="text-sm text-slate-400">
                            Starts month {decision.startMonth}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                          <Edit2 className="w-4 h-4 text-slate-400" />
                        </button>
                        <button
                          onClick={() => deleteDecision(decision.id)}
                          className="p-2 hover:bg-red-900/30 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Impact:</span>
                        <span className="font-medium text-slate-100">
                          ${decision.impact.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Lag:</span>
                        <span className="text-slate-100">
                          {decision.lag} months
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Ramp:</span>
                        <span className="text-slate-100">
                          {decision.ramp} months
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Duration:</span>
                        <span className="text-slate-100">
                          {decision.duration === "permanent"
                            ? "Permanent"
                            : `${decision.duration} months`}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}