import chess
import chess.pgn
import chess.engine
import requests
import json
import io
from datetime import datetime
import os
import sys
import tempfile
import subprocess

# Configuration (can be overridden with environment variables)
USERNAME = os.environ.get("CHESS_USERNAME", "Toxima1")
PLATFORM = os.environ.get("CHESS_PLATFORM", "chess.com")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "puzzles.json")
MAX_GAMES = int(os.environ.get("MAX_GAMES", "5"))
BLUNDER_THRESHOLD = int(os.environ.get("BLUNDER_THRESHOLD", "150"))

# Chess.com API endpoints
CHESS_COM_ARCHIVES_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
# Lichess API endpoint
LICHESS_GAMES_URL = f"https://lichess.org/api/games/user/{USERNAME}"

def download_stockfish():
    """Download and prepare Stockfish for the current platform"""
    print("Downloading Stockfish...")
    stockfish_path = os.path.join(tempfile.gettempdir(), "stockfish")
    
    if sys.platform == "linux" or sys.platform == "linux2":
        # Linux - download Stockfish 16
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar.gz"
        subprocess.run(["wget", url, "-O", "stockfish.tar.gz"], check=True)
        subprocess.run(["tar", "-xzf", "stockfish.tar.gz"], check=True)
        subprocess.run(["mv", "stockfish/stockfish-ubuntu-x86-64-avx2", stockfish_path], check=True)
        subprocess.run(["chmod", "+x", stockfish_path], check=True)
    elif sys.platform == "darwin":
        # macOS - download Stockfish 16
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-macos-x86-64-avx2.tar.gz"
        subprocess.run(["curl", "-L", url, "-o", "stockfish.tar.gz"], check=True)
        subprocess.run(["tar", "-xzf", "stockfish.tar.gz"], check=True)
        subprocess.run(["mv", "stockfish/stockfish-macos-x86-64-avx2", stockfish_path], check=True)
        subprocess.run(["chmod", "+x", stockfish_path], check=True)
    elif sys.platform == "win32":
        # Windows - download Stockfish 16
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-windows-x86-64-avx2.zip"
        subprocess.run(["curl", "-L", url, "-o", "stockfish.zip"], check=True)
        subprocess.run(["unzip", "stockfish.zip"], check=True)
        stockfish_path = os.path.join(tempfile.gettempdir(), "stockfish.exe")
        subprocess.run(["mv", "stockfish/stockfish-windows-x86-64-avx2.exe", stockfish_path], check=True)

    print(f"Stockfish downloaded to {stockfish_path}")
    return stockfish_path

def fetch_chess_com_games(limit=MAX_GAMES):
    """Fetch recent games from Chess.com"""
    try:
        # Get archives (monthly game collections)
        archives_response = requests.get(CHESS_COM_ARCHIVES_URL)
        archives_response.raise_for_status()
        archives = archives_response.json().get("archives", [])
        
        if not archives:
            return []
        
        # Get games from the most recent archive
        recent_archive = archives[-1]
        games_response = requests.get(recent_archive)
        games_response.raise_for_status()
        
        games = games_response.json().get("games", [])
        return games[:limit]
    except Exception as e:
        print(f"Error fetching Chess.com games: {e}")
        return []

def fetch_lichess_games(limit=MAX_GAMES):
    """Fetch recent games from Lichess.org"""
    try:
        params = {"max": limit, "pgnInJson": "true"}
        response = requests.get(LICHESS_GAMES_URL, params=params)
        response.raise_for_status()
        
        # Parse NDJSON (each line is a JSON object)
        games = [json.loads(line) for line in response.text.split('\n') if line]
        return games
    except Exception as e:
        print(f"Error fetching Lichess games: {e}")
        return []

def get_pgn_from_game(game, platform):
    """Extract PGN from a game object based on platform"""
    if platform == "chess.com":
        return game.get("pgn", "")
    elif platform == "lichess":
        return game.get("pgn", "")
    return ""

def analyze_game(pgn_text, stockfish_path):
    """Analyze a game to find blunders"""
    # Parse PGN
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    if not game:
        return []
    
    blunders = []
    board = game.board()
    
    # Initialize Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    try:
        # Process each move
        node = game.next()
        move_number = 1
        
        while node:
            # Get position before the move
            prev_fen = board.fen()
            prev_eval = engine.analyse(board, chess.engine.Limit(time=0.1))["score"].relative.score(mate_score=10000)
            
            # Make the move
            move = node.move
            san_move = board.san(move)
            board.push(move)
            
            # Evaluate new position
            curr_eval = -engine.analyse(board, chess.engine.Limit(time=0.1))["score"].relative.score(mate_score=10000)
            
            # Calculate evaluation change
            eval_change = prev_eval - curr_eval
            
            # Check if move is a blunder
            if eval_change >= BLUNDER_THRESHOLD:
                player = "white" if board.turn == chess.BLACK else "black"
                blunder = {
                    "fen": prev_fen,
                    "solution": [move.uci()],
                    "player_color": player,
                    "move_number": move_number,
                    "blundered_move": san_move,
                    "eval_change": eval_change,
                    "difficulty": calculate_difficulty(eval_change)
                }
                blunders.append(blunder)
            
            # Move to the next node
            node = node.next()
            if board.turn == chess.WHITE:
                move_number += 1
    finally:
        engine.quit()
    
    return blunders

def calculate_difficulty(eval_change):
    """Calculate puzzle difficulty based on evaluation change"""
    if eval_change >= 800:
        return 1
    elif eval_change >= 500:
        return 2
    elif eval_change >= 300:
        return 3
    elif eval_change >= 200:
        return 4
    else:
        return 5

def main():
    # Download stockfish when running in CI
    stockfish_path = os.environ.get("STOCKFISH_PATH")
    if not stockfish_path:
        stockfish_path = download_stockfish()
        
    puzzles = []
    
    if PLATFORM == "chess.com":
        games = fetch_chess_com_games()
    else:
        games = fetch_lichess_games()
    
    print(f"Fetched {len(games)} games from {PLATFORM}")
    
    # Analyze each game
    for game in games:
        pgn = get_pgn_from_game(game, PLATFORM)
        if pgn:
            game_blunders = analyze_game(pgn, stockfish_path)
            puzzles.extend(game_blunders)
            print(f"Found {len(game_blunders)} blunders in game")
    
    # Save puzzles to JSON file
    if puzzles:
        # Add metadata and timestamps
        output = {
            "puzzles": puzzles,
            "count": len(puzzles),
            "generated_at": datetime.now().isoformat(),
            "username": USERNAME,
            "platform": PLATFORM
        }
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Saved {len(puzzles)} puzzles to {OUTPUT_FILE}")
    else:
        print("No puzzles generated")

if __name__ == "__main__":
    main() 