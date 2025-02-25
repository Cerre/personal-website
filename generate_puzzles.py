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
USERNAME = os.environ.get("CHESS_USERNAME", "Toxima")
PLATFORM = os.environ.get("CHESS_PLATFORM", "lichess")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "puzzles.json")
MAX_GAMES = int(os.environ.get("MAX_GAMES", "15"))
BLUNDER_THRESHOLD = int(os.environ.get("BLUNDER_THRESHOLD", "80"))

# Chess.com API endpoints
CHESS_COM_ARCHIVES_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
# Lichess API endpoint
LICHESS_GAMES_URL = f"https://lichess.org/api/games/user/{USERNAME}"

def download_stockfish():
    """Download and prepare Stockfish for the current platform"""
    print("Downloading Stockfish...")
    stockfish_path = os.path.join(tempfile.gettempdir(), "stockfish")
    
    try:
        if sys.platform == "linux" or sys.platform == "linux2":
            # Linux - download Stockfish 16
            url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.0/stockfish-ubuntu-x86-64-avx2.tar.gz"
            print(f"Downloading from {url}")
            subprocess.run(["wget", url, "-O", "stockfish.tar.gz"], check=True)
            subprocess.run(["tar", "-xzf", "stockfish.tar.gz"], check=True)
            
            # List files to see the actual structure
            print("Extracted files:")
            subprocess.run(["ls", "-la"], check=True)
            
            # Try to find the stockfish executable
            try:
                subprocess.run(["find", ".", "-name", "stockfish*", "-type", "f", "-executable"], check=True)
            except:
                print("Could not find stockfish executable with find")
            
            # Move the stockfish executable - path might vary
            try:
                subprocess.run(["mv", "./stockfish-*-ubuntu-x86-64-avx2", stockfish_path], check=False)
            except:
                # Try alternative paths
                try:
                    subprocess.run(["find", ".", "-name", "stockfish*", "-type", "f", "-executable", "-exec", "mv", "{}", stockfish_path, ";"], check=False)
                except:
                    print("Could not move stockfish executable, will try to use it directly")
                    # See if we can find it
                    result = subprocess.run(["find", ".", "-name", "stockfish*", "-type", "f", "-executable"], capture_output=True, text=True)
                    if result.stdout.strip():
                        stockfish_path = result.stdout.strip().split("\n")[0]
                        print(f"Found stockfish at: {stockfish_path}")
            
            # Make sure it's executable
            try:
                subprocess.run(["chmod", "+x", stockfish_path], check=True)
            except:
                print(f"Could not chmod {stockfish_path}")
                
        elif sys.platform == "darwin":
            # macOS - download Stockfish 16
            url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.0/stockfish-macos-x86-64-avx2.tar.gz"
            subprocess.run(["curl", "-L", url, "-o", "stockfish.tar.gz"], check=True)
            subprocess.run(["tar", "-xzf", "stockfish.tar.gz"], check=True)
            
            # List files to see the actual structure
            print("Extracted files:")
            subprocess.run(["ls", "-la"], check=True)
            
            # Find and move the stockfish executable - path might vary
            result = subprocess.run(["find", ".", "-name", "stockfish*", "-type", "f", "-perm", "+111"], capture_output=True, text=True)
            if result.stdout.strip():
                found_path = result.stdout.strip().split("\n")[0]
                subprocess.run(["mv", found_path, stockfish_path], check=True)
            else:
                raise Exception("Could not find stockfish executable")
                
            subprocess.run(["chmod", "+x", stockfish_path], check=True)
            
        elif sys.platform == "win32":
            # Windows - download Stockfish 16
            url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.0/stockfish-windows-x86-64-avx2.zip"
            subprocess.run(["curl", "-L", url, "-o", "stockfish.zip"], check=True)
            subprocess.run(["unzip", "stockfish.zip"], check=True)
            
            # List files to see the actual structure
            print("Extracted files:")
            subprocess.run(["dir", "/b"], shell=True, check=True)
            
            stockfish_path = os.path.join(tempfile.gettempdir(), "stockfish.exe")
            
            # Find and move the stockfish executable - path might vary
            result = subprocess.run(["where", "/r", ".", "stockfish*.exe"], capture_output=True, text=True, shell=True)
            if result.stdout.strip():
                found_path = result.stdout.strip().split("\n")[0]
                subprocess.run(["move", found_path, stockfish_path], shell=True, check=True)
            else:
                raise Exception("Could not find stockfish executable")
    
        print(f"Stockfish downloaded to {stockfish_path}")
        return stockfish_path
        
    except Exception as e:
        print(f"Error downloading/preparing Stockfish: {e}")
        # As a fallback, try to use stockfish from PATH
        print("Trying to use stockfish from PATH...")
        try:
            # Check if stockfish is available in PATH
            subprocess.run(["stockfish", "--version"], check=True, capture_output=True)
            return "stockfish"
        except:
            print("Could not find stockfish in PATH either")
            raise

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
        # Use more specific parameters to get better quality games
        params = {
            "max": limit,  
            "pgnInJson": "true",
            "rated": "true",           # Only rated games
            "perfType": "blitz,rapid,classical", # Focus on standard time controls
            "ongoing": "false",        # Exclude games in progress
            "lastFen": "true"          # Include FEN of final position
        }
        
        print(f"Fetching {limit} rated games for user {USERNAME}...")
        response = requests.get(LICHESS_GAMES_URL, params=params)
        response.raise_for_status()
        
        # Parse NDJSON (each line is a JSON object)
        games = [json.loads(line) for line in response.text.split('\n') if line]
        print(f"Received {len(games)} games from Lichess")
        
        # Filter out games with less than 10 moves (likely to be quick losses or non-serious games)
        filtered_games = [game for game in games if game.get("moves", "").count(" ") > 10]
        print(f"Filtered to {len(filtered_games)} games with more than 10 moves")
        
        return filtered_games
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

