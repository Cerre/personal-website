"""
Puzzle generator module.

This module handles creating puzzles from detected blunders and saving them to files.
"""
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from chess_puzzles import config

logger = logging.getLogger(__name__)

class PuzzleGenerator:
    """Generates chess puzzles from detected blunders."""
    
    def __init__(self, username: str, platform: str = "lichess"):
        """Initialize the puzzle generator.
        
        Args:
            username (str): Username of the player.
            platform (str, optional): Platform the games are from. Defaults to "lichess".
        """
        self.username = username
        self.platform = platform
        
    def generate_puzzles(self, blunders: List[Dict[str, Any]], 
                        output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate puzzles from detected blunders and save them to a file.
        
        Args:
            blunders (List[Dict[str, Any]]): List of detected blunders.
            output_file (Optional[str], optional): Path to save the puzzles to.
                Defaults to None, which will use the default output file.
                
        Returns:
            Dict[str, Any]: Generated puzzles data.
        """
        if output_file is None:
            output_file = config.OUTPUT_FILE
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        output = self._prepare_puzzle_output(blunders)
        
        # Save puzzles to JSON file
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved {len(output['puzzles'])} puzzles to {output_file}")
        return output
        
    def _prepare_puzzle_output(self, blunders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare the puzzle output structure.
        
        Args:
            blunders (List[Dict[str, Any]]): List of detected blunders.
            
        Returns:
            Dict[str, Any]: Structured puzzle output.
        """
        # Output data structure
        output = {
            "puzzles": blunders,
            "count": len(blunders),
            "generated_at": datetime.now().isoformat(),
            "username": self.username,
            "platform": self.platform
        }
        
        # If no puzzles were found, add a placeholder puzzle
        if not blunders:
            logger.info("No puzzles generated, adding a placeholder puzzle")
            output["puzzles"] = [self._create_placeholder_puzzle()]
            output["count"] = 1
            output["is_placeholder"] = True
            output["message"] = "No blunders found in recent games. This is a placeholder puzzle."
            
        return output
        
    def _create_placeholder_puzzle(self) -> Dict[str, Any]:
        """Create a placeholder puzzle when no real puzzles are found.
        
        Returns:
            Dict[str, Any]: Placeholder puzzle data.
        """
        return {
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
            "solution": ["e8f7"],  # Kf7 is the only legal move
            "player_color": "black",
            "move_number": 3,
            "blundered_move": "Nc6",
            "eval_change": 900,
            "difficulty": 2,
            "difficulty_label": "Easy",
            "game_url": "https://lichess.org/learn#/4",
            "is_placeholder": True
        }
        
    def save_puzzle_theme_data(self, 
                             blunders: List[Dict[str, Any]], 
                             output_file: Optional[str] = None) -> None:
        """Save additional themed puzzle data for specialized collections.
        
        Args:
            blunders (List[Dict[str, Any]]): List of detected blunders.
            output_file (Optional[str], optional): Path to save the themed puzzles to.
                Defaults to None, which will generate a themed filename.
        """
        if not blunders:
            return
            
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = config.PUZZLE_DIR / f"themed_puzzles_{timestamp}.json"
            
        # Group puzzles by difficulty
        difficulty_groups = {}
        for puzzle in blunders:
            difficulty = puzzle.get("difficulty", 3)
            if difficulty not in difficulty_groups:
                difficulty_groups[difficulty] = []
            difficulty_groups[difficulty].append(puzzle)
            
        # Group puzzles by blunder type
        blunder_type_groups = {}
        for puzzle in blunders:
            blunder_type = puzzle.get("blunder_type", "unknown")
            if blunder_type not in blunder_type_groups:
                blunder_type_groups[blunder_type] = []
            blunder_type_groups[blunder_type].append(puzzle)
            
        # Prepare themed output
        themed_output = {
            "by_difficulty": {
                str(diff): {
                    "puzzles": puzzles,
                    "count": len(puzzles)
                } for diff, puzzles in difficulty_groups.items()
            },
            "by_blunder_type": {
                blunder_type: {
                    "puzzles": puzzles,
                    "count": len(puzzles)
                } for blunder_type, puzzles in blunder_type_groups.items()
            },
            "total_count": len(blunders),
            "generated_at": datetime.now().isoformat(),
            "username": self.username
        }
        
        # Save themed puzzles
        with open(output_file, 'w') as f:
            json.dump(themed_output, f, indent=2)
            
        logger.info(f"Saved themed puzzle data with {len(blunders)} puzzles to {output_file}")
