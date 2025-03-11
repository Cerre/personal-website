"""
Game fetching and parsing module.

This module handles fetching games from chess platforms like Lichess and Chess.com,
parsing them, and preparing them for analysis.
"""
import re
import io
import logging
import requests
import chess
import chess.pgn
from typing import List, Dict, Any, Optional, Tuple, Union, Set

from chess_puzzles import config

logger = logging.getLogger(__name__)

class GameFetcher:
    """Fetches and parses chess games from online platforms."""
    
    def __init__(self, username: str, platform: str = "lichess"):
        """Initialize the game fetcher.
        
        Args:
            username (str): The username to fetch games for.
            platform (str, optional): The platform to fetch games from ('lichess' or 'chess.com').
                Defaults to "lichess".
        """
        self.username = username
        self.platform = platform.lower()
        logger.info(f"Initialized GameFetcher for {username} on {platform}")
        
    def fetch_games(self, max_games: int = config.MAX_GAMES, 
                   already_analyzed_games: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Fetch games from the specified platform.
        
        Args:
            max_games (int, optional): Maximum number of games to fetch. Defaults to config.MAX_GAMES.
            already_analyzed_games (Optional[Set[str]], optional): Set of game URLs that have already
                been analyzed and don't need to be fetched again.
                
        Returns:
            List[Dict[str, Any]]: List of game data dictionaries.
            
        Raises:
            ValueError: If the platform is not supported.
        """
        max_games_to_fetch = max(500, max_games)  # Fetch at least 500 to have a good pool to filter from
        logger.info(f"Fetching up to {max_games_to_fetch} games for {self.username} from {self.platform}")
        
        already_analyzed_games = already_analyzed_games or set()
        
        if self.platform == "lichess":
            games = self.fetch_lichess_games(max_games_to_fetch)
        elif self.platform == "chess.com":
            games = self.fetch_chess_com_games(max_games_to_fetch)
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
        
        # Filter out already analyzed games
        filtered_games = []
        for game in games:
            game_url = game.get('game_url')
            if game_url and game_url not in already_analyzed_games:
                filtered_games.append(game)
            
            # Stop once we have the requested number of games
            if len(filtered_games) >= max_games:
                break
        
        logger.info(f"Fetched {len(games)} games, filtered to {len(filtered_games)} new games")
        return filtered_games
            
    def fetch_lichess_games(self, max_games: int) -> List[Dict[str, Any]]:
        """Fetch games from Lichess API for the given username.
        
        Args:
            max_games (int): Maximum number of games to fetch.
            
        Returns:
            List[Dict[str, Any]]: List of game data dictionaries.
        """
        url = config.LICHESS_GAMES_URL(self.username)
        
        params = {
            'max': max_games,
            'pgnInJson': 'false',
            'rated': 'true',
            'perfType': 'blitz,rapid,classical',
            'ongoing': 'false',
            'finished': 'true',
            'sort': 'dateDesc',
            'moves': 'true',
            'tags': 'true',
            'opening': 'true',
            'clocks': 'false',
            'evals': 'false'
        }
        
        logger.info(f"Fetching {max_games} rated games from Lichess for user {self.username}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            pgn_content = response.text
            
            # Split the PGN content into individual games
            game_texts = re.split(r'\n\n\n+', pgn_content.strip())
            
            logger.info(f"Retrieved {len(game_texts)} games from Lichess")
            
            games = []
            
            for i, game_text in enumerate(game_texts):
                try:
                    game_data = self._parse_pgn_text(game_text, i)
                    if game_data:
                        games.append(game_data)
                except Exception as e:
                    logger.warning(f"Error parsing game {i+1}: {e}")
            
            logger.info(f"Successfully parsed {len(games)} games from Lichess")
            
            # Filter to games with at least MIN_MOVES moves
            filtered_games = [g for g in games if len(g['moves'].split()) > config.MIN_MOVES]
            logger.info(f"Filtered to {len(filtered_games)} games with more than {config.MIN_MOVES} moves")
            
            return filtered_games[:max_games]
            
        except requests.RequestException as e:
            logger.error(f"Error fetching games from Lichess: {e}")
            return []
            
    def fetch_chess_com_games(self, max_games: int) -> List[Dict[str, Any]]:
        """Fetch recent games from Chess.com.
        
        Args:
            max_games (int): Maximum number of games to fetch.
            
        Returns:
            List[Dict[str, Any]]: List of game data dictionaries.
        """
        try:
            # Get archives (monthly game collections)
            archives_url = config.CHESS_COM_ARCHIVES_URL(self.username)
            logger.info(f"Fetching game archives from Chess.com for user {self.username}")
            
            archives_response = requests.get(archives_url)
            archives_response.raise_for_status()
            archives = archives_response.json().get("archives", [])
            
            if not archives:
                logger.warning("No game archives found on Chess.com")
                return []
            
            # Get games from the most recent archive
            recent_archive = archives[-1]
            logger.info(f"Fetching games from most recent archive: {recent_archive}")
            
            games_response = requests.get(recent_archive)
            games_response.raise_for_status()
            
            raw_games = games_response.json().get("games", [])
            logger.info(f"Retrieved {len(raw_games)} games from Chess.com archive")
            
            # Convert Chess.com format to our standard format
            games = []
            for i, game in enumerate(raw_games[:max_games]):
                try:
                    pgn = game.get("pgn", "")
                    if pgn:
                        game_data = self._parse_pgn_text(pgn, i)
                        if game_data:
                            games.append(game_data)
                except Exception as e:
                    logger.warning(f"Error parsing Chess.com game {i+1}: {e}")
            
            logger.info(f"Successfully parsed {len(games)} games from Chess.com")
            
            # Filter to games with at least MIN_MOVES moves
            filtered_games = [g for g in games if len(g['moves'].split()) > config.MIN_MOVES]
            logger.info(f"Filtered to {len(filtered_games)} games with more than {config.MIN_MOVES} moves")
            
            return filtered_games[:max_games]
            
        except requests.RequestException as e:
            logger.error(f"Error fetching games from Chess.com: {e}")
            return []
            
    def _parse_pgn_text(self, pgn_text: str, index: int = 0) -> Optional[Dict[str, Any]]:
        """Parse a PGN text string into a structured game data dictionary.
        
        Args:
            pgn_text (str): PGN text to parse.
            index (int, optional): Index of the game for logging purposes. Defaults to 0.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed game data or None if parsing failed.
        """
        # Extract headers
        headers = re.findall(r'\[(.*?) "(.*?)"\]', pgn_text)
        headers_dict = {h[0]: h[1] for h in headers}
        
        # Look for important headers
        game_id = headers_dict.get('GameId', '')
        site = headers_dict.get('Site', '')
        white = headers_dict.get('White', '')
        black = headers_dict.get('Black', '')
        result = headers_dict.get('Result', '*')
        date = headers_dict.get('Date', '')
        
        # Ensure we have a URL
        game_url = self._extract_game_url(site, game_id)
        
        # Extract the moves text
        moves = self._extract_moves_from_pgn(pgn_text)
        
        # Only add games where we have the necessary information
        if white and black and moves:
            game_data = {
                'id': game_id or f"{self.platform}_{index}",
                'url': game_url,
                'white': white,
                'black': black,
                'result': result,
                'date': date,
                'pgn': pgn_text,
                'moves': moves,
                'headers': headers_dict,
                'platform': self.platform
            }
            
            return game_data
            
        logger.warning(f"Missing required information in game {index+1}")
        return None
        
    def _extract_game_url(self, site: str, game_id: str) -> Optional[str]:
        """Extract game URL from site or game_id.
        
        Args:
            site (str): Site header from PGN.
            game_id (str): Game ID header from PGN.
            
        Returns:
            Optional[str]: Game URL or None if not available.
        """
        if site and (site.startswith('https://lichess.org/') or site.startswith('https://www.chess.com/')):
            return site
        elif game_id and self.platform == 'lichess':
            return f"https://lichess.org/{game_id}"
        elif game_id and self.platform == 'chess.com':
            return f"https://www.chess.com/game/{game_id}"
        return None
        
    def _extract_moves_from_pgn(self, pgn_text: str) -> str:
        """Extract moves from PGN text.
        
        Args:
            pgn_text (str): PGN text to extract moves from.
            
        Returns:
            str: Moves text.
        """
        # Try to extract moves using regex pattern
        moves_match = re.search(r'\n\n(.*?)(?:\n\n|$)', pgn_text, re.DOTALL)
        if moves_match:
            return moves_match.group(1).strip()
        
        # Fallback: gather all lines that don't start with '['
        moves_lines = [line for line in pgn_text.split('\n') if not line.startswith('[')]
        return ' '.join(moves_lines).strip()
        
    def determine_player_color(self, game: Dict[str, Any], username: Optional[str] = None) -> Tuple[Optional[bool], str]:
        """Determine the color played by the player in the game.
        
        Args:
            game (Dict[str, Any]): Game data dictionary.
            username (Optional[str], optional): Username to look for. Defaults to self.username.
            
        Returns:
            Tuple[Optional[bool], str]: Tuple containing the color (chess.WHITE, chess.BLACK, or 
                None) and a description string.
        """
        username = username or self.username
        
        if not username:
            return None, "unknown"
        
        # For case-insensitive comparison
        username_lower = username.lower()
        
        # Try to get from direct game properties first
        white_player = game.get('white', '')
        black_player = game.get('black', '')
        
        white_player_lower = white_player.lower() if white_player else None
        black_player_lower = black_player.lower() if black_player else None
        
        # Try exact matches first
        if white_player_lower and username_lower == white_player_lower:
            return chess.WHITE, "WHITE"
        
        if black_player_lower and username_lower == black_player_lower:
            return chess.BLACK, "BLACK"
        
        # Try to extract from PGN if available
        pgn_text = game.get('pgn', '')
        if pgn_text:
            white_match = re.search(r'\[White\s+"([^"]+)"\]', pgn_text)
            black_match = re.search(r'\[Black\s+"([^"]+)"\]', pgn_text)
            
            pgn_white = white_match.group(1).lower() if white_match else None
            pgn_black = black_match.group(1).lower() if black_match else None
            
            if pgn_white and username_lower == pgn_white:
                return chess.WHITE, "WHITE (from PGN)"
            
            if pgn_black and username_lower == pgn_black:
                return chess.BLACK, "BLACK (from PGN)"
        
        # If we got here, we couldn't determine the color
        logger.warning(f"Could not find username '{username}' in the players list. Color unknown.")
        return None, "unknown"
        
    def parse_pgn_to_board(self, pgn_text: str) -> Optional[chess.pgn.Game]:
        """Parse PGN text into a chess.pgn.Game object.
        
        Args:
            pgn_text (str): PGN text to parse.
            
        Returns:
            Optional[chess.pgn.Game]: Parsed game or None if parsing failed.
        """
        try:
            pgn_io = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn_io)
            return game
        except Exception as e:
            logger.error(f"Error parsing PGN: {e}")
            return None
