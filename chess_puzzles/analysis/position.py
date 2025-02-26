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
        
    def analyze_game(self, pgn_text: str, game_url: str, player_color: bool, 
                   verbose: bool = False, time_limit: float = config.DEFAULT_TIME_LIMIT) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Analyze a game to find blunders and generate puzzles.
        
        Args:
            pgn_text (str): The PGN text of the game to analyze.
            game_url (str): URL of the game being analyzed.
            player_color (bool): The color of the player we're analyzing for blunders (chess.WHITE or chess.BLACK).
            verbose (bool, optional): Whether to print detailed output. Defaults to False.
            time_limit (float, optional): Time to let engine think per position in seconds. 
                Defaults to config.DEFAULT_TIME_LIMIT.
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (blunders, position_evaluations)
        """
        # Validate input parameters
        if not pgn_text:
            logger.warning(f"Empty PGN for game {game_url}")
            return [], []
            
        if player_color is None:
            logger.warning(f"Player color not provided for game {game_url}")
            return [], []
        
        logger.info(f"Analyzing game {game_url}")
        logger.info(f"Player color is {'WHITE' if player_color == chess.WHITE else 'BLACK'}")
        
        # Parse PGN
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        
        if not game:
            logger.warning(f"Could not parse PGN for game {game_url}")
            return [], []
        
        blunders = []
        position_evaluations = []  # Store all position evaluations
        board = game.board()
        
        # Extract game ID from URL if possible
        game_id = game_url.split('/')[-1] if game_url else "unknown_game"
        
        # Process each move
        node = game.next()
        move_number = 1
        moves_analyzed = 0
        
        while node:
            try:
                # Only analyze when it's player's turn
                is_player_turn = (board.turn == player_color)
                
                if is_player_turn:
                    # Get position before the move
                    prev_fen = board.fen()
                    
                    # Evaluate current position 
                    initial_eval = self.engine.evaluate_position(board, time_limit=time_limit)
                    # Handle case when engine evaluation returns None
                    if initial_eval is None:
                        logger.warning(f"Engine returned None evaluation for position before move {move_number}")
                        prev_eval = 0
                    else:
                        prev_eval = initial_eval
                    
                    # Save the board before making the move
                    prev_position_board = board.copy()
                    
                    # Make the move
                    move = node.move
                    san_move = board.san(move)
                    
                    # Store the UCI notation of the move before making it
                    blundered_move_uci = move.uci()
                    
                    board.push(move)
                    
                    # Save the position after the blunder
                    post_blunder_fen = board.fen()
                    post_blunder_board = board.copy()
                    
                    # Evaluate new position
                    new_eval = self.engine.evaluate_position(board, time_limit=time_limit)
                    # Handle case when engine evaluation returns None
                    if new_eval is None:
                        logger.warning(f"Engine returned None evaluation at move {move_number}.{san_move}")
                        curr_eval = 0
                    else:
                        curr_eval = -new_eval
                    
                    # Calculate evaluation change
                    eval_change = prev_eval - curr_eval
                    
                    if verbose:
                        logger.info(f"Move {move_number}.{san_move} - Prev eval: {prev_eval}, Curr eval: {curr_eval}, Change: {eval_change}")
                    
                    # Check if it's a blunder
                    is_blunder, blunder_type = self.blunder_detector.is_blunder(prev_eval, curr_eval, player_color)
                    
                    # Create position evaluation data
                    player_turn = "white" if player_color == chess.WHITE else "black"
                    position_data = self._create_position_data(
                        game_id=game_id,
                        move_number=move_number,
                        fen=prev_fen,
                        player_turn=player_turn,
                        move_san=san_move,
                        prev_eval=prev_eval,
                        curr_eval=curr_eval,
                        eval_change=eval_change,
                        is_blunder=is_blunder,
                        blunder_type=blunder_type
                    )
                    position_evaluations.append(position_data)
                    
                    # If it's a blunder, find the best move for the opponent to punish the blunder
                    if is_blunder:
                        # Find best move in the position AFTER the blunder
                        punishment_move = self.engine.find_best_move(post_blunder_board, time_limit=time_limit)
                        
                        # For reference, also find what would have been the best move
                        correct_move = self.engine.find_best_move(prev_position_board, time_limit=time_limit)
                        correct_move_uci = correct_move.uci() if correct_move else None
                        
                        if punishment_move:
                            # Convert Move object to UCI string
                            punishment_move_uci = punishment_move.uci()
                            
                            # Create blunder data
                            blunder_data = self._create_blunder_data(
                                post_blunder_fen=post_blunder_fen,  # Use position AFTER the blunder
                                pre_blunder_fen=prev_fen,          # Include position BEFORE the blunder
                                punishment_move_uci=punishment_move_uci,  # Best move to punish the blunder
                                correct_move_uci=correct_move_uci,  # For reference only
                                player_color=player_turn,
                                move_number=move_number,
                                blundered_move=san_move,
                                blundered_move_uci=blundered_move_uci,  # Pass the UCI notation
                                eval_change=abs(eval_change),
                                game_url=game_url,
                                blunder_type=blunder_type
                            )
                            blunders.append(blunder_data)
                            logger.info(f"Found blunder at move {move_number}.{san_move}. Eval change: {eval_change}")
                else:
                    # Just make the move if it's not player's turn
                    board.push(node.move)
                
                # Move to next node
                node = node.next()
                
                # Update move number
                if board.turn == chess.WHITE:
                    move_number += 1
                
                moves_analyzed += 1
                
            except Exception as e:
                logger.error(f"Error analyzing move {move_number}: {e}")
                logger.error(traceback.format_exc())
                # Continue with next move
                node = node.next()
                if board.turn == chess.WHITE:
                    move_number += 1
        
        logger.info(f"Analyzed {moves_analyzed} moves and found {len(blunders)} blunders")
        return blunders, position_evaluations
        
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
