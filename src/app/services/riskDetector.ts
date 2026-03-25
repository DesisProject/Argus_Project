// src/app/utils/riskDetector.ts

export interface RiskSignal {
  level: 'critical' | 'warning';
  title: string;
  message: string;
}

export function detectEarlyRisks(
  baseline: any[], 
  scenario: any[]
): RiskSignal[] {
  const signals: RiskSignal[] = [];
  
  // 1. Rapid Runway Depletion (Materially faster than baseline)
  const baselineInsolvency = baseline.findIndex(m => m.cash_balance < 0);
  const scenarioInsolvency = scenario.findIndex(m => m.cash_balance < 0);

  if (scenarioInsolvency !== -1 && (baselineInsolvency === -1 || scenarioInsolvency < baselineInsolvency - 6)) {
    signals.push({
      level: 'critical',
      title: 'Rapid Runway Depletion',
      message: `This scenario pulls insolvency forward by ${baselineInsolvency === -1 ? 'over 24' : baselineInsolvency - scenarioInsolvency} months compared to baseline.`
    });
  }

  // 2. Compounding Cost Shocks (Fixed costs increasing > 20% in 3 months)
  for (let i = 3; i < scenario.length; i++) {
    const costIncrease = (scenario[i].operating_expenses - scenario[i-3].operating_expenses) / scenario[i-3].operating_expenses;
    if (costIncrease > 0.20) {
      signals.push({
        level: 'warning',
        title: 'Compounding Cost Shock',
        message: 'A significant spike in fixed operating expenses detected within a 3-month window.'
      });
      break; 
    }
  }

  return signals;
}