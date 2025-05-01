'use client'

import React, { useState, useEffect, useCallback } from 'react' // Import useCallback
import { Chessboard } from 'react-chessboard'
import { type Piece, type Square } from 'react-chessboard/dist/chessboard/types' // Import types
import { Chess } from 'chess.js' // Import Chess
import { type PuzzleData } from '@/hooks/use-chess-puzzle-data'
import { cn } from '@/lib/utils'; // Import cn utility

interface ChessPuzzleProps {
  puzzleData: PuzzleData | null
  isLoading: boolean
  error: Error | null
}

export function ChessPuzzle({ puzzleData, isLoading, error }: ChessPuzzleProps) {
  // State to manage the currently displayed FEN
  const [currentFen, setCurrentFen] = useState<string | null>(null);
  // State to manage the chess.js game instance
  const [game, setGame] = useState<Chess | null>(null); 
  const [isAnimatingBlunder, setIsAnimatingBlunder] = useState<boolean>(false);
  const [blunderHighlightSquares, setBlunderHighlightSquares] = useState({});
  const [isIncorrectMoveFlash, setIsIncorrectMoveFlash] = useState<boolean>(false); // State for incorrect move feedback

  useEffect(() => {
    let animationTimeout: NodeJS.Timeout;
    let gameInitializationTimeout: NodeJS.Timeout;

    if (puzzleData) {
      // 1. Initially show the board state *before* the blunder
      setCurrentFen(puzzleData.fen_before_user_blunder);
      setIsAnimatingBlunder(true); // Indicate animation is starting
      setGame(null); // Reset game instance during animation
      setBlunderHighlightSquares({}); 

      // 2. After a delay, update to the state *after* the blunder (puzzle start)
      animationTimeout = setTimeout(() => {
        setCurrentFen(puzzleData.fen_after_user_blunder);
        setIsAnimatingBlunder(false); // Animation complete
        
        // 3. Initialize the chess.js game instance slightly after FEN update
        //    to ensure Chessboard has rendered the starting position
        gameInitializationTimeout = setTimeout(() => {
          try {
            const newGame = new Chess(puzzleData.fen_after_user_blunder);
            setGame(newGame);
            console.log("Chess game initialized with FEN:", puzzleData.fen_after_user_blunder);
          } catch (e) {
            console.error("Failed to initialize chess.js with FEN:", puzzleData.fen_after_user_blunder, e);
            setGame(null); // Ensure game is null if initialization fails
          }
        }, 50); // Short delay after setting FEN

      }, 1000); // 1-second delay for the animation
    } else {
      // Reset if puzzleData becomes null
      setCurrentFen(null);
      setGame(null);
      setIsAnimatingBlunder(false);
      setBlunderHighlightSquares({});
    }

    // Cleanup function to clear the timeouts
    return () => {
      clearTimeout(animationTimeout);
      clearTimeout(gameInitializationTimeout);
    };
    // Depend on the specific FENs to re-trigger when a *new* puzzle loads
  }, [puzzleData?.fen_before_user_blunder, puzzleData?.fen_after_user_blunder]);

  // Handle piece drop event
  const onPieceDrop = useCallback((sourceSquare: Square, targetSquare: Square, piece: Piece): boolean => {
    // Don't allow moves if game not initialized, animating, or no puzzle
    if (!game || isAnimatingBlunder || !puzzleData || !puzzleData.solution_moves_san || puzzleData.solution_moves_san.length === 0) {
      console.log("Move prevented: Game not ready, animating, or puzzle data incomplete.");
      return false; // Prevent the move visually
    }

    // Check whose turn it is
    const pieceColor = piece.startsWith('w') ? 'white' : 'black';
    if (pieceColor !== puzzleData.player_color_to_move) {
      console.log("Move prevented: Not your turn.");
      return false; // Prevent moving opponent's pieces
    }

    let moveResult = null;
    const currentFenBeforeMove = game.fen(); // Store FEN before attempting move

    try {
      moveResult = game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q', // Assume queen promotion for simplicity
      });
    } catch (e) {
      moveResult = null; // Treat errors as illegal moves
    }

    // If the move is illegal in chess rules, chess.js returns null
    if (moveResult === null) {
      console.log("Illegal move attempted (chess.js):", sourceSquare, "->", targetSquare);
      // Flash feedback for illegal move
      setIsIncorrectMoveFlash(true);
      setTimeout(() => setIsIncorrectMoveFlash(false), 500); // Flash duration
      return false; // Tell react-chessboard the move was invalid
    }

    // Move is legal according to chess rules, now check if it's the puzzle solution
    const solutionMove = puzzleData.solution_moves_san[0]; // Get the first (current) solution move

    if (moveResult.san === solutionMove) {
      // Correct move!
      console.log("Correct move made:", moveResult.san);
      setCurrentFen(game.fen()); // Update the board state visually

      // TODO: Trigger opponent's response move after a short delay
      // TODO: Advance the puzzle state (remove the first move from solution_moves_san?)

      return true; // Tell react-chessboard the move was valid and accepted
    } else {
      // Incorrect move (but legal chess move)
      console.log("Incorrect move:", moveResult.san, "Expected:", solutionMove);

      // 1. Undo the move in the internal game state
      game.load(currentFenBeforeMove); // More reliable than undo() if promotions involved

      // 2. Flash visual feedback
      setIsIncorrectMoveFlash(true);
      setTimeout(() => setIsIncorrectMoveFlash(false), 500); // Flash duration

      // 3. Tell react-chessboard the move was invalid *for the puzzle*
      //    so it snaps the piece back. We don't update currentFen here.
      return false;
    }

  }, [game, isAnimatingBlunder, puzzleData]); // Add dependencies


  if (isLoading) {
    return <div className="p-4 text-center">Loading puzzle...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-600">Error loading puzzle: {error.message}</div>
  }

  // Use currentFen for the board position if available, otherwise show placeholder
  if (!puzzleData || currentFen === null) {
    return <div className="p-4 text-center">No puzzle loaded yet or initializing...</div>
  }

  // Determine board orientation based on whose turn it is *in the puzzle*
  const boardOrientation = puzzleData.player_color_to_move === 'white' ? 'white' : 'black';

  return (
    <div className="p-4 flex flex-col items-center">
      <p className="mb-2 text-center h-6"> {/* Added fixed height to prevent layout shift */}
        {isAnimatingBlunder 
          ? `Showing blunder: ${puzzleData.user_blunder_move_san}` 
          : `${puzzleData.player_color_to_move === 'white' ? 'White' : 'Black'} to move. Find the best move!`}
      </p>
      {/* Add conditional styling for border highlight during blunder animation OR incorrect move flash */}
      <div 
        className={cn(
          "chessboard-container w-full max-w-[400px] sm:max-w-[500px] md:max-w-[600px] transition-all duration-300 ease-in-out",
          "relative", // Add relative positioning for the overlay
          // Apply ring for blunder animation OR incorrect move flash
          (isAnimatingBlunder || isIncorrectMoveFlash) && "ring-4 ring-red-500/80 ring-offset-2 ring-offset-background rounded-md"
        )}
      >
        <Chessboard
          id="ChessPuzzleBoard" // Added id for potential debugging/testing
          position={currentFen} // Use the state variable for the position
          onPieceDrop={onPieceDrop} // Add the drop handler
          boardOrientation={boardOrientation}
          animationDuration={isAnimatingBlunder ? 300 : 200} // Slightly faster user move animation
          customSquareStyles={blunderHighlightSquares} // Pass dynamic styles
          // Prevent user interaction while the initial blunder animation is playing OR if game not ready
          arePiecesDraggable={!isAnimatingBlunder && !!game} 
        />
        {/* Red Overlay during blunder animation (only) */}
        <div
          className={cn(
            "absolute inset-0 bg-red-500/30 rounded-md pointer-events-none transition-opacity duration-300 ease-in-out z-10",
            isAnimatingBlunder ? "opacity-100" : "opacity-0" // Only show during blunder animation
          )}
          aria-hidden="true" // Hide from screen readers
        />
      </div>
      {/* Optional Debug Info */}
      {/* ... existing debug info commented out ... */}
    </div>
  )
}
