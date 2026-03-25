import { useEffect, useMemo, useState } from "react";
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
  Trash2,
  Zap,
  AlertCircle,
  Users,
  Save,
  RefreshCw,
} from "lucide-react";
import {
  createScenario,
  deleteScenario,
  listScenarios,
  updateScenario,
  type Scenario,
  type ScenarioDecisionPayload,
  type ScenarioPayload,
} from "../../services/simulationApi";

interface Decision {
  id: string;
  type: string;
  name: string;
  impact: number;
  startMonth: number;
  lag: number;
  ramp: number;
  duration: string;
  isStressTest?: boolean;
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

const stressLibrary = [
  {
    type: "market_downturn",
    name: "Market Downturn",
    icon: TrendingDown,
    description: "Reduces revenue growth by 50% for 6 months",
    defaultImpact: -25000,
    duration: "6",
    color: "border-red-500/50 bg-red-950/20 text-red-400 hover:bg-red-950/40",
  },
  {
    type: "customer_churn",
    name: "Major Customer Churn",
    icon: Users,
    description: "Immediate 20% drop in total revenue",
    defaultImpact: -30000,
    duration: "permanent",
    color: "border-orange-500/50 bg-orange-950/20 text-orange-400 hover:bg-orange-950/40",
  },
  {
    type: "funding_delay",
    name: "Funding Delay",
    icon: Calendar,
    description: "Delays expected funding by 6 months",
    defaultImpact: -20000,
    duration: "6",
    color: "border-amber-500/50 bg-amber-950/20 text-amber-400 hover:bg-amber-950/40",
  },
];

function fromApiDecision(decision: ScenarioDecisionPayload & { id?: number }): Decision {
  return {
    id: String(decision.id ?? Date.now()),
    type: decision.type,
    name: decision.name,
    impact: decision.impact,
    startMonth: decision.start_month,
    lag: decision.lag_months ?? 0,
    ramp: decision.ramp_months ?? 1,
    duration:
      decision.duration_months === null || decision.duration_months === undefined
        ? "permanent"
        : String(decision.duration_months),
    isStressTest: stressLibrary.some((s) => s.type === decision.type),
  };
}

function toPayloadDecision(decision: Decision): ScenarioDecisionPayload {
  return {
    type: decision.type,
    name: decision.name,
    impact: decision.impact,
    start_month: decision.startMonth,
    lag_months: decision.lag,
    ramp_months: decision.ramp,
    duration_months: decision.duration === "permanent" ? null : Number(decision.duration),
  };
}

export function ScenarioBuilder() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [scenarioName, setScenarioName] = useState("");
  const [scenarioDescription, setScenarioDescription] = useState("");
  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeScenarioId, setActiveScenarioId] = useState<string>("");
  
  const [config, setConfig] = useState({
    impact: 0,
    startMonth: 1,
    lag: 0,
    ramp: 1,
    duration: "permanent",
  });
  // FETCH: Load from DB on refresh
 useEffect(() => {
  const loadDecisions = async () => {
    const token = localStorage.getItem('token');
    const res = await fetch("http://localhost:8000/api/scenarios/active/decisions", {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (Array.isArray(data)) {
      setDecisions(data); // These will now stay after refresh
    }
    setLoading(false);
  };
  loadDecisions();
}, []);


  // SAVE: Helper to sync state to DB
  // src/app/pages/ScenarioBuilder.tsx

const syncToDb = async (decisions: Decision | Decision[]) => {
  try {
    const decisionArray = Array.isArray(decisions) ? decisions : [decisions];
    
    for (const newDecision of decisionArray) {
      const response = await fetch("http://localhost:8000/api/scenarios/decisions", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // If you have auth implemented:
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          scenario_id: activeScenarioId, // Ensure you have the current scenario ID
          type: newDecision.type,
          month: newDecision.startMonth,
          payload: newDecision.impact // The backend expects 'payload'
        }),
      });

      if (!response.ok) throw new Error('Failed to sync decision');
    }
  } catch (error) {
    console.error("Sync Error:", error);
  }
};
  const selectDecisionType = (type: string) => {
    const decision = decisionLibrary.find((entry) => entry.type === type);
    if (!decision) {
      return;
    }

    setSelectedType(type);
    setConfig((current) => ({ ...current, impact: decision.defaultImpact }));
  };

