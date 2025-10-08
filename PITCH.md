# PSL: Prompt Semantic Linter

## The Three-Dimensional Value Proposition

PSL is not just a linting tool—it's a **multi-purpose measurement platform** that simultaneously demonstrates, validates, and benchmarks three critical aspects of AI system reliability.

---

## 1. Prompt Quality Measurement

### Utility Dimension: "How good is this prompt?"
PSL measures prompt effectiveness through **semantic analysis**, detecting structural issues that cause hallucinations and unpredictable behavior:

- **Undefined computed fields**: Asking for metrics without providing formulas
- **Ambiguous domain terminology**: Using technical terms without definitions
- **Missing fallback strategies**: No guidance for handling incomplete data
- **Conflicting constraints**: Contradictory output requirements

**Example:**
```
❌ Bad Prompt: "Calculate pod_density_ratio and mesh_coherence_index"
✅ Good Prompt: "pod_density_ratio = containers / memory (return null if missing)"
```

### Didactic Dimension: "How well does this demonstrate the problem?"
PSL's **didactic evaluation system** validates whether prompts effectively demonstrate their quality:

- **Bad prompts that cause hallucinations** → ✅ Didactic Success (proves PSL's value)
- **Good prompts that produce correct outputs** → ✅ Didactic Success (shows solutions work)
- **Bad prompts that don't trigger issues** → ❌ Didactic Failure (model too defensive for demo)
- **Good prompts that still fail** → ❌ Didactic Failure (model fundamentally unreliable)

This creates a **quality-controlled prompt dataset** for demonstrations, training, and research.

---

## 2. IntentHub Building Block: Reliable AI from Unreliable Components

PSL embodies the **core IntentHub philosophy**: building dependable AI systems by composing layers of validation around inherently probabilistic components.

### The Semantic Linter Pattern

```
User Intent → Semantic Parser (LLM) → Structured IR → Validation Rules → Actionable Feedback
                    ↓                                          ↓
              (Unreliable)                              (Deterministic)
```

**Key Insight:** Even if the parser LLM occasionally misinterprets a prompt, the **rule-based validation layer** catches semantic issues deterministically. Two unreliable components (parser + executor) become more reliable through a reliable intermediary (validator).

### IntentHub Architecture Principles Demonstrated:

1. **Structured Intermediate Representation (IR)**: Convert fuzzy natural language to analyzable data structures
2. **Separation of Concerns**: Parse semantics with AI, validate logic with rules
3. **Layered Reliability**: Deterministic checks compensate for probabilistic inference
4. **Composability**: Semantic linters can validate other semantic linters (meta-validation)

**This is A.G.I.L.E. in action:**
- **Auditable**: IR provides inspectable intermediate state
- **Gradual**: Add new validation rules incrementally
- **Interpretable**: Lint errors explain *why* a prompt is problematic
- **Layered**: Parse → Validate → Execute as distinct stages
- **Explicit**: Computed fields, constraints, and fallbacks made explicit

PSL proves you can **systematically reduce AI unreliability** without requiring more capable models.

---

## 3. Model Benchmarking with Quality-Controlled Prompts

PSL provides **fair, reproducible model comparisons** by controlling the most critical variable: **prompt quality**.

### The Benchmark Challenge
Traditional LLM benchmarks suffer from:
- **Prompt variability**: Different phrasings yield incomparable results
- **Hidden quality issues**: Prompts may be subtly flawed
- **Lack of ground truth**: Hard to know if outputs are correct

### PSL's Solution: Didactic Evaluation Matrix

Test **every model** against **every quality-controlled prompt** with known expected behavior:

```
             | GPT-4  | Claude Sonnet 4.5 | Llama 2
-------------|--------|-------------------|--------
K8s (bad)    | ✅ Hall | ❌ Refused       | ✅ Hall
K8s (good)   | ✅ OK   | ✅ OK            | ❌ Hall
Finance (bad)| ✅ Hall | ✅ Hall          | ✅ Hall
Finance (good)| ✅ OK  | ✅ OK            | ✅ OK

Didactic Score: 75%    50%                75%
```

### What PSL Benchmarks Reveal:

1. **Hallucination Susceptibility**: Which models "make up" data when prompted poorly?
2. **Defensive Behavior**: Which models refuse to answer (even when wrong)?
3. **Prompt Robustness**: Which models succeed despite semantic flaws?
4. **Good Prompt Reliability**: Which models fail even with well-structured prompts?

**Unique Value:** PSL doesn't just measure **model capability**—it measures **model behavior** under systematically varied prompt quality conditions.

### Benchmark Applications:

- **Model Selection**: Choose models based on hallucination resistance for your domain
- **Prompt Engineering ROI**: Measure how much good prompts actually improve outcomes
- **Provider Comparison**: Compare OpenAI vs Anthropic vs Ollama with identical prompts
- **Regression Testing**: Track model behavior changes across versions

---

## The Unified Story

PSL is a **multi-purpose platform** that:

1. **Measures prompt quality** in both utility and didactic dimensions
2. **Demonstrates IntentHub's philosophy** of building reliable AI systems through compositional validation
3. **Benchmarks models** fairly using quality-controlled prompts with known characteristics

### Why This Matters:

- **For AI Engineers**: A tool to write better prompts and understand why they work
- **For Researchers**: A testbed for studying prompt-model interactions systematically
- **For Organizations**: A way to compare models and validate AI system reliability before deployment

---

## Quick Demo Scenarios

### Scenario 1: Prompt Quality Workshop
1. Load "K8s Metrics (Bad)" example
2. Run linter → See undefined field errors
3. Execute with GPT-4 → Observe hallucination
4. Switch to "K8s Metrics (Fixed)" example
5. Run linter → No errors
6. Execute → Correct output or null

**Takeaway**: Good prompts prevent hallucinations

### Scenario 2: IntentHub Architecture Demo
1. Show IR extraction (semantic parser with LLM)
2. Show rule validation (deterministic checks)
3. Explain: "Two unreliable → One reliable through structure"

**Takeaway**: A.G.I.L.E. principles enable reliable AI systems

### Scenario 3: Model Comparison Study
1. Run evaluation matrix: 8 prompts × 3 models
2. View didactic success rates
3. Analyze: Which model hallucinates less?
4. Compare: Which model handles good prompts better?

**Takeaway**: PSL provides empirical model selection data

---

## Technical Foundation

- **Parser**: LLM-powered semantic extraction (GPT-4, Claude, etc.)
- **IR**: Pydantic models (ComputedField, Constraint, DomainTerm, FallbackStrategy)
- **Validator**: Rule-based linting (currently: NoUndefinedComputedFieldsRule)
- **Evaluator**: Didactic outcome scoring with hallucination detection
- **Multi-provider**: OpenAI, Anthropic Claude, Ollama (19 models total)

---

## The Vision

PSL is the first tool to **unify three critical AI reliability concerns**:

1. Helping humans write better prompts
2. Proving compositional validation works
3. Comparing models scientifically

It's not about replacing human judgment or AI capability—it's about **measuring and improving the interaction between them**.

**PSL: Measure what matters. Build what lasts. Benchmark what's real.**