def get_game_url(game, platform):
    """Extract the URL for a game based on platform"""
    if platform == "chess.com":
        return game.get("url", "")
    elif platform == "lichess":
        return f"https://lichess.org/{game.get('id', '')}"
    return ""

def analyze_game(pgn_text, game_url, stockfish_path):
    """Analyze a game to find blunders"""
    # Parse PGN
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    if not game:
        print(f"Warning: Could not parse PGN for game {game_url}")
        return []
    
    blunders = []
    board = game.board()
    
    # Initialize Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    try:
        # Process each move
        node = game.next()
        move_number = 1
        
        print(f"Analyzing game {game_url}")
        
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
                    "difficulty": calculate_difficulty(eval_change),
                    "game_url": game_url
                }
                blunders.append(blunder)
                print(f"  Found blunder: move {move_number}, {san_move}, eval change: {eval_change}")
            
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
        game_url = get_game_url(game, PLATFORM)
        if pgn:
            game_blunders = analyze_game(pgn, game_url, stockfish_path)
            puzzles.extend(game_blunders)
            print(f"Found {len(game_blunders)} blunders in game {game_url}")
    
    # Output data structure - always create this file
    output = {
        "puzzles": puzzles,
        "count": len(puzzles),
        "generated_at": datetime.now().isoformat(),
        "username": USERNAME,
        "platform": PLATFORM
    }
    
    # If no puzzles were found, add a placeholder puzzle
    if not puzzles:
        print("No puzzles generated, adding a placeholder puzzle")
        # Provide a simple default puzzle - Scholar's mate position
        placeholder_puzzle = {
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
            "solution": ["e8f7"],  # Kf7 is the only legal move
            "player_color": "black",
            "move_number": 3,
            "blundered_move": "Nc6",
            "eval_change": 900,
            "difficulty": 2,
            "game_url": "https://lichess.org/learn#/4"
        }
        output["puzzles"] = [placeholder_puzzle]
        output["count"] = 1
        output["is_placeholder"] = True
        output["message"] = "No blunders found in recent games. This is a placeholder puzzle."
    
    # Save puzzles to JSON file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved {len(output['puzzles'])} puzzles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 