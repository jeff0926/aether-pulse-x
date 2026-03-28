# config.py
import os
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ZENODO_URL = os.getenv("ZENODO_URL", "https://zenodo.org/records/19212829")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/jeff0926/aether")
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.65"))
MAX_DRAFTS_PER_DAY = int(os.getenv("MAX_DRAFTS_PER_DAY", "3"))
RUN_INTERVAL_HOURS = int(os.getenv("RUN_INTERVAL_HOURS", "6"))

# Apify actor ID for Tweet Scraper V2
APIFY_ACTOR_ID = "61RPP7dywgiy0JPD0"

# Keywords to monitor
KEYWORDS = [
    '"AI agents" min_faves:50 lang:en -filter:retweets',
    '"agentic AI" min_faves:50 lang:en -filter:retweets',
    '".claude/agents" min_faves:50 lang:en',
    '"SKILL.md" min_faves:50 lang:en',
    '"agent framework" min_faves:50 lang:en -filter:retweets',
    '"LLM verification" min_faves:50 lang:en',
    '"agent harness" min_faves:50 lang:en',
    '"building agents" min_faves:50 lang:en -filter:retweets',
    '"microservice" "agents" min_faves:50 lang:en',
    '"prompt wrapper" min_faves:50 lang:en'
]

# Proof points for reply drafts — verified facts only
PROOF_POINTS = {
    "score_improvement": "0.143 → 0.889",
    "human_intervention": "zero human intervention",
    "verification_speed": "sub-millisecond verification",
    "tech_stack": "no embeddings, no vector DB",
    "tagline": "The model didn't change. The skill did.",
    "thesis": "Intelligence is intrinsic to the system, not the model.",
    "zenodo": ZENODO_URL
}

# Recency threshold — posts older than this get score penalty
RECENCY_HOURS_THRESHOLD = 48

# Power words — every reply must contain at least one
POWER_WORDS = [
    "self-healing",
    "self-educating",
    "self-verifying",
    "portable",
    "verified",
    "intrinsic",
    "capsule",
    "grounded"
]

# Taglines — close every reply with one of these
TAGLINES = [
    "The model didn't change. The skill did.",
    "Intelligence is intrinsic to the system, not the model.",
    "Most systems are toolchains. This is an organization.",
    "Agents aren't wrappers. They're roles. The difference is knowledge.",
    "The model is replaceable. The expertise is not.",
    "The system is the product. The proof is in production."
]

# Gap signals — phrases that indicate missing verification/education
GAP_SIGNALS = [
    "flat markdown",
    "prompt wrapper",
    "tool router",
    "microservice",
    "agent harness",
    "fragmented context",
    "scattered skills",
    "hallucin",
    "no memory",
    "fails",
    "unreliable",
    "stateless",
    "chaining",
    "orchestrat",
    "middleware",
    "no verification",
    "no learning",
    "stale"
]

# Technical depth signals
TECH_SIGNALS = [
    "architecture",
    "framework",
    "pipeline",
    "knowledge graph",
    "verification",
    "grounding",
    "self-educat",
    "self-heal",
    "capsule",
    "agent",
    "skill",
    "LLM",
    "reasoning"
]
