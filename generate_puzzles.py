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
import traceback
import re
import uuid

# Configuration (can be overridden with environment variables)
USERNAME = os.environ.get("CHESS_USERNAME", "Toxima")
PLATFORM = os.environ.get("CHESS_PLATFORM", "lichess")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "puzzles.json")
MAX_GAMES = int(os.environ.get("MAX_GAMES", "5"))
BLUNDER_THRESHOLD = int(os.environ.get("BLUNDER_THRESHOLD", "500"))
DEBUG = True  # Enable detailed debugging

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
            "pgnInJson": "false",   # Get PGN format (not inside JSON)
            "rated": "true",        # Only rated games
            "perfType": "blitz,rapid,classical", # Focus on standard time controls
            "ongoing": "false",     # Exclude games in progress
            "lastFen": "true"       # Include FEN of final position
        }
        
        print(f"DEBUG: Fetching {limit} rated games for user {USERNAME}...")
        print(f"DEBUG: Request URL: {LICHESS_GAMES_URL} with params: {params}")
        
        response = requests.get(LICHESS_GAMES_URL, params=params)
        response.raise_for_status()
        
        # Debug: print raw response 
        if DEBUG:
            print(f"DEBUG: Response status code: {response.status_code}")
            print(f"DEBUG: Response headers: {response.headers}")
            print(f"DEBUG: Response content snippet: {response.text[:500]}...")
        
        # Split PGN data into individual games
        pgn_content = response.text
        
        # Split the PGN text into individual games (games are separated by blank lines)
        pgn_games = []
        current_game = []
        
        for line in pgn_content.split('\n'):
            if line.strip():  # If line is not empty
                current_game.append(line)
            elif current_game:  # Empty line and we have game data
                pgn_games.append('\n'.join(current_game))
                current_game = []
        
        # Add the last game if there is one
        if current_game:
            pgn_games.append('\n'.join(current_game))
            
        print(f"DEBUG: Split into {len(pgn_games)} PGN games")
        
        # Parse each game to extract metadata and create a game object
        games = []
        for pgn_text in pgn_games:
            try:
                # Extract game ID and site from the PGN
                game_id = None
                game_url = None
                
                # Look for Site tag
                site_match = re.search(r'\[Site "([^"]+)"\]', pgn_text)
                if site_match:
                    game_url = site_match.group(1)
                    game_id = game_url.split('/')[-1]
                
                # If no Site tag, look for GameId tag
                if not game_id:
                    game_id_match = re.search(r'\[GameId "([^"]+)"\]', pgn_text)
                    if game_id_match:
                        game_id = game_id_match.group(1)
                        game_url = f"https://lichess.org/{game_id}"
                
                # Create a game object
                game = {
                    'id': game_id,
                    'url': game_url,
                    'pgn': pgn_text,
                    # Count moves by splitting on move numbers (like "1. e4")
                    'moves': ' '.join([line for line in pgn_text.split('\n') if not line.startswith('[')])
                }
                
                games.append(game)
                
                # Print debug info about the first game
                if DEBUG and len(games) == 1:
                    print("\nDEBUG: Example of first game data:")
                    print(f"  Game ID: {game.get('id')}")
                    print(f"  Game URL: {game.get('url')}")
                    print(f"  PGN length: {len(pgn_text)}")
                    print(f"  PGN snippet: {pgn_text[:200]}...")
                    print(f"  Move data snippet: {game.get('moves')[:100]}...")
                
            except Exception as e:
                print(f"DEBUG: Error parsing PGN game: {e}")
                traceback.print_exc()
        
        print(f"DEBUG: Successfully parsed {len(games)} games from Lichess")
        
        # Filter out games with less than 10 moves
        # Count moves by looking for move numbers in the PGN (e.g., "1. e4 e5 2. Nf3")
        move_count_threshold = 10
        filtered_games = []
        
        for game in games:
            # Simple heuristic: count the number of dots (.) in the moves line to estimate move count
            # Each move number like "1." has a dot, so if we find more than 10 dots, it likely has >10 moves
            moves_line = game.get('moves', '')
            move_numbers = [word for word in moves_line.split() if word.endswith('.')]
            move_count = len(move_numbers)
            
            if move_count >= move_count_threshold:
                filtered_games.append(game)
                
        print(f"DEBUG: Filtered to {len(filtered_games)} games with more than {move_count_threshold} moves")
        
        return filtered_games
    except Exception as e:
        print(f"Error fetching Lichess games: {e}")
        print("Traceback:")
        traceback.print_exc()
        return []

