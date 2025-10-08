export interface LintRequest {
  prompt: string;
  model?: string;
}

export interface LintError {
  rule: string;
  severity: string;
  message: string;
  suggestion: string;
}

export interface LintResponse {
  ir: any;
  errors: LintError[];
  summary: {
    total_errors: number;
    total_warnings: number;
    computed_fields: number;
    undefined_fields: number;
  };
}

export interface ExecuteRequest {
  prompt: string;
  context: string;
  model?: string;
}

export interface ExecuteResponse {
  output: string;
  model: string;
  has_errors: boolean;
}

const API_BASE = 'http://localhost:8000';

export async function lintPrompt(req: LintRequest): Promise<LintResponse> {
  const response = await fetch(`${API_BASE}/lint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function executePrompt(req: ExecuteRequest): Promise<ExecuteResponse> {
  const response = await fetch(`${API_BASE}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export interface PromptExample {
  id: string;
  name: string;
  category: string;
  type: 'good' | 'bad';
  prompt_file: string;
  context_file: string;
  description: string;
  expected_behavior: string;
  prompt: string;
  context: string;
}

export interface ExamplesResponse {
  examples: PromptExample[];
}

export async function getExamples(): Promise<ExamplesResponse> {
  const response = await fetch(`${API_BASE}/examples`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export interface ModelsResponse {
  openai?: string[];
  anthropic?: string[];
  google?: string[]; // Gemini models
  ollama?: string[];
}

export async function getModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE}/models`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(10000) // 10 second timeout
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getHealthyModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE}/models/healthy`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(15000) // 15 second timeout for health checks
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export interface EvaluationRequest {
  example_ids?: string[];
  models?: string[];
}

export interface EvaluationResult {
  example_id: string;
  example_name: string;
  example_type: string;
  model: string;
  provider: string;
  lint_errors_count: number;
  lint_warnings_count: number;
  undefined_fields: string[];
  llm_output: string;
  execution_error: string | null;
  outcome: 'success' | 'failure' | 'error';
  reasoning: string;
  hallucination_detected: boolean;
}

export interface EvaluationResponse {
  results: EvaluationResult[];
  summary: {
    total_evaluations: number;
    successes: number;
    failures: number;
    errors: number;
    success_rate: number;
    models_tested: string[];
    examples_tested: number;
  };
}

export async function runEvaluation(req: EvaluationRequest): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