// src/app/pages/ScenarioBuilder.tsx

const addDecision = async () => {
  if (!selectedType) return;
  const def = decisionLibrary.find((d) => d.type === selectedType);
  
  // Map frontend state to the JSON structure the backend expects
  const payload = {
    type: selectedType,
    name: def!.name,
    impact: config.impact,
    startMonth: config.startMonth, // Backend maps this to start_month
    lag: config.lag,
    ramp: config.ramp,
    duration: config.duration
  };

  try {
    const res = await fetch("http://localhost:8000/api/scenarios/decisions", {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}` 
      },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("Failed to save to DB");
    const savedDecision = await res.json();
    
    // Use the ID returned from the database for the local state
    setDecisions([...decisions, { ...payload, id: savedDecision.id.toString() }]);
    setSelectedType(null);
  } catch (error) {
    console.error("Save Error:", error);
  }
};

const deleteDecision = async (id: string) => {
  try {
    const res = await fetch(`http://localhost:8000/api/scenarios/decisions/${id}`, {
      method: 'DELETE',
      headers: { 
        'Authorization': `Bearer ${localStorage.getItem('token')}` 
      }
    });

    if (res.ok) {
      setDecisions(decisions.filter((d) => d.id !== id));
    }
  } catch (error) {
    console.error("Delete Error:", error);
  }
};

  // Quick Stress Test - Apply all three stress scenarios at once
// src/app/pages/ScenarioBuilder.tsx