def get_pgn_from_game(game, platform):
    """Extract PGN from a game object based on platform"""
    if platform == "chess.com":
        pgn = game.get("pgn", "")
        if DEBUG:
            print(f"DEBUG: Chess.com PGN length: {len(pgn)}")
        return pgn
    elif platform == "lichess":
        pgn = game.get("pgn", "")
        if DEBUG:
            print(f"DEBUG: Lichess PGN length: {len(pgn)}")
            if pgn:
                print(f"DEBUG: PGN snippet: {pgn[:100]}...")
        return pgn
    return ""

def get_game_url(game_data, platform):
    """Extract the game URL from game data."""
    if isinstance(game_data, dict):
        # Handle dictionary format
        if 'pgn' in game_data:
            # Extract from PGN text inside the dictionary
            pgn_text = game_data['pgn']
            # Try to extract URL from the Site tag
            site_match = re.search(r'\[Site "([^"]+)"\]', pgn_text)
            if site_match:
                return site_match.group(1)
            
            # If that fails, try to extract from GameId tag
            game_id_match = re.search(r'\[GameId "([^"]+)"\]', pgn_text)
            if game_id_match and platform == "lichess":
                return f"https://lichess.org/{game_id_match.group(1)}"
                
        # Direct keys in the dictionary
        if 'url' in game_data:
            # For Chess.com games
            return game_data['url']
        elif 'site' in game_data:
            # For Lichess games
            return game_data['site']
        elif 'id' in game_data and platform == "lichess":
            # Use game_id if available
            return f"https://lichess.org/{game_data['id']}"
    
    elif isinstance(game_data, str):
        # Handle string format (PGN text)
        # Try to extract URL from the Site tag
        site_match = re.search(r'\[Site "([^"]+)"\]', game_data)
        if site_match:
            return site_match.group(1)
        
        # If that fails, try to extract from GameId tag
        game_id_match = re.search(r'\[GameId "([^"]+)"\]', game_data)
        if game_id_match and platform == "lichess":
            return f"https://lichess.org/{game_id_match.group(1)}"
    
    # If neither works, return None
    return None

def test_game_parsing(pgn_text, game_url):
    """Test if we can parse a game's PGN"""
    try:
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        if game:
            print(f"DEBUG: Successfully parsed game PGN for {game_url}")
            return True
        else:
            print(f"DEBUG: Failed to parse game PGN for {game_url}")
            return False
    except Exception as e:
        print(f"DEBUG: Exception during game parsing for {game_url}: {e}")
        return False

