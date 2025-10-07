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
