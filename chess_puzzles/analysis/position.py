"""
Position analysis module.

This module handles analyzing chess positions and detecting blunders.
"""
import io
import json
import logging
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import chess
import chess.pgn

from chess_puzzles import config
from chess_puzzles.engine.stockfish import StockfishEngine
from chess_puzzles.analysis.blunder import BlunderDetector

logger = logging.getLogger(__name__)

class PositionAnalyzer:
    """Analyzes chess positions to find blunders and tactical opportunities."""
    
    def __init__(self, engine: StockfishEngine, username: str, strictness: str = "standard"):
        """Initialize the position analyzer.
        
        Args:
            engine (StockfishEngine): The chess engine to use for analysis.
            username (str): The username of the player whose games are being analyzed.
            strictness (str, optional): Strictness level for blunder detection.
                Defaults to "standard".
        """
        self.engine = engine
        self.username = username
        self.blunder_detector = BlunderDetector(strictness)
        
    def set_strictness(self, strictness: str):
        """Set the strictness level for blunder detection.
        
        Args:
            strictness (str): Strictness level.
        """
        self.blunder_detector.set_strictness(strictness)
        
    def analyze_game(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        game_id = game.get("id", "")
        game_url = game.get("url", "")
        pgn_text = game.get("pgn", "")
        
        if not pgn_text or not game_id:
            logger.warning(f"Missing PGN or game ID, skipping game")
            return []
            
        try:
            # Parse PGN
            pgn = io.StringIO(pgn_text)
            game_obj = chess.pgn.read_game(pgn)
            if not game_obj:
                logger.warning(f"Failed to parse PGN, skipping game")
                return []
            
            # Determine player color - case insensitive comparison
            player_color = None
            white_player = game_obj.headers.get("White", "").lower()
            black_player = game_obj.headers.get("Black", "").lower()
            
            if self.username.lower() == white_player:
                player_color = chess.WHITE
                logger.info(f"Player is WHITE in game {game_id}")
            elif self.username.lower() == black_player:
                player_color = chess.BLACK
                logger.info(f"Player is BLACK in game {game_id}")
            
            if player_color is None:
                logger.warning(f"Could not determine player color for game {game_id}. White: {white_player}, Black: {black_player}")
                return []
            
            # Analyze positions
            board = game_obj.board()
            blunders = []
            
            # Store evaluations for each position
            prev_eval = None
            move_number = 0
            is_player_turn = board.turn == player_color
            
            for node in game_obj.mainline():
                move = node.move
                move_uci = move.uci()
                move_san = board.san(move)
                
                # Only analyze positions where it's the player's turn
                if is_player_turn:
                    # Store current position before making the move
                    current_fen = board.fen()
                    
                    # Evaluate position before the move
                    if prev_eval is None:
                        result = self.engine.analyze_position(board.fen())
                        prev_eval = result.get("score", 0)
                    
                    # Make the move
                    board.push(move)
                    
                    # Evaluate position after the move
                    result = self.engine.analyze_position(board.fen())
                    curr_eval = result.get("score", 0)
                    
                    # Check if it's a blunder
                    is_blunder = self.blunder_detector.is_blunder(prev_eval, curr_eval, player_color)
                    
                    if is_blunder:
                        # Get the best move in the position before the blunder
                        board.pop()  # Go back to position before the move
                        best_move_result = self.engine.get_best_move(board.fen())
                        correct_move_uci = best_move_result.get("bestmove")
                        
                        # Validate that the suggested move is legal
                        correct_move_san = ""
                        if correct_move_uci:
                            try:
                                correct_move = chess.Move.from_uci(correct_move_uci)
                                if correct_move in board.legal_moves:
                                    correct_move_san = board.san(correct_move)
                                else:
                                    logger.warning(f"Move {correct_move_uci} suggested by Stockfish is not legal in position {board.fen()}")
                            except ValueError:
                                logger.warning(f"Invalid UCI move: {correct_move_uci}")
                        
                        board.push(move)  # Re-apply the actual move
                        
                        # Create blunder data
                        blunder_data = {
                            "fen": current_fen,
                            "moves": [move_uci, correct_move_uci] if correct_move_uci else [move_uci],
                            "game_id": game_id,
                            "game_url": game_url,
                            "player_move": move_san,
                            "correct_move": correct_move_san,
                            "eval_before": prev_eval,
                            "eval_after": curr_eval,
                            "move_number": move_number // 2 + 1,
                            "player_color": "white" if player_color == chess.WHITE else "black",
                        }
                        blunders.append(blunder_data)
                    
                    # Update for next move
                    prev_eval = curr_eval
                else:
                    # Just make the move
                    board.push(move)
                    prev_eval = None  # Reset eval since opponent moved
                
                # Update turn
                move_number += 1
                is_player_turn = board.turn == player_color
            
            return blunders
            
        except Exception as e:
            logger.exception(f"Error analyzing game {game_id}: {e}")
            return []
        
    def _create_position_data(self, game_id: str, move_number: int, fen: str, player_turn: str, 
                            move_san: str, prev_eval: int, curr_eval: int, eval_change: int, 
                            is_blunder: bool, blunder_type: Optional[str] = None) -> Dict[str, Any]:
        """Create structured data for a position evaluation.
        
        Args:
            game_id (str): ID of the game.
            move_number (int): Move number in the game.
            fen (str): FEN of the position.
            player_turn (str): The player who made the move ("white" or "black").
            move_san (str): The move in SAN notation.
            prev_eval (int): Evaluation before the move.
            curr_eval (int): Evaluation after the move.
            eval_change (int): The change in evaluation.
            is_blunder (bool): Whether the move is a blunder.
            blunder_type (Optional[str], optional): Type of blunder if applicable. Defaults to None.
            
        Returns:
            Dict[str, Any]: Position evaluation data.
        """
        return {
            "game_id": game_id,
            "move_number": move_number,
            "fen": fen,
            "player_turn": player_turn,
            "move_san": move_san,
            "prev_eval": prev_eval,
            "curr_eval": curr_eval, 
            "eval_change": eval_change,
            "is_blunder": is_blunder,
            "blunder_type": blunder_type,
            "timestamp": datetime.now().isoformat()
        }
        
    def _create_blunder_data(self, post_blunder_fen: str, punishment_move_uci: str, player_color: str, 
                           move_number: int, blundered_move: str, eval_change: int, 
                           game_url: str, correct_move_uci: Optional[str] = None,
                           blundered_move_uci: Optional[str] = None,
                           pre_blunder_fen: Optional[str] = None,
                           blunder_type: Optional[str] = None) -> Dict[str, Any]:
        """Create a structured blunder data object.
        
        Args:
            post_blunder_fen (str): FEN of the position after the blunder.
            punishment_move_uci (str): The best move to punish the blunder in UCI notation.
            player_color (str): The color of the player ("white" or "black").
            move_number (int): Move number in the game.
            blundered_move (str): The blundered move in SAN notation.
            eval_change (int): The absolute change in evaluation.
            game_url (str): URL of the game.
            correct_move_uci (Optional[str], optional): The move that should have been played instead of the blunder. For reference only.
            blundered_move_uci (Optional[str], optional): The blundered move in UCI notation for animation purposes.
            pre_blunder_fen (Optional[str], optional): FEN of the position before the blunder.
            blunder_type (Optional[str], optional): Type of blunder. Defaults to None.
            
        Returns:
            Dict[str, Any]: Blunder data.
        """
        difficulty = self.blunder_detector.calculate_difficulty(eval_change)
        difficulty_label = self.blunder_detector.get_difficulty_label(difficulty)
        
        # Determine the opponent's color (the solver's color in the puzzle)
        opponent_color = "black" if player_color == "white" else "white"
        
        return {
            "fen": post_blunder_fen,  # Position AFTER the blunder
            "pre_blunder_fen": pre_blunder_fen,  # Position BEFORE the blunder
            "solution": [punishment_move_uci],  # Best move to punish the blunder
            "player_color": opponent_color,  # The puzzle is solved from the opponent's perspective
            "original_player_color": player_color,  # For reference
            "move_number": move_number,
            "blundered_move": blundered_move,
            "blundered_move_uci": blundered_move_uci,  # Include UCI format for animation
            "correct_move": correct_move_uci,  # What should have been played instead (for reference)
            "eval_change": eval_change,
            "difficulty": difficulty,
            "difficulty_label": difficulty_label,
            "blunder_type": blunder_type,
            "game_url": game_url,
            "timestamp": datetime.now().isoformat(),
            "show_solution_text": False  # Flag to prevent the widget from showing solution text
        }
        
    def save_position_evaluations(self, position_evaluations: List[Dict[str, Any]], game_id: str,
                                export_evaluations: bool = True, verbose: bool = False) -> None:
        """Save position evaluations to files.
        
        Args:
            position_evaluations (List[Dict[str, Any]]): List of position evaluation data.
            game_id (str): ID of the game.
            export_evaluations (bool, optional): Whether to export evaluations to files.
                Defaults to True.
            verbose (bool, optional): Whether to print detailed output. Defaults to False.
        """
        if not export_evaluations or not position_evaluations:
            return
            
        # Create a filename using the game ID
        game_output_file = config.EVAL_DIR / f"evaluations_{game_id}.json"
        
        with open(game_output_file, 'w') as f:
            json.dump({
                "game_id": game_id, 
                "evaluations": position_evaluations,
                "count": len(position_evaluations),
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
            
        if verbose:
            logger.info(f"Saved {len(position_evaluations)} position evaluations for game {game_id} to {game_output_file}")
        
        # Combine with global evaluations
        try:
            global_eval_file = config.EVAL_LOG_FILE
            
            # If the global evaluation file exists, append to it
            if os.path.exists(global_eval_file):
                with open(global_eval_file, 'r') as f:
                    existing_data = json.load(f)
                    existing_evals = existing_data.get("evaluations", [])
                    
                # Append new evaluations
                existing_evals.extend(position_evaluations)
                
                # Save back to file
                with open(global_eval_file, 'w') as f:
                    json.dump({
                        "evaluations": existing_evals,
                        "count": len(existing_evals),
                        "last_updated": datetime.now().isoformat(),
                        "username": self.username
                    }, f, indent=2)
                logger.info(f"Updated global evaluation file with {len(position_evaluations)} new evaluations")
            else:
                # Create new file if it doesn't exist
                self.save_evaluations_to_file(position_evaluations)
        except Exception as e:
            logger.error(f"Error updating global evaluation file: {e}")
            logger.error(traceback.format_exc())
            # Still save this game's evaluations as a backup
            backup_file = config.EVAL_DIR / f"eval_backup_{game_id}.json"
            self.save_evaluations_to_file(position_evaluations, backup_file)
            
    def save_evaluations_to_file(self, evaluations: List[Dict[str, Any]], 
                              output_file: str = config.EVAL_LOG_FILE) -> None:
        """Save position evaluations to a JSON file.
        
        Args:
            evaluations (List[Dict[str, Any]]): List of position evaluation data.
            output_file (str, optional): Path to the output file.
                Defaults to config.EVAL_LOG_FILE.
        """
        output = {
            "evaluations": evaluations,
            "count": len(evaluations),
            "generated_at": datetime.now().isoformat(),
            "settings": {
                "thinking_time": f"{config.DEFAULT_TIME_LIMIT} seconds",
                "depth": f"{config.DEFAULT_DEPTH}",
                "username": self.username
            }
        }
        
        # Ensure directory exists, but only if output_file has a directory part
        dir_name = os.path.dirname(output_file)
        if dir_name:  # Only try to create the directory if it's not empty
            os.makedirs(dir_name, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved {len(evaluations)} position evaluations to {output_file}")