def analyze_game(game_data, stockfish_path=None, blunder_threshold=80, platform="lichess"):
    """Analyze a game for blunders and generate puzzles."""
    try:
        # Extract game URL directly from the game_data dict
        game_url = None
        if isinstance(game_data, dict) and 'url' in game_data:
            game_url = game_data['url']
        
        # Get the PGN text
        pgn = get_pgn_from_game(game_data, platform)
        
        # If we still don't have a URL, try to extract it from PGN
        if not game_url:
            site_match = re.search(r'\[Site "([^"]+)"\]', pgn)
            if site_match:
                game_url = site_match.group(1)
            else:
                game_id_match = re.search(r'\[GameId "([^"]+)"\]', pgn)
                if game_id_match and platform == "lichess":
                    game_url = f"https://lichess.org/{game_id_match.group(1)}"
                    
        print(f"Analyzing game {game_url}")
        
        DEBUG and print(f"DEBUG: PGN length: {len(pgn)}")
        DEBUG and print(f"DEBUG: PGN snippet: {pgn[:100]}...")
        DEBUG and print(f"DEBUG: Game URL: {game_url}")
        
        if not pgn:
            print(f"Warning: Could not parse PGN for game {game_url}")
            return []
        
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)
        
        if DEBUG:
            print(f"DEBUG: Game URL: {game_url}")
            print(f"DEBUG: PGN length: {len(str(game.mainline_moves()))}")
            print(f"DEBUG: Game status: {getattr(game, 'status', None)}")
            print(f"DEBUG: Game winner: {getattr(game, 'winner', None)}")
            print(f"DEBUG: Game moves: {str(game.mainline_moves())[:50]}...")
            print(f"DEBUG: Successfully parsed game PGN for {game_url}")
            print(f"DEBUG: Game headers: {game.headers}")
        
        if not game:
            print(f"Warning: Could not parse PGN for game {game_url}")
            return []
        
        blunders = []
        board = game.board()
        
        # Determine which color Toxima is playing
        toxima_color = None
        if 'White' in game.headers and game.headers['White'].lower() == USERNAME.lower():
            toxima_color = chess.WHITE
            print(f"DEBUG: {USERNAME} is playing White")
        elif 'Black' in game.headers and game.headers['Black'].lower() == USERNAME.lower():
            toxima_color = chess.BLACK
            print(f"DEBUG: {USERNAME} is playing Black")
        else:
            print(f"WARNING: Could not determine {USERNAME}'s color in this game. Headers: {game.headers}")
            # If we can't determine the color, skip this game
            return []
        
        # Debug: examine headers
        if DEBUG:
            print(f"DEBUG: Game headers: {game.headers}")
        
        # Initialize Stockfish engine
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        except Exception as e:
            print(f"ERROR: Failed to initialize Stockfish engine: {e}")
            traceback.print_exc()
            return []
        
        try:
            # Process each move
            node = game.next()
            move_number = 1
            moves_analyzed = 0
            
            print(f"Analyzing game {game_url}")
            
            while node:
                try:
                    # Only check for blunders when it's Toxima's turn
                    is_toxima_turn = (board.turn == toxima_color)
                    
                    # Get position before the move
                    prev_fen = board.fen()
                    
                    # Debug: evaluate current position
                    if DEBUG and moves_analyzed < 3:  # Only debug first few moves to avoid too much output
                        print(f"DEBUG: Evaluating position at move {move_number}, FEN: {prev_fen}")
                    
                    prev_eval = engine.analyse(board, chess.engine.Limit(time=0.1))["score"].relative.score(mate_score=10000)
                    
                    # Make the move
                    move = node.move
                    san_move = board.san(move)
                    board.push(move)
                    
                    # Debug: show move being analyzed
                    if DEBUG and moves_analyzed < 3:
                        print(f"DEBUG: Made move {san_move}, analyzing new position")
                    
                    # Evaluate new position
                    curr_eval = -engine.analyse(board, chess.engine.Limit(time=0.1))["score"].relative.score(mate_score=10000)
                    
                    # Calculate evaluation change
                    eval_change = prev_eval - curr_eval
                    
                    if DEBUG and moves_analyzed < 3:
                        print(f"DEBUG: Move {move_number}.{san_move} - Prev eval: {prev_eval}, Curr eval: {curr_eval}, Change: {eval_change}")
                    
                    # Check if move is a blunder and it was Toxima's turn
                    # A true blunder is when a player in a good/even position makes a move
                    # that significantly worsens their position
                    if is_toxima_turn and eval_change >= blunder_threshold and prev_eval >= 0:
                        player = "white" if toxima_color == chess.WHITE else "black"
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
                        print(f"  Found blunder by {USERNAME}: move {move_number}, {san_move}, eval change: {eval_change}, prev_eval: {prev_eval}, curr_eval: {curr_eval}")
                    
                    # Move to the next node
                    node = node.next()
                    moves_analyzed += 1
                    if board.turn == chess.WHITE:
                        move_number += 1
                    
                except Exception as e:
                    print(f"ERROR during move analysis: {e}")
                    traceback.print_exc()
                    node = node.next()  # Skip problematic move
                    if board.turn == chess.WHITE:
                        move_number += 1
            
            print(f"DEBUG: Completed analysis, analyzed {moves_analyzed} moves, found {len(blunders)} blunders by {USERNAME}")
            
        except Exception as e:
            print(f"ERROR during game analysis: {e}")
            traceback.print_exc()
        finally:
            engine.quit()
        
        return blunders
    except Exception as e:
        print(f"Error analyzing game: {e}")
        traceback.print_exc()
        return []

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

