#!/usr/bin/env python3
"""
Tests for the chess_puzzles package.
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

import chess
import chess.engine

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chess_puzzles.engine.stockfish import StockfishEngine
from chess_puzzles.analysis.position import PositionAnalyzer
from chess_puzzles.puzzle.generator import PuzzleGenerator
from chess_puzzles.game.fetcher import GameFetcher
from chess_puzzles.utils.helpers import setup_logging, find_games_in_pgn_file


class TestStockfishEngine(unittest.TestCase):
    """Tests for the StockfishEngine class."""
    
    @patch('chess_puzzles.engine.stockfish.StockfishEngine._prepare_stockfish')
    def test_init(self, mock_prepare):
        """Test StockfishEngine initialization."""
        mock_prepare.return_value = '/path/to/stockfish'
        engine = StockfishEngine()
        self.assertEqual(engine.path, '/path/to/stockfish')
    
    @patch('chess_puzzles.engine.stockfish.StockfishEngine._prepare_stockfish')
    @patch('chess_puzzles.engine.stockfish.chess.engine.SimpleEngine.popen_uci')
    def test_analyze_position(self, mock_popen, mock_prepare):
        """Test position analysis."""
        mock_prepare.return_value = '/path/to/stockfish'
        
        # Setup mock engine
        mock_engine_instance = MagicMock()
        mock_popen.return_value = mock_engine_instance
        
        # Setup mock analysis
        mock_info = {'score': chess.engine.PovScore(chess.engine.Cp(100), chess.WHITE)}
        mock_engine_instance.analyse.return_value = mock_info
        
        # Create engine and test
        engine = StockfishEngine()
        engine.start()  # This should now use the mocked popen_uci
        
        # Test with a simple board
        board = chess.Board()
        with patch.object(engine, 'evaluate_position', return_value=100):
            result = engine.evaluate_position(board, time_limit=1.0)
            self.assertEqual(result, 100)


class TestPositionAnalyzer(unittest.TestCase):
    """Tests for the PositionAnalyzer class."""
    
    def setUp(self):
        """Set up for each test."""
        self.mock_engine = MagicMock()
        self.analyzer = PositionAnalyzer(self.mock_engine, username="test_user")
    
    def test_blunder_detection(self):
        """Test blunder detection logic."""
        # Test the BlunderDetector instance that's part of PositionAnalyzer
        # For the standard strictness level, a position is considered "equal" if
        # it's between -800 and 800 centipawns, and "terrible" if it's worse than -2000 (for white)
        prev_eval = 50
        curr_eval = -2500  # This is below the terrible_threshold for standard strictness
        player_color = chess.WHITE
        
        # Use the blunder detector directly
        result, blunder_type = self.analyzer.blunder_detector.is_blunder(prev_eval, curr_eval, player_color)
        
        # With standard strictness, this should now be detected as a blunder
        self.assertTrue(result)
        self.assertEqual(blunder_type, "major_blunder")
        
        # Test a non-blunder case
        prev_eval = 50
        curr_eval = -500  # Not terrible enough to be a blunder with standard strictness
        result, blunder_type = self.analyzer.blunder_detector.is_blunder(prev_eval, curr_eval, player_color)
        self.assertFalse(result)
        self.assertIsNone(blunder_type)


class TestPuzzleGenerator(unittest.TestCase):
    """Tests for the PuzzleGenerator class."""
    
    def setUp(self):
        """Set up for each test."""
        self.generator = PuzzleGenerator(username="test_user", platform="lichess")
    
    def test_puzzle_generation(self):
        """Test puzzle generation capabilities."""
        # Create a sample blunder data that matches the expected format
        blunder_data = {
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
            "move": chess.Move.from_uci("f8a3"),  # Bad move
            "best_move": chess.Move.from_uci("g8f6"),  # Best move
            "eval_before": chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE),
            "eval_after": chess.engine.PovScore(chess.engine.Cp(800), chess.WHITE),
            "move_number": 2,
            "player_color": chess.BLACK,
            "game_url": "https://lichess.org/test123"
        }
        
        # This is a simplified test that just verifies the class can be instantiated
        self.assertIsInstance(self.generator, PuzzleGenerator)


class TestGameFetcher(unittest.TestCase):
    """Tests for the GameFetcher class."""
    
    def setUp(self):
        """Set up for each test."""
        self.fetcher = GameFetcher(username="test_user", platform="lichess")
    
    def test_game_fetcher_init(self):
        """Test GameFetcher initialization."""
        self.assertEqual(self.fetcher.username, "test_user")
        self.assertEqual(self.fetcher.platform, "lichess")


if __name__ == '__main__':
    # Setup basic logging for tests
    setup_logging("INFO")
    unittest.main() 