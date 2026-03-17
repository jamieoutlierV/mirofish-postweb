# Post-Web Swarm Simulations

Three MiroFish swarm intelligence simulations exploring the Post-Web transition — how token economies adapt, how new systems scale, and how firms decompose themselves.

Based on the [Post-Web thesis](https://postweb.io) by [Outlier Ventures](https://outlierventures.io) (Jamie Burke).

## Simulations

### A. Token Economy Adaptation (`token-adaptation/`)
How do existing crypto token economies — DeFi protocols, L1 chains, DAOs — transition from speculation-driven attention economy instruments to Post-Web conviction-based coordination mechanisms? What happens to communities, liquidity, and network effects during the transition?

### B. Zero to Many (`zero-to-many/`)
How do new Post-Web-native systems scale using the "Systems Not Startups" grammar, constitutional design, and the 100x founder model? How does conviction-based financing compare to venture capital? What happens to traditional startups that don't adopt the paradigm?

### C. Firm Decomposition (`firm-decomposition/`)
How do firms and institutions decompose themselves into machine-readable primitives (knowledge graphs, skills, processes) before AI agents do it without consent? Based on Outlier Ventures' own 24-month decomposition from 100 staff to 10 humans orchestrating an agentic system.

## Running a Simulation

### Prerequisites
- MiroFish running locally or via Docker (see root README)
- LLM API key (OpenAI-compatible endpoint)
- Zep Cloud API key (free tier works)

### Steps

Each simulation has a `seed.md` (the input document) and a `config.json` (the simulation parameters).

**1. Upload the seed document and generate the ontology**

```bash
curl -X POST http://localhost:5001/api/graph/ontology/generate \
  -F "files=@simulations/token-adaptation/seed.md" \
  -F "simulation_requirement=$(jq -r .simulation_requirement simulations/token-adaptation/config.json)" \
  -F "project_name=$(jq -r .project_name simulations/token-adaptation/config.json)" \
  -F "additional_context=$(jq -r .additional_context simulations/token-adaptation/config.json)"
```

This returns a `project_id` and the generated ontology (entity types and relationship types).

**2. Build the knowledge graph**

```bash
curl -X POST http://localhost:5001/api/graph/build \
  -H "Content-Type: application/json" \
  -d '{"project_id": "YOUR_PROJECT_ID"}'
```

Poll `/api/graph/task/YOUR_TASK_ID` for progress. The graph is built asynchronously in Zep.

**3. Prepare and run the simulation**

```bash
# Prepare simulation (reads entities from graph, generates agent profiles)
curl -X POST http://localhost:5001/api/simulation/prepare \
  -H "Content-Type: application/json" \
  -d '{"project_id": "YOUR_PROJECT_ID"}'

# Start simulation (runs parallel social simulations)
curl -X POST http://localhost:5001/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "YOUR_SIMULATION_ID"}'
```

**4. Generate the prediction report**

```bash
curl -X POST http://localhost:5001/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "YOUR_SIMULATION_ID"}'
```

**5. Interact with the results**

```bash
# Chat with the Report Agent about findings
curl -X POST http://localhost:5001/api/report/chat \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "YOUR_SIMULATION_ID", "message": "What coalitions formed around conviction-based tokens?"}'
```

Or use the Vue.js frontend at `http://localhost:3000`.

## What to Look For

### Token Adaptation
- Resistance patterns from speculation-dependent holders
- Coalition formation between builders and long-term holders
- Speed at which AI agents preference conviction-weighted protocols
- Whether market bifurcation emerges (attention tokens vs intention tokens)

### Zero to Many
- Whether constitutional design quality predicts success better than execution speed
- Agent-mediated discovery dynamics (winner-take-most vs composable long tail)
- Founder gig economy self-organisation patterns
- Constitutional failure modes (extractive tokens, prescriptive traces, premature token launch)

### Firm Decomposition
- Optimal decomposition sequencing (knowledge → skills → processes?)
- Relationship between institutional age and decomposition difficulty
- How fast agents approximate undecomposed institutions
- Social dynamics of staff reduction — resistance, talent migration, coalition formation
- Whether radical openness creates power-user advantage or accelerates commoditisation

## Configuration

Copy `simulations/.env.example` to `.env` in the project root. See the main MiroFish README for full setup instructions.
