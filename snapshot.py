# snapshot.py
# =============================================================================
# Snapshot and URL modes for aether-pulse-x
# =============================================================================
# Process screenshots of papers/posts or URLs to generate draft replies.
# =============================================================================

import base64
import urllib.request
from pathlib import Path
import anthropic
from config import ANTHROPIC_API_KEY, ZENODO_URL, POWER_WORDS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SNAPSHOT_SYSTEM_PROMPT = """You are analyzing a research paper or social media post screenshot
on behalf of Jeff Conn, founder of 864 Zeros LLC and creator of AETHER.

Your job:
1. Extract the key claims or problem statements from the image
2. Identify which specific claim or gap AETHER addresses
3. Draft a reply or standalone post in Jeff's voice

Jeff's voice: direct, technical, kind, curious. Never promotional.

AETHER key facts (verified — never fabricate):
- Any .md file becomes a self-verifying, self-educating agent capsule
- Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention
- 17 knowledge triples acquired autonomously
- Sub-millisecond verification. No embeddings. No vector DB. No GPU.
- 15 Python files, stdlib only, zero framework dependencies
- Intelligence is intrinsic to the system, not the model.
- The model didn't change. The skill did.
- Paper: {zenodo_url}

Power words to use: self-healing, self-educating, self-verifying, portable, verified, intrinsic, capsule, grounded

Output format (use exactly these labels):
CLAIM: [the specific claim or problem from the image]
GAP: [what's missing that AETHER addresses]
DRAFT: [the reply or post — under 280 chars including URL counted as 23 chars]
TYPE: [reply or standalone]
""".format(zenodo_url=ZENODO_URL)


def process_snapshot(image_path):
    """
    Process a screenshot or image and generate a draft post.
    Returns dict with claim, gap, draft, and type.
    """
    image_data = Path(image_path).read_bytes()
    base64_image = base64.standard_b64encode(image_data).decode('utf-8')

    # Detect media type
    suffix = Path(image_path).suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'image/jpeg')

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SNAPSHOT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_image
                    }
                },
                {
                    "type": "text",
                    "text": "Analyze this image and produce a CLAIM, GAP, DRAFT, and TYPE."
                }
            ]
        }]
    )

    response = message.content[0].text
    return parse_snapshot_response(response)


def parse_snapshot_response(response):
    """Parse the structured response from Claude."""
    result = {}
    for line in response.split('\n'):
        for key in ['CLAIM', 'GAP', 'DRAFT', 'TYPE']:
            if line.strip().startswith(f'{key}:'):
                result[key.lower()] = line.split(':', 1)[1].strip()
    return result


def process_url(url):
    """
    Fetch a URL and generate a draft post.
    Uses web fetch to get content then processes like snapshot.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; AETHER-Pulse/1.1)'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')[:8000]  # First 8000 chars
    except Exception as e:
        return {"error": str(e)}

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SNAPSHOT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this content and produce a CLAIM, GAP, DRAFT, and TYPE:\n\n{content}"
        }]
    )

    return parse_snapshot_response(message.content[0].text)
