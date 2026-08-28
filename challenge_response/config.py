import os

CHALLENGE_RESPONSE_ENABLED = os.getenv("CHALLENGE_RESPONSE_ENABLED", "true").lower() == "true"
CHALLENGE_RESPONSE_TTL_MINUTES = int(os.getenv("CHALLENGE_RESPONSE_TTL_MINUTES", "3"))
CHALLENGE_RESPONSE_MAX_ATTEMPTS = int(os.getenv("CHALLENGE_RESPONSE_MAX_ATTEMPTS", "3"))
CHALLENGE_RESPONSE_RISK_THRESHOLD = float(os.getenv("CHALLENGE_RESPONSE_RISK_THRESHOLD", "0.40"))

DEFAULT_CHALLENGE_COLORS = (
    "blue",
    "green",
    "red",
    "yellow",
    "orange",
    "purple",
    "silver",
    "black",
    "white",
    "gold",
)

DEFAULT_CHALLENGE_WORDS = (
    "apple",
    "tiger",
    "river",
    "mango",
    "lighthouse",
    "signal",
    "harbor",
    "orbit",
    "cabin",
    "summit",
    "planet",
    "verve",
    "forest",
    "silver",
    "stone",
    "marble",
    "shadow",
    "ember",
    "meteor",
    "copper",
)
