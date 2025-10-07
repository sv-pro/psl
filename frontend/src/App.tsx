import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { lintPrompt, LintResponse } from './api/client';

const EXAMPLE_PROMPT = `You are an expert in analyzing Kubernetes manifests.
Extract the following metrics:
- pod_density_ratio
- mesh_coherence_index
- scheduling_entropy

ALL metrics must be calculated from the manifest.`;

function App() {
  const [prompt, setPrompt] = useState(EXAMPLE_PROMPT);
  const [model, setModel] = useState('claude-3-5-sonnet-20241022');
  const [results, setResults] = useState<LintResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLint = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await lintPrompt({ prompt, model });
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Prompt Semantic Linter</h1>
          <p className="text-gray-400">Detect semantic issues that cause LLM hallucinations</p>
        </header>

        <div className="grid grid-cols-2 gap-8">
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2"
              >
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="gpt-4">GPT-4</option>
                <option value="ollama/llama2">Llama 2 (local)</option>
              </select>
            </div>

            <label className="block text-sm font-medium mb-2">System Prompt</label>
            <div className="border border-gray-700 rounded overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="text"
                theme="vs-dark"
                value={prompt}
                onChange={(value) => setPrompt(value || '')}
              />
            </div>

            <button
              onClick={handleLint}
              disabled={loading}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
            >
              {loading ? 'Analyzing...' : 'Lint Prompt'}
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Results</label>
            <div className="bg-gray-800 border border-gray-700 rounded p-6 h-[500px] overflow-auto">
              {error && (
                <div className="text-red-400 mb-4">
                  Error: {error}
                </div>
              )}

              {results && (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Summary</h3>
                    <div className="space-y-1 text-sm">
                      <div>❌ Errors: {results.summary.total_errors}</div>
                      <div>⚠️  Warnings: {results.summary.total_warnings}</div>
                      <div>📊 Computed fields: {results.summary.computed_fields}</div>
                      <div>🚨 Undefined: {results.summary.undefined_fields}</div>
                    </div>
                  </div>

                  {results.errors.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-2">Issues</h3>
                      <div className="space-y-4">
                        {results.errors.map((err, i) => (
                          <div key={i} className="border-l-4 border-red-500 pl-4 py-2">
                            <div className="font-medium">
                              {err.severity === 'error' ? '❌' : '⚠️'} [{err.rule}]
                            </div>
                            <div className="text-sm text-gray-300 mt-1">{err.message}</div>
                            <div className="text-sm text-blue-400 mt-2">💡 {err.suggestion}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {results.errors.length === 0 && (
                    <div className="text-green-400">
                      ✅ No issues found! This prompt looks good.
                    </div>
                  )}
                </>
              )}

              {!results && !error && !loading && (
                <div className="text-gray-500 text-center mt-20">
                  Click "Lint Prompt" to analyze
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
