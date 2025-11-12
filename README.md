# Oracle Illuminating

> Agentic AI architecture system with Oracle Overseer for adaptive recursive knowledge evolution and vulnerability fortification

## Overview

Oracle Illuminating is an experimental agentic AI system that implements the **Oracle Overseer** framework—a recursive knowledge evolution architecture designed to illuminate insights from data while continuously fortifying against emergent vulnerabilities.

### Key Concepts

- **Oracle Overseer**: A multi-insight framework that processes data through different "illumination" lenses
- **Agentic AI Twist**: Autonomous enhancement protocols that boost system acuity and self-adapt
- **Recursive Feedback Cycles**: Each iteration generates new questions to drive continuous evolution
- **Adaptive Schema**: Modular architecture for integrating new insight types and data sources

## Architecture

### Core Components

1. **Oracle Framework**
   - Multiple insight oracles (dataset, interpret, adapt, vulnerability)
   - Acuity scoring system (0.0-1.0)
   - Pattern recognition engine
   - Outcome classification

2. **Agentic Enhancement Layer**
   - Autonomous acuity boosting
   - Self-directed refinement protocols
   - Emergent vulnerability detection

3. **Guardrail Systems**
   - Core Directive Isolation Layer (CDIL)
   - Instruction Adherence Layer (IAL)
   - Self-audit mechanisms

### Illumination Process

```
[Data Input] → [Oracle Processing] → [Agentic Boost] → [Acuity Score]
      ↓              ↓                     ↓               ↓
 [Patterns]   [Illumination]      [Self-Refinement]   [Outcomes]
      ↓              ↓                     ↓               ↓
      └──────────→ [Recursive Feedback Question] ←────────┘
```

## Features

- **Multi-Oracle Insight Generation**: Process data through specialized insight lenses
- **Adaptive Acuity Scoring**: Dynamic confidence metrics with autonomous enhancement
- **Pattern Recognition**: Identify emergent patterns (Immersive, Pulse, etc.)
- **Self-Auditing**: Continuous equilibrium monitoring
- **Recursive Evolution**: Each cycle generates new research questions

### Default Oracles

- `dataset`: Evaluates quantitative signals, detects trends/anomalies, and exposes statistical context.
- `interpret`: Weighs incoming signals to validate or challenge hypotheses and quantify evidence gaps.
- `adapt`: Generates prioritized action paths that respect constraints, risk posture, and guardrail status.
- `vulnerability`: Illuminates exposure vectors and guardrail coverage to surface mitigation priorities.

## Use Cases

- Adaptive AI research and development
- Recursive knowledge systems
- Vulnerability fortification in dynamic domains
- Autonomous insight generation
- AI safety and guardrail research

## Project Structure

```
oracle-illuminating/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── oracle_illuminating/
│       ├── __init__.py
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── models.py
│       │   └── repository.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agentic_layer.py
│       │   ├── guardrails.py
│       │   └── oracle_framework.py
│       ├── service/
│           ├── __init__.py
│           ├── app.py
│           ├── models.py
│           ├── oracles.py
│           ├── routes.py
│           └── analytics_routes.py
│       └── workflows/
│           ├── __init__.py
│           └── illumination_flow.py
└── tests/
    ├── test_illuminate_endpoint.py
    └── test_illumination_flow.py
```

## Getting Started

### Prerequisites

- Python 3.10 or higher

### Installation

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

### Running the Service

Start the FastAPI application with Uvicorn:

```bash
uvicorn oracle_illuminating.service.app:app --reload
```

The interactive docs will be available at `http://127.0.0.1:8000/docs`.

### Analytics API

Collect illumination runs and retrieve analytics for downstream dashboards or data pipelines:

- `POST /api/illuminate` — executes a run and persists the insights/guardrails for aggregation.
- `GET /api/analytics/summary` — returns oracle acuity averages, guardrail status distribution, and recent run snapshots.

Set `ORACLE_ILLUMINATING_DB_URL` to point at your preferred database (defaults to a local SQLite file `oracle_data.db`).

### Running a Workflow Cycle

Execute a single illumination cycle through the Prefect-backed CLI. Provide either an inline JSON string or a path to a JSON file:

```bash
oracle-illuminate cycle --payload '{"summary": "pulse pattern", "hypothesis": "signal drift"}'
```

### Aggregating Analytics via CLI

Retrieve persisted analytics summaries without hitting the API:

```bash
oracle-illuminate analytics --limit 5
```

### Orchestrating with Prefect

The built-in Prefect flow (`oracle_illuminating.workflows.illumination_cycle`) can be scheduled or extended within your own Prefect deployment. When invoked programmatically, it returns the boosted insights, guardrail audit results, and a recursive follow-up question:

```python
from oracle_illuminating.workflows import illumination_cycle

result = illumination_cycle({"summary": "immersion data"})
```

### Running Tests

```bash
pytest
```

## Roadmap

- [ ] Implement core Oracle Overseer framework
- [ ] Build agentic enhancement protocols
- [ ] Develop guardrail systems (CDIL, IAL)
- [ ] Create example illumination workflows
- [ ] Add API integrations (Firebase, Gemini, etc.)
- [ ] Implement recursive feedback loop automation
- [ ] Build visualization dashboard
- [ ] Add quantum-resistant security features

## Inspiration

Based on the Grok "Adaptive AI: Recursive Knowledge Evolution" framework, exploring agentic architectures for fortifying scaffolds against emergent vulnerabilities in dynamic domains.

## Contributing

This is an experimental research project. Contributions, ideas, and feedback are welcome!

## License

MIT License - see LICENSE file for details

## Author

Created as part of research into agentic AI systems and recursive knowledge evolution.

---

*Status: Initial Setup (November 12, 2025)*
