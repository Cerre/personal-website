"""
Helper utility functions for the chess puzzles generator.
"""
import logging
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import chess

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration.
    
    Args:
        log_level (str, optional): Logging level. Defaults to "INFO".
        log_file (Optional[str], optional): Path to log file. Defaults to None.
    """
    # Create logs directory if logging to file
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = []
    
    # Always log to console
    handlers.append(logging.StreamHandler(sys.stdout))
    
    # Log to file if specified
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Set up logging configuration
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    # Log startup info
    logger.info(f"Logging initialized at level {log_level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")

def format_time(seconds: float) -> str:
    """Format time in seconds to a human-readable string.
    
    Args:
        seconds (float): Time in seconds.
        
    Returns:
        str: Formatted time string.
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def format_eval(eval_score: int) -> str:
    """Format evaluation score in a human-readable way.
    
    Args:
        eval_score (int): Evaluation in centipawns.
        
    Returns:
        str: Formatted evaluation string.
    """
    if abs(eval_score) >= 9900:  # Mate score
        if eval_score > 0:
            return f"Mate in {(10000 - eval_score) // 100}"
        else:
            return f"Mated in {(10000 + eval_score) // 100}"
    
    # Regular evaluation
    pawns = eval_score / 100.0
    sign = "+" if pawns > 0 else ""
    return f"{sign}{pawns:.2f}"

def color_name(color: bool) -> str:
    """Convert chess.WHITE/chess.BLACK to a string representation.
    
    Args:
        color (bool): chess.WHITE (True) or chess.BLACK (False).
        
    Returns:
        str: "white" or "black" string.
    """
    return "white" if color == chess.WHITE else "black"

def get_game_statistics(blunders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics from found blunders.
    
    Args:
        blunders (List[Dict[str, Any]]): List of detected blunders.
        
    Returns:
        Dict[str, Any]: Statistics about the blunders.
    """
    if not blunders:
        return {
            "count": 0,
            "message": "No blunders found"
        }
    
    # Collect statistics
    stats = {
        "count": len(blunders),
        "by_difficulty": {},
        "by_blunder_type": {},
        "avg_eval_change": 0,
        "earliest_move": float("inf"),
        "latest_move": 0
    }
    
    total_eval_change = 0
    
    # Process each blunder
    for blunder in blunders:
        # Difficulty stats
        difficulty = blunder.get("difficulty", 0)
        if difficulty not in stats["by_difficulty"]:
            stats["by_difficulty"][difficulty] = 0
        stats["by_difficulty"][difficulty] += 1
        
        # Blunder type stats
        blunder_type = blunder.get("blunder_type", "unknown")
        if blunder_type not in stats["by_blunder_type"]:
            stats["by_blunder_type"][blunder_type] = 0
        stats["by_blunder_type"][blunder_type] += 1
        
        # Move number stats
        move_number = blunder.get("move_number", 0)
        stats["earliest_move"] = min(stats["earliest_move"], move_number)
        stats["latest_move"] = max(stats["latest_move"], move_number)
        
        # Evaluation change
        eval_change = blunder.get("eval_change", 0)
        total_eval_change += eval_change
    
    # Calculate average evaluation change
    stats["avg_eval_change"] = total_eval_change / len(blunders)
    
    # Format difficulty levels with labels
    difficulty_labels = {
        1: "Very Easy",
        2: "Easy",
        3: "Intermediate",
        4: "Challenging",
        5: "Advanced"
    }
    
    stats["difficulty_distribution"] = {
        difficulty_labels.get(diff, f"Level {diff}"): count 
        for diff, count in stats["by_difficulty"].items()
    }
    
    return stats

def create_init_files(root_dir: Path):
    """Create __init__.py files in all subdirectories.
    
    Args:
        root_dir (Path): Root directory of the project.
    """
    for path in root_dir.glob('**/'):
        if path.is_dir() and not path.name.startswith('.'):
            init_file = path / "__init__.py"
            if not init_file.exists():
                with open(init_file, 'w') as f:
                    f.write(f'"""\n{path.name} package.\n"""\n')
                logger.debug(f"Created {init_file}")

def find_games_in_pgn_file(pgn_file: str, username: str) -> List[Tuple[str, bool]]:
    """Find games for a specific player in a PGN file.
    
    Args:
        pgn_file (str): Path to the PGN file.
        username (str): Username to search for.
        
    Returns:
        List[Tuple[str, bool]]: List of (pgn_text, color) tuples.
    """
    if not os.path.exists(pgn_file):
        logger.error(f"PGN file not found: {pgn_file}")
        return []
    
    games = []
    username_lower = username.lower()
    
    try:
        with open(pgn_file, 'r') as f:
            pgn_content = f.read()
            
        # Split the file into individual games
        game_texts = pgn_content.split("\n\n\n")
        
        for game_text in game_texts:
            # Check if this game contains the username
            if username_lower in game_text.lower():
                # Determine the color
                white_match = re.search(r'\[White\s+"([^"]+)"\]', game_text)
                black_match = re.search(r'\[Black\s+"([^"]+)"\]', game_text)
                
                white = white_match.group(1) if white_match else ""
                black = black_match.group(1) if black_match else ""
                
                if username_lower == white.lower():
                    games.append((game_text, chess.WHITE))
                elif username_lower == black.lower():
                    games.append((game_text, chess.BLACK))
        
        logger.info(f"Found {len(games)} games for {username} in {pgn_file}")
        return games
    
    except Exception as e:
        logger.error(f"Error reading PGN file {pgn_file}: {e}")
        return []
