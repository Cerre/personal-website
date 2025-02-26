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
            "finished": "true",     # Only include finished games
            "sort": "dateDesc",     # Latest games first (default, but being explicit)
            "moves": "true",        # Include the PGN moves
            "tags": "true",         # Include the PGN tags
            "opening": "true",      # Include opening information
            "clocks": "false",      # Skip clock information to reduce size
            "evals": "false"        # Skip evaluation data as we'll do our own analysis
        }
        
        print(f"DEBUG: Fetching {limit} rated games for user {USERNAME}...")
        print(f"DEBUG: Request URL: {LICHESS_GAMES_URL} with params: {params}")
        
        # Set Accept header for PGN format
        headers = {
            "Accept": "application/x-chess-pgn"
        }
        
        response = requests.get(LICHESS_GAMES_URL, params=params, headers=headers)
        response.raise_for_status()
        
        # Debug: print raw response 
        if DEBUG:
            print(f"DEBUG: Response status code: {response.status_code}")
            print(f"DEBUG: Response headers: {response.headers}")
            print(f"DEBUG: Response content snippet: {response.text[:500]}...")
        
        # Split PGN data into individual games in a more systematic way
        pgn_content = response.text
        
        # First, split by blank lines to separate games
        raw_games = re.split(r'\n\n\n+', pgn_content.strip())
        print(f"DEBUG: Split into {len(raw_games)} raw games")
        
        games = []
        
        # Process each game
        for raw_game in raw_games:
            if not raw_game.strip():
                continue  # Skip empty entries
                
            try:
                # Complete PGN text for this game
                pgn_text = raw_game.strip()
                
                # Create a dictionary to store game data
                game_data = {'pgn': pgn_text}
                
                # Extract headers using regex
                # Common headers we need
                header_patterns = {
                    'id': r'\[GameId "([^"]+)"\]',
                    'site': r'\[Site "([^"]+)"\]',
                    'white': r'\[White "([^"]+)"\]',
                    'black': r'\[Black "([^"]+)"\]',
                    'result': r'\[Result "([^"]+)"\]',
                    'date': r'\[Date "([^"]+)"\]',
                    'time_control': r'\[TimeControl "([^"]+)"\]',
                    'termination': r'\[Termination "([^"]+)"\]',
                }
                
                # Extract all headers at once
                for key, pattern in header_patterns.items():
                    match = re.search(pattern, pgn_text)
                    if match:
                        game_data[key] = match.group(1)
                
                # Make sure we have the essential data
                if 'site' in game_data:
                    # For Lichess, the game URL is the Site value
                    game_data['url'] = game_data['site']
                elif 'id' in game_data:
                    # If we have a GameId but no Site, construct the URL
                    game_data['url'] = f"https://lichess.org/{game_data['id']}"
                
                # Extract the moves text (excluding headers)
                moves_pattern = r'\]\s*\n\s*\n([\s\S]+)$'
                moves_match = re.search(moves_pattern, pgn_text)
                if moves_match:
                    game_data['moves'] = moves_match.group(1).strip()
                else:
                    # Fallback: get all lines that don't start with [
                    game_data['moves'] = '\n'.join([
                        line for line in pgn_text.split('\n') 
                        if line.strip() and not line.strip().startswith('[')
                    ])
                
                # Double-check we have required fields
                if 'white' in game_data and 'black' in game_data and 'moves' in game_data:
                    # Add the game to our list
                    games.append(game_data)
                    
                    # Print debug info about the first game
                    if DEBUG and len(games) == 1:
                        print("\nDEBUG: Example of first game data:")
                        print(f"  Game ID: {game_data.get('id')}")
                        print(f"  Game URL: {game_data.get('url')}")
                        print(f"  White Player: {game_data.get('white')}")
                        print(f"  Black Player: {game_data.get('black')}")
                        print(f"  PGN length: {len(pgn_text)}")
                        print(f"  PGN snippet: {pgn_text[:200]}...")
                        print(f"  Move data snippet: {game_data.get('moves')[:100]}...")
                else:
                    print(f"DEBUG: Skipping game because it's missing required fields: {game_data.keys()}")
            
            except Exception as e:
                print(f"DEBUG: Error parsing PGN game: {e}")
                traceback.print_exc()
        
        print(f"DEBUG: Successfully parsed {len(games)} games from Lichess")
        
        # Filter out games with less than 10 moves
        move_count_threshold = 10
        filtered_games = []
        
        for game in games:
            # Count moves by looking for move numbers in the moves text
            moves_text = game.get('moves', '')
            # Each move number like "1." has a dot, so count those
            move_numbers = [word for word in moves_text.split() if word.endswith('.')]
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
        if 'url' in game_data and game_data['url']:
            return game_data['url']
            
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
        if 'site' in game_data and game_data['site']:
            # For Lichess games
            return game_data['site']
        elif 'id' in game_data and game_data['id'] and platform == "lichess":
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
        game_url = get_game_url(game_data, platform)
                    
        print(f"Analyzing game {game_url}")
        
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
        
        # Modified PGN parsing to ensure headers are properly set
        pgn_io = io.StringIO(pgn)
        
        # Before parsing the game, check if this is a newer format PGN with headers at the top
        # Extract the headers manually if needed
        pgn_headers = {}
        
        # Extract known headers from the PGN text using regex
        white_match = re.search(r'\[White "([^"]+)"\]', pgn)
        black_match = re.search(r'\[Black "([^"]+)"\]', pgn)
        
        if white_match:
            pgn_headers['White'] = white_match.group(1)
        
        if black_match:
            pgn_headers['Black'] = black_match.group(1)
            
        # Parse the game
        game = chess.pgn.read_game(pgn_io)
        
        if not game:
            print(f"Warning: Could not parse PGN for game {game_url}")
            return []
            
        # If we have manually extracted headers, use them to supplement the game headers
        if pgn_headers:
            # Update game headers with our extracted values
            for header, value in pgn_headers.items():
                game.headers[header] = value
                
            if DEBUG:
                print(f"DEBUG: Updated game headers using extracted values: {game.headers}")
        
        if DEBUG:
            print(f"DEBUG: Game URL: {game_url}")
            print(f"DEBUG: PGN length: {len(str(game.mainline_moves()))}")
            print(f"DEBUG: Game status: {getattr(game, 'status', None)}")
            print(f"DEBUG: Game winner: {getattr(game, 'winner', None)}")
            print(f"DEBUG: Game moves: {str(game.mainline_moves())[:50]}...")
            print(f"DEBUG: Successfully parsed game PGN for {game_url}")
            print(f"DEBUG: Game headers: {game.headers}")
        
        blunders = []
        board = game.board()
        
        # If we don't have proper headers in the game object, get them from the game_data if available
        if ('White' not in game.headers or 'Black' not in game.headers or 
            game.headers['White'] == '?' or game.headers['Black'] == '?'):
            
            if isinstance(game_data, dict):
                # Use values from the parsed game object
                if 'white' in game_data and game_data['white']:
                    game.headers['White'] = game_data['white']
                if 'black' in game_data and game_data['black']:
                    game.headers['Black'] = game_data['black']
                    
                print(f"DEBUG: Updated headers from game_data: White={game.headers.get('White')}, Black={game.headers.get('Black')}")
        
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
        print(f"DEBUG: Game data: id={game.get('id')}, url={game.get('url')}")
        print(f"DEBUG: Players: White={game.get('white')}, Black={game.get('black')}")
        
        # Determine player color directly here
        player_color = None
        white_player = game.get('white', '')
        black_player = game.get('black', '')
        
        # Handle None values in player names
        if white_player is None:
            white_player = ''
        if black_player is None:
            black_player = ''
            
        if white_player.lower() == USERNAME.lower():
            player_color = chess.WHITE
            print(f"DEBUG: {USERNAME} is playing as WHITE")
        elif black_player.lower() == USERNAME.lower():
            player_color = chess.BLACK
            print(f"DEBUG: {USERNAME} is playing as BLACK")
        else:
            print(f"WARNING: Could not determine {USERNAME}'s color from game data")
            print(f"DEBUG: Game white player: '{white_player}', black player: '{black_player}'")
            
            # Try another approach - extract from raw PGN
            pgn_text = game.get('pgn', '')
            if pgn_text:
                print("Trying to extract player names from raw PGN...")
                white_match = re.search(r'\[White "([^"]+)"\]', pgn_text)
                black_match = re.search(r'\[Black "([^"]+)"\]', pgn_text)
                
                white_from_pgn = white_match.group(1) if white_match else None
                black_from_pgn = black_match.group(1) if black_match else None
                
                print(f"Extracted from PGN: White='{white_from_pgn}', Black='{black_from_pgn}'")
                
                if white_from_pgn and white_from_pgn.lower() == USERNAME.lower():
                    player_color = chess.WHITE
                    print(f"DEBUG: {USERNAME} is playing as WHITE (from PGN)")
                elif black_from_pgn and black_from_pgn.lower() == USERNAME.lower():
                    player_color = chess.BLACK
                    print(f"DEBUG: {USERNAME} is playing as BLACK (from PGN)")
                else:
                    print(f"Still unable to determine player color")
                    continue  # Skip this game
            else:
                continue  # Skip this game if no player color found
            
        # Get the PGN text
        pgn_text = game.get('pgn', '')
        
        # Get game URL - try multiple sources
        game_url = game.get('url')
        if not game_url:
            # Try to extract from site field
            game_url = game.get('site')
            
        if not game_url and game.get('id'):
            # Construct URL from game ID if available
            game_url = f"https://lichess.org/{game.get('id')}"
        
        if not game_url:
            # Last resort - extract from PGN
            site_match = re.search(r'\[Site "([^"]+)"\]', pgn_text)
            if site_match:
                game_url = site_match.group(1)
                game['url'] = game_url  # Store it for later use
        
        print(f"DEBUG: Lichess PGN length: {len(pgn_text)}")
        print(f"DEBUG: Game URL: {game_url}")
        
        # Custom simplified analysis that knows the player color upfront
        game_blunders = analyze_game_simple(
            pgn_text=pgn_text, 
            game_url=game_url, 
            toxima_color=player_color, 
            stockfish_path=stockfish_path, 
            blunder_threshold=BLUNDER_THRESHOLD
        )
        
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

def analyze_game_simple(pgn_text, game_url=None, toxima_color=None, stockfish_path=None, blunder_threshold=80):
    """Simplified game analysis that already knows the player color."""
    try:
        if not pgn_text:
            print(f"Warning: Empty PGN for game {game_url}")
            return []
            
        if toxima_color is None:
            print(f"Warning: Player color not provided for game {game_url}")
            return []
            
        print(f"Analyzing game {game_url}")
        print(f"Player color is {'WHITE' if toxima_color == chess.WHITE else 'BLACK'}")
        
        # Parse PGN
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        
        if not game:
            print(f"Warning: Could not parse PGN for game {game_url}")
            return []
        
        blunders = []
        board = game.board()
        
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

if __name__ == "__main__":
    main() 