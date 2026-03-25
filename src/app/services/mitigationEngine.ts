// src/app/utils/mitigationEngine.ts

export interface MitigationSuggestion {
  strategy: string;
  impact: string;
  tradeOff: string;
}

export function generateMitigations(
  expectedTimeline: any[], 
  worstTimeline: any[]
): MitigationSuggestion[] {
  const suggestions: MitigationSuggestion[] = [];
  
  const expectedInsolvency = expectedTimeline.findIndex(m => m.cash_balance < 0);
  const worstInsolvency = worstTimeline.findIndex(m => m.cash_balance < 0);

  // Scenario: Cash Gap detected in Worst Case
  if (worstInsolvency !== -1) {
    suggestions.push({
      strategy: "Reduce Variable Costs by 20%",
      impact: `Extends runway in the Worst Case by approximately ${Math.ceil(worstInsolvency * 0.2)} months.`,
      tradeOff: "May slow down product development or customer acquisition speed."
    });
  }

  // Scenario: Burn rate is too high in Expected Case
  if (expectedInsolvency !== -1 && expectedInsolvency < 12) {
    suggestions.push({
      strategy: "Immediate Hiring Freeze",
      impact: "Reduces monthly burn by 15-25%, potentially avoiding insolvency in Year 1.",
      tradeOff: "Increases workload on current staff; potential for burnout."
    });
  }

  // Default suggestion for healthy startups
  if (suggestions.length === 0) {
    suggestions.push({
      strategy: "Opportunistic Expansion",
      impact: "Current cash reserves support a 15% increase in marketing spend.",
      tradeOff: "Reduces overall cash buffer for unexpected market shocks."
    });
  }

  return suggestions;
}