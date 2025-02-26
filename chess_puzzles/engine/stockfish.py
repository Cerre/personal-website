"""
Stockfish chess engine management module.

This module handles downloading, setting up, and interacting with the Stockfish chess engine.
"""
import os
import sys
import tempfile
import subprocess
import traceback
from pathlib import Path
import chess
import chess.engine
import logging

from chess_puzzles import config

logger = logging.getLogger(__name__)

class StockfishEngine:
    """Manages interactions with the Stockfish chess engine."""
    
    def __init__(self, path=None):
        """Initialize the Stockfish engine.
        
        Args:
            path (str, optional): Path to the Stockfish executable. If None, will
                try to find or download Stockfish automatically.
        """
        self.path = path or self._prepare_stockfish()
        self.engine = None
        
    def _prepare_stockfish(self):
        """Prepare the Stockfish engine.
        
        Returns:
            str: Path to the Stockfish executable.
        """
        # Try to use path from environment variable first
        stockfish_path = config.STOCKFISH_PATH
        if stockfish_path and os.path.exists(stockfish_path):
            logger.info(f"Using Stockfish from environment variable: {stockfish_path}")
            return stockfish_path
            
        # Try to find Stockfish in PATH
        try:
            subprocess.run(["stockfish", "--version"], 
                         check=True, capture_output=True)
            logger.info("Found Stockfish in PATH")
            return "stockfish"
        except (FileNotFoundError, subprocess.SubprocessError):
            logger.info("Stockfish not found in PATH, attempting to download")
            
        # Try to download Stockfish
        try:
            return self._download_stockfish()
        except Exception as e:
            logger.error(f"Error downloading Stockfish: {e}")
            logger.error(traceback.format_exc())
            raise RuntimeError("Failed to find or download Stockfish")
            
    def _download_stockfish(self):
        """Download Stockfish for the current platform.
        
        Returns:
            str: Path to the downloaded Stockfish executable.
        """
        stockfish_path = os.path.join(tempfile.gettempdir(), "stockfish")
        if os.path.exists(stockfish_path):
            # Check if existing download works
            try:
                test_engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                test_engine.quit()
                logger.info(f"Using existing Stockfish at {stockfish_path}")
                return stockfish_path
            except Exception:
                logger.info("Existing Stockfish doesn't work, downloading again")
                
        logger.info("Downloading Stockfish...")
        
        # Platform-specific download logic
        if sys.platform == "linux" or sys.platform == "linux2":
            return self._download_linux_stockfish(stockfish_path)
        elif sys.platform == "darwin":
            return self._download_macos_stockfish(stockfish_path)
        elif sys.platform == "win32":
            return self._download_windows_stockfish(stockfish_path)
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")
            
    def _download_linux_stockfish(self, stockfish_path):
        """Download Stockfish for Linux.
        
        Args:
            stockfish_path (str): Path where Stockfish should be saved.
            
        Returns:
            str: Path to the downloaded Stockfish executable.
        """
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_17/stockfish-ubuntu-x86-64-avx2.tar"
        logger.info(f"Downloading from {url}")
        
        subprocess.run(["wget", url, "-O", "stockfish.tar"], check=True)
        subprocess.run(["tar", "-xf", "stockfish.tar"], check=True)
        
        # Find the stockfish executable
        result = subprocess.run(
            ["find", ".", "-name", "stockfish*", "-type", "f", "-executable"], 
            capture_output=True, text=True
        )
        
        if not result.stdout.strip():
            raise RuntimeError("Could not find stockfish executable after download")
            
        found_path = result.stdout.strip().split("\n")[0]
        
        # Move to destination and make executable
        subprocess.run(["cp", found_path, stockfish_path], check=True)
        subprocess.run(["chmod", "+x", stockfish_path], check=True)
        
        # Clean up
        subprocess.run(["rm", "stockfish.tar"], check=False)
        subprocess.run(["rm", "-rf", found_path.split("/")[1]], check=False)
        
        logger.info(f"Stockfish downloaded to {stockfish_path}")
        return stockfish_path
        
    def _download_macos_stockfish(self, stockfish_path):
        """Download Stockfish for macOS.
        
        Args:
            stockfish_path (str): Path where Stockfish should be saved.
            
        Returns:
            str: Path to the downloaded Stockfish executable.
        """
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_17/stockfish-macos-x86-64-avx2.tar"
        logger.info(f"Downloading from {url}")
        
        subprocess.run(["wget", url, "-O", "stockfish.tar"], check=True)
        subprocess.run(["tar", "-xf", "stockfish.tar"], check=True)
        
        # Find the stockfish executable
        result = subprocess.run(
            ["find", ".", "-name", "stockfish*", "-type", "f", "-perm", "+111"], 
            capture_output=True, text=True
        )
        
        if not result.stdout.strip():
            raise RuntimeError("Could not find stockfish executable after download")
            
        found_path = result.stdout.strip().split("\n")[0]
        
        # Move to destination and make executable
        subprocess.run(["cp", found_path, stockfish_path], check=True)
        subprocess.run(["chmod", "+x", stockfish_path], check=True)
        
        # Clean up
        subprocess.run(["rm", "stockfish.tar"], check=False)
        subprocess.run(["rm", "-rf", found_path.split("/")[1]], check=False)
        
        logger.info(f"Stockfish downloaded to {stockfish_path}")
        return stockfish_path
        
    def _download_windows_stockfish(self, stockfish_path):
        """Download Stockfish for Windows.
        
        Args:
            stockfish_path (str): Path where Stockfish should be saved.
            
        Returns:
            str: Path to the downloaded Stockfish executable.
        """
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_17/stockfish-windows-x86-64-avx2.zip"
        logger.info(f"Downloading from {url}")
        
        # Ensure stockfish_path has .exe extension on Windows
        if not stockfish_path.endswith(".exe"):
            stockfish_path += ".exe"
            
        subprocess.run(["curl", "-L", url, "-o", "stockfish.zip"], check=True)
        subprocess.run(["powershell", "Expand-Archive", "-Path", "stockfish.zip", "-DestinationPath", "."], check=True)
        
        # Find the stockfish executable
        result = subprocess.run(
            ["powershell", "Get-ChildItem", "-Path", ".", "-Recurse", "-Filter", "stockfish*.exe"], 
            capture_output=True, text=True
        )
        
        if "stockfish" not in result.stdout.lower():
            raise RuntimeError("Could not find stockfish executable after download")
            
        # Extract path from output
        for line in result.stdout.splitlines():
            if "stockfish" in line.lower() and ".exe" in line.lower():
                # Extract path from line
                found_path = line.strip()
                break
        else:
            raise RuntimeError("Could not parse stockfish path from output")
            
        # Move to destination
        subprocess.run(["powershell", "Copy-Item", found_path, "-Destination", stockfish_path], check=True)
        
        # Clean up
        subprocess.run(["powershell", "Remove-Item", "stockfish.zip"], check=False)
        subprocess.run(["powershell", "Remove-Item", "-Recurse", "-Force", "stockfish-windows-x86-64-avx2"], check=False)
        
        logger.info(f"Stockfish downloaded to {stockfish_path}")
        return stockfish_path
        
    def start(self):
        """Start the Stockfish engine."""
        if self.engine:
            return
            
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.path)
            logger.info("Stockfish engine started")
        except Exception as e:
            logger.error(f"Failed to start Stockfish engine: {e}")
            logger.error(traceback.format_exc())
            raise
            
    def test(self):
        """Test if the Stockfish engine is working properly.
        
        Returns:
            bool: True if the engine is working, False otherwise.
        """
        try:
            test_engine = chess.engine.SimpleEngine.popen_uci(self.path)
            # Run a quick test analysis
            test_engine.analyse(chess.Board(), chess.engine.Limit(time=0.1))
            test_engine.quit()
            logger.info("Stockfish engine test successful")
            return True
        except Exception as e:
            logger.error(f"Stockfish engine test failed: {e}")
            logger.error(traceback.format_exc())
            return False
            
    def evaluate_position(self, board, time_limit=None, depth=None):
        """Evaluate a position with the Stockfish engine.
        
        Args:
            board (chess.Board): The board position to evaluate.
            time_limit (float, optional): Time limit in seconds. Defaults to config value.
            depth (int, optional): Search depth. Defaults to config value.
            
        Returns:
            int: Evaluation in centipawns from the perspective of the side to move.
        """
        if not self.engine:
            self.start()
            
        time_limit = time_limit or config.DEFAULT_TIME_LIMIT
        depth = depth or config.DEFAULT_DEPTH
            
        try:
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(time=time_limit, depth=depth)
            )
            
            # Get score from perspective of player to move (relative score)
            score = info["score"].relative
            
            # Convert mate scores to high numerical values
            if score.mate():
                value = 9999 if score.mate() > 0 else -9999
            else:
                value = score.score()
                
            return value
        except Exception as e:
            logger.error(f"Engine failed to evaluate position: {e}")
            return 0
            
    def find_best_move(self, board, time_limit=None, depth=None):
        """Find the best move in the position.
        
        Args:
            board (chess.Board): The board position to analyze.
            time_limit (float, optional): Time limit in seconds. Defaults to config value.
            depth (int, optional): Search depth. Defaults to config value.
            
        Returns:
            chess.Move: The best move according to the engine, or None if failed.
        """
        if not self.engine:
            self.start()
            
        time_limit = time_limit or config.DEFAULT_TIME_LIMIT
        depth = depth or config.DEFAULT_DEPTH
            
        try:
            result = self.engine.play(
                board, 
                chess.engine.Limit(time=time_limit, depth=depth)
            )
            return result.move
        except Exception as e:
            logger.error(f"Engine failed to find best move: {e}")
            return None
            
    def close(self):
        """Shut down the Stockfish engine."""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Stockfish engine closed")
            except Exception as e:
                logger.error(f"Error closing Stockfish engine: {e}")
            finally:
                self.engine = None
                
    def __enter__(self):
        """Start the engine when used as a context manager."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the engine when exiting context."""
        self.close()
