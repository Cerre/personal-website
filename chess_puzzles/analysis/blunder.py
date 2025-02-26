"""
Blunder detection module.

This module provides logic for detecting blunders in chess positions
based on evaluation changes.
"""
import chess
import logging
from typing import Dict, Tuple, Optional

from chess_puzzles import config

logger = logging.getLogger(__name__)

class BlunderDetector:
    """Detects blunders in chess positions based on evaluation changes."""
    
    def __init__(self, strictness: str = "standard"):
        """Initialize the blunder detector.
        
        Args:
            strictness (str, optional): Strictness level for blunder detection.
                Options: "strict", "standard", "relaxed", "all".
                Defaults to "standard".
        """
        self.set_strictness(strictness)
    
    def set_strictness(self, strictness: str):
        """Set the strictness level for blunder detection.
        
        Args:
            strictness (str): Strictness level. Options: "strict", "standard", "relaxed", "all".
            
        Raises:
            ValueError: If an invalid strictness level is provided.
        """
        if strictness not in config.STRICTNESS_LEVELS:
            valid_levels = ", ".join(config.STRICTNESS_LEVELS.keys())
            raise ValueError(f"Invalid strictness level: {strictness}. Valid levels: {valid_levels}")
            
        self.strictness = strictness
        self.equal_range = config.STRICTNESS_LEVELS[strictness]["equal_range"]
        self.terrible_threshold = config.STRICTNESS_LEVELS[strictness]["terrible_threshold"]
        logger.info(f"Set blunder detection strictness to {strictness}")
    
    def is_blunder(self, prev_eval: int, curr_eval: int, player_color: bool) -> Tuple[bool, Optional[str]]:
        """Determine if a move is a blunder based on evaluation change.
        
        Args:
            prev_eval (int): Evaluation before the move (in centipawns).
            curr_eval (int): Evaluation after the move (in centipawns).
            player_color (bool): The color of the player (chess.WHITE or chess.BLACK).
            
        Returns:
            Tuple[bool, Optional[str]]: (is_blunder, blunder_type) - Whether it's a blunder and what type.
        """
        # Simplified blunder detection logic:
        # 1. Initial position must be roughly equal (-200 to 200)
        is_initial_equal = -200 <= prev_eval <= 200
        
        # 2. Evaluation change must be significant (at least 500 points)
        # For white, negative change is bad; for black, positive change is bad
        eval_change = prev_eval - curr_eval
        
        # 3. Check if it's a blunder based on player color and eval change
        is_blunder_detected = False
        if is_initial_equal:
            if player_color == chess.WHITE and eval_change <= -500:
                is_blunder_detected = True
            elif player_color == chess.BLACK and eval_change >= 500:
                is_blunder_detected = True
        
        if is_blunder_detected:
            return True, "blunder"
        
        return False, None
        
    def calculate_difficulty(self, eval_change: int) -> int:
        """Calculate puzzle difficulty based on evaluation change.
        
        Args:
            eval_change (int): The absolute evaluation change in centipawns.
            
        Returns:
            int: Difficulty level from 1 (Very Easy) to 5 (Advanced).
        """
        if eval_change >= 1500:
            return 1  # Very Easy
        elif eval_change >= 1200:
            return 2  # Easy  
        elif eval_change >= 900:
            return 3  # Intermediate
        elif eval_change >= 600:
            return 4  # Challenging
        else:
            return 5  # Advanced
            
    def get_difficulty_label(self, difficulty: int) -> str:
        """Get a text label for a difficulty level.
        
        Args:
            difficulty (int): Difficulty level from 1-5.
            
        Returns:
            str: Text label for the difficulty.
        """
        labels = {
            1: "Very Easy",
            2: "Easy",
            3: "Intermediate",
            4: "Challenging",
            5: "Advanced"
        }
        return labels.get(difficulty, "Unknown")
        
    def analyze_potential_blunders(self, evaluations, threshold=None):
        """Analyze evaluation data to find potential blunders using different criteria.
        
        Args:
            evaluations (List[Dict]): List of position evaluation data.
            threshold (int, optional): Custom threshold for detecting blunders.
                Defaults to config.BLUNDER_THRESHOLD.
            
        Returns:
            List[Dict]: List of potential blunders found.
        """
        threshold = threshold or config.BLUNDER_THRESHOLD
        potential_blunders = []
        
        for eval_data in evaluations:
            # Skip already identified blunders
            if eval_data.get("is_blunder", False):
                continue
                
            # Apply different criteria to find more subtle blunders
            eval_change = eval_data.get("eval_change", 0)
            prev_eval = eval_data.get("prev_eval", 0)
            
            if abs(eval_change) >= threshold / 2 and abs(prev_eval) < 500:
                eval_data["blunder_type"] = "moderate"
                potential_blunders.append(eval_data)
            elif abs(eval_change) >= threshold / 3 and abs(prev_eval) < 300:
                eval_data["blunder_type"] = "subtle"
                potential_blunders.append(eval_data)
        
        return potential_blunders