const applyQuickStressTest = async () => {
  const stressDecisions = stressLibrary.map((stress, index) => ({
    type: stress.type,
    name: stress.name,
    impact: stress.defaultImpact,
    startMonth: 1 + index * 2,
    lag: 0,
    ramp: 1,
    duration: stress.duration,
  }));

  const savedResults = [];
  
  for (const payload of stressDecisions) {
    try {
      const res = await fetch("http://localhost:8000/api/scenarios/decisions", {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const saved = await res.json();
        savedResults.push({ ...payload, id: saved.id.toString() });
      }
    } catch (error) {
      console.error("Failed to sync stress test decision:", error);
    }
  }

  setDecisions([...decisions, ...savedResults]);
};
  // Add individual stress test
  const addStressTest = (stressType: string) => {
    const stress = stressLibrary.find((entry) => entry.type === stressType);
    if (!stress) {
      return;
    }

    const newDecision: Decision = {
      id: `stress_${Date.now()}`,
      type: stress.type,
      name: stress.name,
      impact: stress.defaultImpact,
      startMonth: 1,
      lag: 0,
      ramp: 1,
      duration: stress.duration,
      isStressTest: true,
    };

    setDecisions((current) => [...current, newDecision]);
  };

  const deleteDecisionFromEditor = (id: string) => {
    setDecisions((current) => current.filter((decision) => decision.id !== id));
  };

  const saveScenario = async () => {
    const trimmedName = scenarioName.trim();
    if (!trimmedName) {
      setError("Scenario name is required");
      return;
    }

    const payload: ScenarioPayload = {
      name: trimmedName,
      description: scenarioDescription.trim() || null,
      decisions: decisions.map(toPayloadDecision),
    };

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const saved =
        activeScenarioId === null
          ? await createScenario(payload)
          : await updateScenario(activeScenarioId, payload);

      await refreshScenarios();
      loadScenarioIntoEditor(saved);
      setSuccess(activeScenarioId === null ? "Scenario created" : "Scenario updated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save scenario");
    } finally {
      setSaving(false);
    }
  };

  const deleteScenarioById = async (scenarioId: number) => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await deleteScenario(scenarioId);
      if (activeScenarioId === scenarioId) {
        resetForm();
      }
      await refreshScenarios();
      setSuccess("Scenario deleted");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete scenario");
    } finally {
      setSaving(false);
    }
  };

  const selectedDecision = decisionLibrary.find((decision) => decision.type === selectedType);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold text-slate-100">Create Scenario</h2>
          <p className="text-slate-400 mt-1">
            Define internal decisions and external events to simulate their impact
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => resetForm()} disabled={saving}>
            New Scenario
          </Button>
          <Button variant="outline" onClick={() => void refreshScenarios()} disabled={loading || saving}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {(error || success) && (
        <Card className="shadow-sm">
          <CardContent className="pt-6">
            {error && <p className="text-red-400 text-sm">{error}</p>}
            {success && <p className="text-green-400 text-sm">{success}</p>}
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Scenario Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="scenarioName">Scenario Name</Label>
            <Input
              id="scenarioName"
              value={scenarioName}
              onChange={(event) => setScenarioName(event.target.value)}
              placeholder="Ex: Conservative Hiring Plan"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="scenarioDescription">Description</Label>
            <Input
              id="scenarioDescription"
              value={scenarioDescription}
              onChange={(event) => setScenarioDescription(event.target.value)}
              placeholder="Optional notes"
            />
          </div>
          <div className="lg:col-span-2 flex gap-2">
            <Button onClick={() => void saveScenario()} disabled={saving}>
              <Save className="w-4 h-4 mr-2" />
              {activeScenarioId === null ? "Create Scenario" : "Update Scenario"}
            </Button>
            {activeScenario && (
              <Button
                variant="destructive"
                onClick={() => void deleteScenarioById(activeScenario.id)}
                disabled={saving}
              >
                Delete Active
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Saved Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-400 text-sm">Loading scenarios...</p>
          ) : scenarios.length === 0 ? (
            <p className="text-slate-400 text-sm">No saved scenarios yet.</p>
          ) : (
            <div className="space-y-2">
              {scenarios.map((scenario) => (
                <div
                  key={scenario.id}
                  className="flex items-center justify-between rounded-md border border-slate-700 px-3 py-2"
                >
                  <button
                    className="text-left"
                    onClick={() => loadScenarioIntoEditor(scenario)}
                    type="button"
                  >
                    <p className="text-slate-100 font-medium">{scenario.name}</p>
                    <p className="text-slate-400 text-xs">
                      Decisions: {scenario.decisions.length} | Updated: {new Date(scenario.updated_at).toLocaleString()}
                    </p>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => void deleteScenarioById(scenario.id)}
                    disabled={saving}
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">Decision Library</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {decisionLibrary.map((decision) => {
              const Icon = decision.icon;
              return (
                <button
                  key={decision.type}
                  onClick={() => selectDecisionType(decision.type)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${decision.color} ${
                    selectedType === decision.type ? "ring-2 ring-blue-500" : ""
                  }`}
                >
                  <Icon className="w-6 h-6 mb-2" />
                  <div className="font-medium">{decision.name}</div>
                  <div className="text-sm opacity-80 mt-1">
                    Default: ${Math.abs(decision.defaultImpact).toLocaleString()} {" "}
                    {decision.defaultImpact > 0 ? "revenue" : "cost"}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">Decision Configuration</h3>
          <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-4">
              {selectedDecision && (
                <div className="pb-4 border-b border-slate-700">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <selectedDecision.icon className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="font-medium text-slate-100">{selectedDecision.name}</div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="impact">Impact Amount ($)</Label>
                <Input
                  id="impact"
                  type="number"
                  value={config.impact}
                  onChange={(event) => setConfig((current) => ({ ...current, impact: Number(event.target.value) }))}
                  disabled={!selectedType}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="startMonth">Start Month</Label>
                <Input
                  id="startMonth"
                  type="number"
                  min="1"
                  max="24"
                  value={config.startMonth}
                  onChange={(event) =>
                    setConfig((current) => ({ ...current, startMonth: Number(event.target.value) }))
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
                  onChange={(event) => setConfig((current) => ({ ...current, lag: Number(event.target.value) }))}
                  disabled={!selectedType}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ramp">Ramp (months)</Label>
                <Input
                  id="ramp"
                  type="number"
                  min="1"
                  value={config.ramp}
                  onChange={(event) => setConfig((current) => ({ ...current, ramp: Number(event.target.value) }))}
                  disabled={!selectedType}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="duration">Duration</Label>
                <Select
                  value={config.duration}
                  onValueChange={(value) => setConfig((current) => ({ ...current, duration: value }))}
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

              <Button onClick={addDecision} disabled={!selectedType} className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                Add to Scenario
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-red-900/30 bg-slate-900/50 shadow-xl overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between border-b border-white/5 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-red-500/10 rounded-md">
                <AlertCircle className="w-5 h-5 text-red-500" />
              </div>
              <CardTitle className="text-slate-100">Stress Testing Framework</CardTitle>
            </div>
            <p className="text-sm text-slate-400">Apply external shocks to test startup resilience</p>
          </div>
          <Button
            variant="outline"
            onClick={applyQuickStressTest}
            className="border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-800 transition-all"
          >
            <Zap className="w-4 h-4 mr-2 text-yellow-500 fill-yellow-500" />
            Quick Stress Test
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {stressLibrary.map((stress) => {
              const Icon = stress.icon;
              return (
                <button
                  key={stress.type}
                  onClick={() => addStressTest(stress.type)}
                  className={`relative p-5 rounded-xl border-2 text-left transition-all group overflow-hidden ${stress.color}`}
                >
                  <Zap className="absolute -top-2 -right-2 w-16 h-16 opacity-[0.03] rotate-12 group-hover:opacity-10 transition-opacity" />
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2 bg-white/5 rounded-lg">
                      <Icon className="w-6 h-6" />
                    </div>
                    <Zap className="w-4 h-4 text-white/20 group-hover:text-yellow-500/50 transition-colors" />
                  </div>
                  <div className="font-bold text-lg tracking-tight">{stress.name}</div>
                  <div className="text-sm opacity-70 mt-1.5 leading-relaxed">{stress.description}</div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Timeline View (12 Months)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative h-24 bg-slate-900/50 rounded-lg border border-slate-700 overflow-x-auto">
            <div className="absolute inset-0 flex">
              {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                <div key={month} className="flex-1 border-r border-slate-700 last:border-r-0 relative">
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-slate-400">M{month}</div>
                  {decisions
                    .filter((decision) => decision.startMonth === month)
                    .map((decision, markerIndex) => (
                      <div
                        key={decision.id}
                        className="absolute top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-blue-500"
                        style={{ top: `${8 + markerIndex * 16}px` }}
                        title={decision.name}
                      />
                    ))}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {decisions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">Active Decisions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decisions.map((decision) => {
              const decisionDef = decisionLibrary.find((entry) => entry.type === decision.type);
              const stressDef = stressLibrary.find((entry) => entry.type === decision.type);
              const Icon = decisionDef?.icon ?? stressDef?.icon ?? Target;

              return (
                <Card key={decision.id} className="shadow-sm">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-slate-300" />
                        </div>
                        <div>
                          <div className="font-medium text-slate-100">{decision.name}</div>
                          <div className="text-sm text-slate-400">Starts month {decision.startMonth}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteDecisionFromEditor(decision.id)}
                        className="p-2 hover:bg-red-900/30 rounded-lg transition-colors"
                        type="button"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Impact:</span>
                        <span className="font-medium text-slate-100">${decision.impact.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Lag:</span>
                        <span className="text-slate-100">{decision.lag} months</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Ramp:</span>
                        <span className="text-slate-100">{decision.ramp} months</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Duration:</span>
                        <span className="text-slate-100">
                          {decision.duration === "permanent" ? "Permanent" : `${decision.duration} months`}
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
