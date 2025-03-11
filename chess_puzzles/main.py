#!/usr/bin/env python3
"""
Main entry point for the chess puzzles generator.

This script analyzes chess games to find blunders and generate puzzles.
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

import chess

from chess_puzzles import config
from chess_puzzles.engine.stockfish import StockfishEngine
from chess_puzzles.game.fetcher import GameFetcher
from chess_puzzles.analysis.position import PositionAnalyzer
from chess_puzzles.puzzle.generator import PuzzleGenerator
from chess_puzzles.utils.helpers import (
    setup_logging,
    format_time,
    get_game_statistics,
    create_init_files,
    find_games_in_pgn_file
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Generate chess puzzles from online games.')
    
    # Basic options
    parser.add_argument('--username', type=str, 
                        help=f'Username to fetch games for (default: {config.USERNAME})')
    parser.add_argument('--platform', type=str, choices=['lichess', 'chess.com'],
                        help=f'Platform to fetch games from (default: {config.PLATFORM})')
    parser.add_argument('--output', type=str,
                        help=f'Output file for generated puzzles (default: {config.OUTPUT_FILE})')
    
    # Engine options
    parser.add_argument('--stockfish-path', type=str, 
                        help='Path to Stockfish executable (will download if not provided)')
    parser.add_argument('--time-limit', type=float,
                        help=f'Time limit for Stockfish analysis per position in seconds (default: {config.DEFAULT_TIME_LIMIT})')
    parser.add_argument('--depth', type=int,
                        help=f'Depth for Stockfish analysis (default: {config.DEFAULT_DEPTH})')
    
    # Game fetching options
    parser.add_argument('--count', type=int,
                        help=f'Number of recent games to analyze (default: {config.MAX_GAMES})')
    parser.add_argument('--pgn', type=str,
                        help='Analyze games from a local PGN file instead of fetching from online')
    parser.add_argument('--min-moves', type=int,
                        help=f'Minimum number of moves a game must have (default: {config.MIN_MOVES})')
    
    # Analysis options
    parser.add_argument('--strictness', type=str, 
                        choices=['strict', 'standard', 'relaxed', 'all'],
                        help='Strictness level for blunder detection (default: standard)')
    parser.add_argument('--blunder-threshold', type=int,
                        help=f'Threshold for blunder detection in centipawns (default: {config.BLUNDER_THRESHOLD})')
    parser.add_argument('--log-all-evaluations', action='store_true',
                        help='Log evaluations for all positions, not just blunders')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress all output except errors')
    parser.add_argument('--log-file', type=str,
                        help='Log to the specified file')
    
    return parser.parse_args()

def initialize_config(args):
    """Initialize configuration based on command-line arguments.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        
    Returns:
        dict: Updated configuration dictionary.
    """
    # Create a config dictionary with default values
    cfg = {
        'username': config.USERNAME,
        'platform': config.PLATFORM,
        'output_file': config.OUTPUT_FILE,
        'stockfish_path': config.STOCKFISH_PATH,
        'time_limit': config.DEFAULT_TIME_LIMIT,
        'depth': config.DEFAULT_DEPTH,
        'count': config.MAX_GAMES,
        'min_moves': config.MIN_MOVES,
        'strictness': 'standard',
        'blunder_threshold': config.BLUNDER_THRESHOLD,
        'log_all_evaluations': config.LOG_ALL_EVALUATIONS,
        'verbose': False,
        'quiet': False,
        'pgn_file': None,
        'log_file': None
    }
    
    # Update with command-line arguments
    for key, value in vars(args).items():
        if value is not None:  # Only update if argument was provided
            if key == 'pgn':
                cfg['pgn_file'] = value
            else:
                cfg[key] = value
    
    # Set environment variables for compatibility
    os.environ['CHESS_USERNAME'] = cfg['username']
    os.environ['CHESS_PLATFORM'] = cfg['platform']
    os.environ['OUTPUT_FILE'] = cfg['output_file']
    if cfg['stockfish_path']:
        os.environ['STOCKFISH_PATH'] = cfg['stockfish_path']
    os.environ['DEFAULT_TIME_LIMIT'] = str(cfg['time_limit'])
    os.environ['DEFAULT_DEPTH'] = str(cfg['depth'])
    os.environ['MAX_GAMES'] = str(cfg['count'])
    os.environ['MIN_MOVES'] = str(cfg['min_moves'])
    os.environ['BLUNDER_THRESHOLD'] = str(cfg['blunder_threshold'])
    os.environ['LOG_ALL_EVALUATIONS'] = str(cfg['log_all_evaluations'])
    
    return cfg

def process_games(games, cfg, engine, puzzles=None, evaluations=None):
    """Process a list of games to find blunders and generate puzzles.
    
    Args:
        games (list): List of game data dictionaries.
        cfg (dict): Configuration dictionary.
        engine (StockfishEngine): Stockfish engine instance.
        puzzles (list, optional): List to append puzzles to. Defaults to None.
        evaluations (list, optional): List to append evaluations to. Defaults to None.
        
    Returns:
        tuple: Lists of (puzzles, evaluations).
    """
    if puzzles is None:
        puzzles = []
    if evaluations is None:
        evaluations = []
    
    # Create position analyzer
    analyzer = PositionAnalyzer(
        engine=engine,
        username=cfg['username'],
        strictness=cfg['strictness']
    )
    
    # Process each game
    for i, game in enumerate(games):
        logger.info(f"Processing game {i+1} of {len(games)}")
        
        # Determine player color
        if isinstance(game, tuple) and len(game) == 2:
            # Format from PGN file: (pgn_text, color)
            pgn_text, player_color = game
            game_url = f"local_pgn_{i}"
        else:
            # Format from online platforms
            pgn_text = game.get('pgn', '')
            
            # Get game URL
            game_url = game.get('url')
            if not game_url and game.get('id'):
                game_url = f"https://lichess.org/{game.get('id')}"
            
            # Determine player color
            player_color, color_str = GameFetcher(cfg['username']).determine_player_color(game)
            if player_color is None:
                logger.warning(f"Could not determine {cfg['username']}'s color. Skipping game.")
                continue
            
            logger.info(f"{cfg['username']} is playing as {'WHITE' if player_color == chess.WHITE else 'BLACK'}")
        
        # Analyze the game for blunders
        game_blunders, game_evaluations = analyzer.analyze_game(
            pgn_text=pgn_text, 
            game_url=game_url, 
            player_color=player_color, 
            verbose=cfg['verbose'], 
            time_limit=cfg['time_limit']
        )
        
        # Add blunders to the list of puzzles
        if game_blunders:
            puzzles.extend(game_blunders)
            logger.info(f"Found {len(game_blunders)} blunders in game {game_url}")
        else:
            logger.info(f"No puzzles found in game {game_url}")
            
        # Save position evaluations
        if game_evaluations:
            evaluations.extend(game_evaluations)
            analyzer.save_position_evaluations(
                game_evaluations, 
                game_id=game_url.split('/')[-1] if isinstance(game_url, str) else f"game_{i}", 
                export_evaluations=True, 
                verbose=cfg['verbose']
            )
    
    return puzzles, evaluations

def main():
    """Main entry point."""
    start_time = time.time()
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize config
    cfg = initialize_config(args)
    
    # Setup logging
    log_level = "DEBUG" if cfg['verbose'] else ("ERROR" if cfg['quiet'] else "INFO")
    setup_logging(log_level=log_level, log_file=cfg['log_file'])
    
    # Create __init__.py files to ensure proper imports
    create_init_files(Path(__file__).parent)
    
    logger.info(f"Starting chess puzzle generator for {cfg['username']} on {cfg['platform']}")
    
    # Load existing puzzles if the file exists
    puzzle_generator = PuzzleGenerator(cfg['username'], cfg['platform'])
    existing_data = puzzle_generator.load_existing_puzzles(cfg['output_file'])
    
    # Get a set of already analyzed game URLs
    already_analyzed_games = set()
    for puzzle in existing_data.get('puzzles', []):
        if 'game_url' in puzzle and not puzzle.get('is_placeholder', False):
            already_analyzed_games.add(puzzle['game_url'])
    
    logger.info(f"Found {len(already_analyzed_games)} previously analyzed games")
    
    # Initialize the Stockfish engine
    engine = StockfishEngine(cfg['stockfish_path'])
    
    # Test the engine
    if not engine.test():
        logger.error("Stockfish engine test failed. Exiting.")
        return 1
    
    all_puzzles = []
    all_evaluations = []
    
    try:
        with engine:  # Use context manager to ensure engine is closed
            if cfg['pgn_file']:
                # Use local PGN file
                logger.info(f"Using local PGN file: {cfg['pgn_file']}")
                games = find_games_in_pgn_file(cfg['pgn_file'], cfg['username'])
                
                # Filter games that have already been analyzed
                games = [game for game in games if game.get('game_url') not in already_analyzed_games]
                logger.info(f"Found {len(games)} new games to analyze in PGN file")
                
                all_puzzles, all_evaluations = process_games(games, cfg, engine)
            else:
                # Fetch games from online platform
                game_fetcher = GameFetcher(username=cfg['username'], platform=cfg['platform'])
                
                # Fetch games, filtering out already analyzed ones
                games = game_fetcher.fetch_games(
                    max_games=cfg['count'],
                    already_analyzed_games=already_analyzed_games
                )
                
                logger.info(f"Fetched {len(games)} new games from {cfg['platform']} to analyze\n")
                
                if not games:
                    logger.warning(f"No new games found for {cfg['username']} on {cfg['platform']}")
                    # Generate the puzzles anyway to ensure the puzzle file is updated with the current timestamp
                    puzzle_generator.generate_puzzles([], cfg['output_file'])
                    return 0
                
                all_puzzles, all_evaluations = process_games(games, cfg, engine)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Saving current results...")
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        # Still try to save any puzzles found so far
    finally:
        # Generate puzzles from found blunders
        if all_puzzles:
            # Save main puzzles file, appending to existing puzzles
            puzzle_generator.generate_puzzles(all_puzzles, cfg['output_file'])
            
            # Save additional themed puzzles
            puzzle_generator.save_puzzle_theme_data(all_puzzles)
            
            # Show statistics
            stats = get_game_statistics(all_puzzles)
            logger.info(f"\nFound {stats['count']} new puzzles")
            if stats['count'] > 0:
                logger.info(f"Difficulty distribution: {stats['difficulty_distribution']}")
                logger.info(f"Average evaluation change: {stats['avg_eval_change']:.1f} centipawns")
                logger.info(f"Moves range: {stats['earliest_move']} - {stats['latest_move']}")
        else:
            # Just save an updated file with no new puzzles added
            puzzle_generator.generate_puzzles([], cfg['output_file'])
            logger.warning("No puzzles were found in any games")
    
    # Show total execution time
    elapsed_time = time.time() - start_time
    logger.info(f"Total execution time: {format_time(elapsed_time)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
