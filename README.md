# MiroFish × Post-Web Simulations

Swarm intelligence simulations exploring the [Post-Web](https://postweb.io) transition using [MiroFish](https://github.com/666ghj/MiroFish) — an open-source multi-agent prediction engine that spawns thousands of AI agents with independent personalities, memory, and behavioural logic to simulate social dynamics.

## Three Simulations

| Simulation | Question | Path |
|---|---|---|
| **Token Adaptation** | How do existing token economies transition from speculation to conviction? | `simulations/token-adaptation/` |
| **Zero to Many** | How do new Post-Web-native systems scale using constitutional design? | `simulations/zero-to-many/` |
| **Firm Decomposition** | How do firms decompose themselves before agents do it for them? | `simulations/firm-decomposition/` |

Based on [Pathways to the Post-Web](https://outlierventures.io/publications/pathways-to-the-post-web) by [Outlier Ventures](https://outlierventures.io) (Jamie Burke). Source material includes the Post-Web thesis, [Conviction Markets](https://conviction.outlierventures.io), and the OV System State.

## Quick Start

```bash
# Clone and configure
git clone https://github.com/jamieoutlierV/mirofish-postweb.git
cd mirofish-postweb
cp simulations/.env.example .env  # Add your LLM + Zep keys

# Install and run MiroFish
npm run setup:all
npm run dev
```

Then upload any seed document from `simulations/` via the UI at `http://localhost:3000`, or use the API directly. See [`simulations/README.md`](simulations/README.md) for detailed instructions.

## Prerequisites

- Node.js 18+
- Python 3.11+
- LLM API key (any OpenAI SDK-compatible endpoint)
- [Zep Cloud](https://app.getzep.com/) API key (free tier works)

## What This Is

A research tool for stress-testing the Post-Web thesis through emergent multi-agent social simulation. Not prediction — scenario exploration. MiroFish builds a digital sandbox where thousands of agents with different perspectives debate, influence each other, and form coalitions around these questions. The value is in the emergent patterns, not precise forecasts.

## License

Simulation seed documents: CC-BY-4.0 (Outlier Ventures / Jamie Burke)
MiroFish engine: AGPL-3.0 (original MiroFish license)