def prepare_stockfish():
    """Download Stockfish if needed or use from environment or path"""
    stockfish_path = os.environ.get("STOCKFISH_PATH")
    if not stockfish_path:
        try:
            stockfish_path = download_stockfish()
        except Exception as e:
            print(f"Error downloading/preparing Stockfish: {e}")
            print("Trying to use stockfish from PATH...")
            stockfish_path = "stockfish"
    return stockfish_path

def test_stockfish(stockfish_path):
    """Test that Stockfish engine is working correctly"""
    try:
        if DEBUG:
            print("DEBUG: Testing Stockfish engine...")
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            result = engine.analyse(chess.Board(), chess.engine.Limit(time=0.1))
            print(f"DEBUG: Stockfish test evaluation: {result['score']}")
            engine.quit()
            print("DEBUG: Stockfish engine is working correctly")
    except Exception as e:
        print(f"ERROR: Stockfish engine test failed: {e}")
        traceback.print_exc()

def create_puzzle(initial_fen, moves, game_url=None, platform="lichess", player_color="white", puzzle_type="blunder"):
    """Create a puzzle object from a position and moves"""
    try:
        puzzle_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
        
        # Format moves for the puzzle - list of UCI moves
        puzzle_moves = []
        for move in moves:
            puzzle_moves.append(move.uci())
                
        # Create the puzzle object
        puzzle = {
            "id": puzzle_id,
            "fen": initial_fen,
            "moves": puzzle_moves,
            "game_url": game_url,
            "platform": platform,
            "player_color": player_color,
            "puzzle_type": puzzle_type,
            "created_at": datetime.now().isoformat()
        }
        
        return puzzle
    except Exception as e:
        print(f"Error creating puzzle: {e}")
        return None

def main():
    """Main function to generate puzzles"""
    # Download Stockfish if needed
    stockfish_path = prepare_stockfish()
    print(f"DEBUG: Using Stockfish at path: {stockfish_path}")
    
    # Basic test to ensure Stockfish is working
    test_stockfish(stockfish_path)
    
    # Get games from Lichess
    games = fetch_lichess_games(limit=MAX_GAMES)
    print(f"Fetched {len(games)} games from lichess\n")
    
    all_puzzles = []
    
    # Process each game
    for i, game in enumerate(games):
        print(f"\nDEBUG: Processing game {i+1} of {len(games)}")
        
        # Get the PGN text and game URL
        pgn_text = game.get('pgn', '')
        game_url = game.get('url', 'Unknown game URL')
        
        print(f"DEBUG: Lichess PGN length: {len(pgn_text)}")
        print(f"DEBUG: PGN snippet: {pgn_text[:100]}...")
        print(f"Analyzing game {game_url}")
        
        # Analyze the game
        game_blunders = analyze_game(game, stockfish_path=stockfish_path, blunder_threshold=BLUNDER_THRESHOLD, platform="lichess")
        
        # Add blunders to the list of puzzles
        if game_blunders:
            all_puzzles.extend(game_blunders)
            print(f"Found {len(game_blunders)} blunders in game {game_url}")
        else:
            print(f"No puzzles found in game {game_url}")
    
    # Output data structure - always create this file
    output = {
        "puzzles": all_puzzles,
        "count": len(all_puzzles),
        "generated_at": datetime.now().isoformat(),
        "username": USERNAME,
        "platform": PLATFORM
    }
    
    # If no puzzles were found, add a placeholder puzzle
    if not all_puzzles:
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