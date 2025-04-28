'use client'

import React from 'react'
import { type PuzzleData } from '@/hooks/use-chess-puzzle-data' // Import the type

interface ChessPuzzleProps {
  puzzleData: PuzzleData | null
  isLoading: boolean
  error: Error | null
}

export function ChessPuzzle({ puzzleData, isLoading, error }: ChessPuzzleProps) {
  if (isLoading) {
    return <div className="p-4 text-center">Loading puzzle...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-600">Error loading puzzle: {error.message}</div>
  }

  if (!puzzleData) {
    return <div className="p-4 text-center">No puzzle loaded yet.</div> // Or fetch on mount?
  }

  // Placeholder for the actual puzzle display logic
  return (
    <div className="p-4">
      <p>Puzzle Loaded!</p>
      <p>Game ID: {puzzleData.game_id}</p>
      <p>Starting FEN (after blunder): {puzzleData.fen_after_user_blunder}</p>
      <p>Blunder Move (UCI): {puzzleData.blunder_move_uci}</p>
      <p>Correct Move (UCI): {puzzleData.correct_move_uci}</p>
      {/* TODO: Implement react-chessboard and interaction logic here */}
    </div>
  )
}
