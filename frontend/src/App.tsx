import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { lintPrompt, executePrompt, getExamples, getModels, LintResponse, ExecuteResponse, PromptExample, ModelsResponse } from './api/client';

const EXAMPLE_PROMPT = `You are an expert in analyzing Kubernetes manifests.
Extract the following metrics:
- pod_density_ratio
- mesh_coherence_index
- scheduling_entropy

ALL metrics must be calculated from the manifest.`;

const EXAMPLE_CONTEXT = `apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:1.14.2
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"`;

function App() {
  const [prompt, setPrompt] = useState(EXAMPLE_PROMPT);
  const [context, setContext] = useState(EXAMPLE_CONTEXT);
  const [model, setModel] = useState('gpt-4');
  const [lintResults, setLintResults] = useState<LintResponse | null>(null);
  const [executeResults, setExecuteResults] = useState<ExecuteResponse | null>(null);
  const [lintLoading, setLintLoading] = useState(false);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Examples and models
  const [examples, setExamples] = useState<PromptExample[]>([]);
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [selectedExample, setSelectedExample] = useState<string>('');

  // Load examples and models on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [examplesData, modelsData] = await Promise.all([
          getExamples(),
          getModels()
        ]);
        setExamples(examplesData.examples);
        setModels(modelsData);
      } catch (err) {
        console.error('Failed to load examples/models:', err);
      }
    };
    loadData();
  }, []);

  // Handle example selection
  const handleExampleChange = (exampleId: string) => {
    setSelectedExample(exampleId);
    if (!exampleId) return;

    const example = examples.find(e => e.id === exampleId);
    if (example) {
      setPrompt(example.prompt);
      setContext(example.context);
      // Clear previous results when loading new example
      setLintResults(null);
      setExecuteResults(null);
    }
  };

  const handleLint = async () => {
    setLintLoading(true);
    setError(null);
    try {
      const response = await lintPrompt({ prompt, model });
      setLintResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLintLoading(false);
    }
  };

  const handleExecute = async () => {
    setExecuteLoading(true);
    setError(null);
    try {
      const response = await executePrompt({ prompt, context, model });
      setExecuteResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setExecuteLoading(false);
    }
  };

  const handleLintAndExecute = async () => {
    setLintLoading(true);
    setExecuteLoading(true);
    setError(null);
    try {
      const [lintRes, execRes] = await Promise.all([
        lintPrompt({ prompt, model }),
        executePrompt({ prompt, context, model })
      ]);
      setLintResults(lintRes);
      setExecuteResults(execRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLintLoading(false);
      setExecuteLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-[1800px] mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Prompt Semantic Linter</h1>
          <p className="text-gray-400">Detect semantic issues that cause LLM hallucinations - and see the actual results</p>
        </header>

        {/* Example and Model Selectors */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Example Selector */}
          <div>
            <label className="block text-sm font-medium mb-2">Load Example Prompt</label>
            <select
              value={selectedExample}
              onChange={e => handleExampleChange(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2"
            >
              <option value="">-- Select an example --</option>
              {examples.map(ex => (
                <option key={ex.id} value={ex.id}>
                  {ex.name} ({ex.category})
                </option>
              ))}
            </select>
            {selectedExample && (
              <p className="text-xs text-gray-500 mt-1">
                {examples.find(e => e.id === selectedExample)?.description}
              </p>
            )}
          </div>

          {/* Model Selector */}
          <div>
            <label className="block text-sm font-medium mb-2">Model</label>
            <select
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2"
            >
              {models ? (
                <>
                  <optgroup label="OpenAI">
                    {models.openai.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Anthropic">
                    {models.anthropic.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Ollama (Local)">
                    {models.ollama.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                </>
              ) : (
                <option value="gpt-4">Loading models...</option>
              )}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Configure API keys in backend/.env
            </p>
          </div>
        </div>

        {/* Main Grid: 3 columns */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {/* Column 1: System Prompt */}
          <div>
            <label className="block text-sm font-medium mb-2">System Prompt</label>
            <div className="border border-gray-700 rounded overflow-hidden">
              <Editor
                height="300px"
                defaultLanguage="text"
                theme="vs-dark"
                value={prompt}
                onChange={(value) => setPrompt(value || '')}
              />
            </div>
          </div>

          {/* Column 2: Context/Input */}
          <div>
            <label className="block text-sm font-medium mb-2">Context / User Input</label>
            <div className="border border-gray-700 rounded overflow-hidden">
              <Editor
                height="300px"
                defaultLanguage="yaml"
                theme="vs-dark"
                value={context}
                onChange={(value) => setContext(value || '')}
              />
            </div>
          </div>

          {/* Column 3: Action Buttons */}
          <div>
            <label className="block text-sm font-medium mb-2">Actions</label>
            <div className="space-y-3">
              <button
                onClick={handleLint}
                disabled={lintLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
              >
                {lintLoading ? 'Linting...' : 'Lint Prompt Only'}
              </button>
              <button
                onClick={handleExecute}
                disabled={executeLoading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
              >
                {executeLoading ? 'Executing...' : 'Execute Only'}
              </button>
              <button
                onClick={handleLintAndExecute}
                disabled={lintLoading || executeLoading}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
              >
                {lintLoading || executeLoading ? 'Running...' : 'Lint + Execute'}
              </button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-900/50 border border-red-700 rounded text-red-300 text-sm">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        </div>

        {/* Results Grid: 2 columns */}
        <div className="grid grid-cols-2 gap-6">
          {/* Lint Results */}
          <div>
            <label className="block text-sm font-medium mb-2">Lint Results</label>
            <div className="bg-gray-800 border border-gray-700 rounded p-6 min-h-[400px] overflow-auto">
              {lintResults ? (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Summary</h3>
                    <div className="space-y-1 text-sm">
                      <div>❌ Errors: {lintResults.summary.total_errors}</div>
                      <div>⚠️  Warnings: {lintResults.summary.total_warnings}</div>
                      <div>📊 Computed fields: {lintResults.summary.computed_fields}</div>
                      <div>🚨 Undefined: {lintResults.summary.undefined_fields}</div>
                    </div>
                  </div>

                  {lintResults.errors.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-2">Issues</h3>
                      <div className="space-y-4">
                        {lintResults.errors.map((err, i) => (
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

                  {lintResults.errors.length === 0 && (
                    <div className="text-green-400">
                      ✅ No issues found! This prompt looks good.
                    </div>
                  )}
                </>
              ) : (
                <div className="text-gray-500 text-center mt-20">
                  Click a button above to analyze
                </div>
              )}
            </div>
          </div>

          {/* Execution Results */}
          <div>
            <label className="block text-sm font-medium mb-2">Actual LLM Output</label>
            <div className="bg-gray-800 border border-gray-700 rounded p-6 min-h-[400px] overflow-auto">
              {executeResults ? (
                <>
                  <div className="mb-4 pb-4 border-b border-gray-700">
                    <div className="text-sm text-gray-400">
                      Model: <span className="text-white">{executeResults.model}</span>
                    </div>
                  </div>

                  <div className="prose prose-invert max-w-none">
                    <pre className="bg-gray-900 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap">
                      {executeResults.output}
                    </pre>
                  </div>

                  {lintResults && lintResults.summary.total_errors > 0 && (
                    <div className="mt-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded text-yellow-300 text-sm">
                      ⚠️ This output may contain hallucinations due to lint errors detected
                    </div>
                  )}

                  {lintResults && lintResults.summary.total_errors === 0 && (
                    <div className="mt-4 p-3 bg-green-900/30 border border-green-700 rounded text-green-300 text-sm">
                      ✅ Prompt passed linting - output should be reliable
                    </div>
                  )}
                </>
              ) : (
                <div className="text-gray-500 text-center mt-20">
                  Execute the prompt to see LLM output
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
