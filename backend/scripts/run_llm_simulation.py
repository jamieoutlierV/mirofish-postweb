"""
LLM-Powered Swarm Simulation Engine (OASIS-free)

Replaces the OASIS social simulation with direct LLM-driven agent interactions.
Uses the same agent profiles and config, but orchestrates via Claude/OpenAI API
instead of the camel-oasis framework.

Produces actions.jsonl in the same format as OASIS for compatibility with
the MiroFish report generator.
"""

import argparse
import json
import os
import sys
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


class LLMSimulationEngine:
    """Runs a multi-agent swarm simulation using LLM-generated interactions."""

    REDDIT_ACTIONS = [
        "CREATE_POST", "CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST",
        "LIKE_COMMENT", "DO_NOTHING"
    ]
    TWITTER_ACTIONS = [
        "CREATE_POST", "LIKE_POST", "REPOST", "QUOTE_POST",
        "FOLLOW", "DO_NOTHING"
    ]

    def __init__(self, config_path: str, max_rounds: Optional[int] = None):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.sim_dir = os.path.dirname(config_path)
        self.max_rounds = max_rounds or self.config.get("max_rounds", 10)
        self.is_anthropic = 'anthropic' in os.environ.get('LLM_BASE_URL', '').lower()

        self.client = OpenAI(
            api_key=os.environ.get("LLM_API_KEY"),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

        # Load agent profiles
        self.profiles = self._load_profiles()
        log(f"Loaded {len(self.profiles)} agent profiles")

        # Track simulation state
        self.posts = []  # All posts created during simulation
        self.round_summaries = []

    def _load_profiles(self) -> List[Dict[str, Any]]:
        """Load agent profiles from reddit_profiles.json or twitter_profiles.csv"""
        reddit_path = os.path.join(self.sim_dir, "reddit_profiles.json")
        if os.path.exists(reddit_path):
            with open(reddit_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        twitter_path = os.path.join(self.sim_dir, "twitter_profiles.csv")
        if os.path.exists(twitter_path):
            import csv
            profiles = []
            with open(twitter_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    profiles.append(row)
            return profiles

        return []

    def _call_llm(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call LLM with Anthropic compatibility."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        # Don't send response_format for Anthropic
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _call_llm_json(self, messages: List[Dict], temperature: float = 0.3) -> Dict:
        """Call LLM and parse JSON response."""
        import re
        # Add JSON instruction for Anthropic
        if self.is_anthropic and messages:
            if messages[0].get("role") == "system":
                messages[0]["content"] += "\nIMPORTANT: Respond with valid JSON only. No markdown, no explanation."
            else:
                messages.insert(0, {"role": "system", "content": "Respond with valid JSON only."})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if not self.is_anthropic:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content.strip()
        content = re.sub(r'^```(?:json)?\s*\n?', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\n?```\s*$', '', content)
        return json.loads(content.strip())

    def _generate_round_actions(self, round_num: int, platform: str) -> List[Dict]:
        """Generate actions for all agents in a single round using batch LLM call."""
        actions_list = self.TWITTER_ACTIONS if platform == "twitter" else self.REDDIT_ACTIONS

        # Build context: recent posts and round history
        recent_posts = self.posts[-20:] if self.posts else []
        posts_context = "\n".join([
            f"- [{p['agent_name']}]: {p['content'][:150]}"
            for p in recent_posts
        ]) if recent_posts else "No posts yet — this is the start of the simulation."

        round_context = "\n".join(self.round_summaries[-3:]) if self.round_summaries else ""

        # Select a subset of agents to act this round (realistic — not everyone acts every round)
        active_count = max(3, len(self.profiles) // 3)
        active_agents = random.sample(self.profiles, min(active_count, len(self.profiles)))

        agent_descriptions = []
        for i, agent in enumerate(active_agents):
            name = agent.get("agent_name", agent.get("username", f"Agent_{i}"))
            bio = agent.get("bio", agent.get("persona", ""))[:200]
            agent_descriptions.append(f"Agent {i} ({name}): {bio}")

        prompt = f"""You are simulating a multi-agent social environment on {platform}.

Round {round_num}/{self.max_rounds} of the simulation.

SIMULATION CONTEXT:
{self.config.get('simulation_description', self.config.get('description', 'Social simulation'))}

ACTIVE AGENTS THIS ROUND:
{chr(10).join(agent_descriptions)}

RECENT ACTIVITY:
{posts_context}

{f"PREVIOUS ROUND SUMMARIES:{chr(10)}{round_context}" if round_context else ""}

Available actions: {', '.join(actions_list)}

For each active agent, generate 1-2 realistic actions they would take this round.
Actions should reflect the agent's persona, beliefs, and the evolving social dynamics.
CREATE_POST actions must include realistic post content.
LIKE_POST/REPOST/QUOTE_POST should reference existing posts when possible.

Return JSON with format:
{{
  "actions": [
    {{
      "agent_index": 0,
      "action_type": "CREATE_POST",
      "content": "Post content here...",
      "reasoning": "Brief reason for this action"
    }},
    {{
      "agent_index": 1,
      "action_type": "LIKE_POST",
      "target_post_index": 0,
      "reasoning": "Brief reason"
    }}
  ],
  "round_summary": "Brief summary of what happened this round"
}}"""

        try:
            result = self._call_llm_json([
                {"role": "system", "content": "You are a swarm intelligence simulation engine. Generate realistic multi-agent social interactions."},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            log(f"  LLM error in round {round_num}: {e}")
            # Generate fallback actions
            result = {
                "actions": [{"agent_index": 0, "action_type": "DO_NOTHING", "reasoning": "Error fallback"}],
                "round_summary": f"Round {round_num}: Limited activity due to processing error."
            }

        # Convert to MiroFish action format
        formatted_actions = []
        now = datetime.now().isoformat()

        for action in result.get("actions", []):
            agent_idx = action.get("agent_index", 0)
            if agent_idx >= len(active_agents):
                agent_idx = 0
            agent = active_agents[agent_idx]
            agent_name = agent.get("agent_name", agent.get("username", f"Agent_{agent_idx}"))

            action_record = {
                "round": round_num,
                "timestamp": now,
                "platform": platform,
                "agent_id": agent_idx,
                "agent_name": agent_name,
                "action_type": action.get("action_type", "DO_NOTHING"),
                "action_args": {},
                "success": True,
                "result": action.get("reasoning", "")
            }

            # Handle content for CREATE_POST
            if action.get("action_type") == "CREATE_POST" and action.get("content"):
                action_record["action_args"] = {"content": action["content"]}
                self.posts.append({
                    "agent_name": agent_name,
                    "content": action["content"],
                    "round": round_num,
                    "platform": platform
                })
            elif action.get("action_type") in ["LIKE_POST", "REPOST", "QUOTE_POST"]:
                target = action.get("target_post_index", 0)
                action_record["action_args"] = {"post_id": target}
                if action.get("action_type") == "QUOTE_POST" and action.get("content"):
                    action_record["action_args"]["content"] = action["content"]

            formatted_actions.append(action_record)

        # Store round summary
        summary = result.get("round_summary", f"Round {round_num} completed.")
        self.round_summaries.append(f"Round {round_num}: {summary}")

        return formatted_actions

    def run(self):
        """Run the full simulation."""
        log(f"Starting LLM-powered simulation: {self.max_rounds} rounds, {len(self.profiles)} agents")

        # Create platform directories
        for platform in ["twitter", "reddit"]:
            platform_dir = os.path.join(self.sim_dir, platform)
            os.makedirs(platform_dir, exist_ok=True)

        # Write simulation_start event
        for platform in ["twitter", "reddit"]:
            actions_path = os.path.join(self.sim_dir, platform, "actions.jsonl")
            with open(actions_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps({
                    "event_type": "simulation_start",
                    "timestamp": datetime.now().isoformat(),
                    "total_agents": len(self.profiles),
                    "max_rounds": self.max_rounds
                }, ensure_ascii=False) + "\n")

        # Update state.json
        state_path = os.path.join(self.sim_dir, "state.json")
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            state["status"] = "running"
            state["updated_at"] = datetime.now().isoformat()
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        # Run rounds
        for round_num in range(1, self.max_rounds + 1):
            log(f"Round {round_num}/{self.max_rounds}")

            for platform in ["twitter", "reddit"]:
                actions_path = os.path.join(self.sim_dir, platform, "actions.jsonl")

                # Write round_start event
                with open(actions_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "event_type": "round_start",
                        "round": round_num,
                        "timestamp": datetime.now().isoformat()
                    }, ensure_ascii=False) + "\n")

                # Generate and write actions
                actions = self._generate_round_actions(round_num, platform)
                with open(actions_path, 'a', encoding='utf-8') as f:
                    for action in actions:
                        f.write(json.dumps(action, ensure_ascii=False) + "\n")

                # Write round_end event
                with open(actions_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "event_type": "round_end",
                        "round": round_num,
                        "timestamp": datetime.now().isoformat()
                    }, ensure_ascii=False) + "\n")

                log(f"  {platform}: {len(actions)} actions generated")

            # Small delay between rounds to avoid rate limits
            time.sleep(1)

        # Write simulation_end event
        for platform in ["twitter", "reddit"]:
            actions_path = os.path.join(self.sim_dir, platform, "actions.jsonl")
            with open(actions_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "event_type": "simulation_end",
                    "timestamp": datetime.now().isoformat(),
                    "total_rounds": self.max_rounds
                }, ensure_ascii=False) + "\n")

        # Update state.json to completed
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            state["status"] = "completed"
            state["current_round"] = self.max_rounds
            state["updated_at"] = datetime.now().isoformat()
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        log(f"Simulation complete. {len(self.posts)} total posts generated across {self.max_rounds} rounds.")


def main():
    parser = argparse.ArgumentParser(description="LLM-Powered Swarm Simulation")
    parser.add_argument("--config", required=True, help="Path to simulation_config.json")
    parser.add_argument("--max-rounds", type=int, default=None, help="Override max rounds")
    args = parser.parse_args()

    engine = LLMSimulationEngine(config_path=args.config, max_rounds=args.max_rounds)
    engine.run()


if __name__ == "__main__":
    main()
