import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Shield, TrendingUp, AlertTriangle, AlertCircle } from "lucide-react";

interface ResilienceScoreProps {
  minCashBalance: number;
  runwayMonths: number;
  grade?: string;
}

export function ResilienceScore({
  minCashBalance,
  runwayMonths,
  grade,
}: ResilienceScoreProps) {
  // Calculate resilience grade if not provided
  const calculateResilienceGrade = (
    runway: number,
    minCash: number
  ): string => {
    if (runway >= 18 && minCash >= 0) return "A";
    if (runway >= 12 && runway < 18) return "B";
    if (runway >= 6 && runway < 12) return "C";
    if (runway > 0 && runway < 6) return "D";
    return "F";
  };

  const resilienceGrade = grade || calculateResilienceGrade(runwayMonths, minCashBalance);

  // Grade styling
  const getGradeStyles = (grade: string) => {
    switch (grade) {
      case "A":
        return {
          bg: "bg-green-500",
          text: "text-green-400",
          border: "border-green-500",
          ring: "ring-green-500/20",
          label: "Excellent",
          icon: Shield,
          description: "Strong financial position with solid runway",
        };
      case "B":
        return {
          bg: "bg-blue-500",
          text: "text-blue-400",
          border: "border-blue-500",
          ring: "ring-blue-500/20",
          label: "Good",
          icon: TrendingUp,
          description: "Healthy runway with manageable risks",
        };
      case "C":
        return {
          bg: "bg-amber-500",
          text: "text-amber-400",
          border: "border-amber-500",
          ring: "ring-amber-500/20",
          label: "Fair",
          icon: AlertTriangle,
          description: "Moderate risk - consider fundraising soon",
        };
      case "D":
        return {
          bg: "bg-orange-500",
          text: "text-orange-400",
          border: "border-orange-500",
          ring: "ring-orange-500/20",
          label: "Poor",
          icon: AlertCircle,
          description: "Limited runway - immediate action needed",
        };
      case "F":
        return {
          bg: "bg-red-500",
          text: "text-red-400",
          border: "border-red-500",
          ring: "ring-red-500/20",
          label: "Critical",
          icon: AlertCircle,
          description: "Cash flow negative - urgent intervention required",
        };
      default:
        return {
          bg: "bg-slate-500",
          text: "text-slate-400",
          border: "border-slate-500",
          ring: "ring-slate-500/20",
          label: "Unknown",
          icon: Shield,
          description: "Unable to calculate resilience",
        };
    }
  };

  const styles = getGradeStyles(resilienceGrade);
  const Icon = styles.icon;

  // Calculate progress percentage for visual display
  const getProgressPercentage = (grade: string) => {
    switch (grade) {
      case "A":
        return 100;
      case "B":
        return 80;
      case "C":
        return 60;
      case "D":
        return 40;
      case "F":
        return 20;
      default:
        return 0;
    }
  };

  const progressPercentage = getProgressPercentage(resilienceGrade);

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-400" />
          Resilience Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row items-center gap-6">
          {/* Circular Grade Display */}
          <div className="relative flex-shrink-0">
            <div
              className={`w-32 h-32 rounded-full border-8 ${styles.border} ${styles.ring} ring-8 flex items-center justify-center bg-slate-900`}
            >
              <div className="text-center">
                <div className={`text-5xl font-bold ${styles.text}`}>
                  {resilienceGrade}
                </div>
                <div className="text-xs text-slate-400 mt-1">{styles.label}</div>
              </div>
            </div>
            {/* Progress ring visualization */}
            <svg
              className="absolute top-0 left-0 w-32 h-32 -rotate-90"
              viewBox="0 0 128 128"
            >
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="#1e293b"
                strokeWidth="8"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke={`currentColor`}
                strokeWidth="8"
                strokeDasharray={`${(progressPercentage / 100) * 351.858} 351.858`}
                strokeLinecap="round"
                className={styles.text}
              />
            </svg>
          </div>

          {/* Details */}
          <div className="flex-1 space-y-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-5 h-5 ${styles.text}`} />
                <span className="text-sm text-slate-400">{styles.description}</span>
              </div>
              <Badge
                variant="outline"
                className={`${styles.bg} ${styles.text} border-0`}
              >
                {styles.label} Resilience
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-700">
              <div>
                <div className="text-sm text-slate-400 mb-1">Runway</div>
                <div className={`text-2xl font-semibold ${styles.text}`}>
                  {runwayMonths >= 24 ? "24+" : runwayMonths} mo
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">Min Cash</div>
                <div
                  className={`text-2xl font-semibold ${
                    minCashBalance < 0 ? "text-red-400" : styles.text
                  }`}
                >
                  ${minCashBalance >= 0 ? (minCashBalance / 1000).toFixed(0) : minCashBalance.toLocaleString()}
                  {minCashBalance >= 0 ? "k" : ""}
                </div>
              </div>
            </div>

            {/* Recommendations based on grade */}
            {resilienceGrade !== "A" && (
              <div className="pt-4 border-t border-slate-700">
                <div className="text-xs text-slate-400 mb-2">Recommendations:</div>
                <ul className="text-xs text-slate-300 space-y-1">
                  {resilienceGrade === "F" && (
                    <>
                      <li>• Immediate cost reduction required</li>
                      <li>• Secure emergency funding</li>
                      <li>• Review all expenditures</li>
                    </>
                  )}
                  {resilienceGrade === "D" && (
                    <>
                      <li>• Begin fundraising conversations</li>
                      <li>• Identify cost-cutting opportunities</li>
                      <li>• Accelerate revenue initiatives</li>
                    </>
                  )}
                  {resilienceGrade === "C" && (
                    <>
                      <li>• Prepare fundraising materials</li>
                      <li>• Monitor burn rate closely</li>
                      <li>• Explore revenue diversification</li>
                    </>
                  )}
                  {resilienceGrade === "B" && (
                    <>
                      <li>• Maintain current trajectory</li>
                      <li>• Plan next funding round</li>
                      <li>• Consider strategic growth investments</li>
                    </>
                  )}
                </ul>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
