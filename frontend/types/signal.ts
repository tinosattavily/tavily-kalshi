export type Signal = {
  market_prob?: number;
  model_prob?: number;
  edge_pct?: number;
  expected_value_per_dollar?: number;
  kelly_fraction_yes?: number;
  kelly_fraction_no?: number;
  confidence_level?: string;
  confidence_score?: number;
  recommended_action?: string;
  recommended_size_fraction?: number;
  target_take_profit_prob?: number;
  target_stop_loss_prob?: number;
  horizon?: string;
  rationale_short?: string;
  rationale_long?: string;
  // Legacy fields for backward compatibility
  direction?: string;
  model_prob_abs?: number;
  confidence?: string;
  rationale?: string;
};
