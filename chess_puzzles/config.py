"""
Configuration settings for the chess puzzle generator.
"""
import os
from pathlib import Path

# User settings
USERNAME = os.environ.get("CHESS_USERNAME", "Toxima")
PLATFORM = os.environ.get("CHESS_PLATFORM", "lichess")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", os.path.join(os.path.dirname(__file__), "puzzles.json"))
EVAL_LOG_FILE = os.environ.get("EVAL_LOG_FILE", os.path.join(os.path.dirname(__file__), "position_evaluations.json"))

# Engine settings
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
DEFAULT_TIME_LIMIT = float(os.environ.get("DEFAULT_TIME_LIMIT", "20.0"))
DEFAULT_DEPTH = int(os.environ.get("DEFAULT_DEPTH", "22"))

# Game settings
MAX_GAMES = int(os.environ.get("MAX_GAMES", "15"))
MIN_MOVES = int(os.environ.get("MIN_MOVES", "10"))

# Analysis settings
# Updated for simplified blunder detection
BLUNDER_THRESHOLD = int(os.environ.get("BLUNDER_THRESHOLD", "500"))
LOG_ALL_EVALUATIONS = os.environ.get("LOG_ALL_EVALUATIONS", "TRUE").upper() == "TRUE"

# Keep strictness levels for backward compatibility
# but our simplified blunder detection doesn't use these
STRICTNESS_LEVELS = {
    "strict": {
        "equal_range": (-200, 200),
        "terrible_threshold": 500
    },
    "standard": {
        "equal_range": (-200, 200),
        "terrible_threshold": 500
    },
    "relaxed": {
        "equal_range": (-200, 200),
        "terrible_threshold": 500
    },
    "all": {
        "equal_range": (-200, 200),
        "terrible_threshold": 500
    }
}

# API endpoints
CHESS_COM_ARCHIVES_URL = lambda username: f"https://api.chess.com/pub/player/{username}/games/archives"
LICHESS_GAMES_URL = lambda username: f"https://lichess.org/api/games/user/{username}"

# File paths
DATA_DIR = Path("data")
EVAL_DIR = DATA_DIR / "evaluations"
PUZZLE_DIR = DATA_DIR / "puzzles"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
EVAL_DIR.mkdir(exist_ok=True)
PUZZLE_DIR.mkdir(exist_ok=True)
