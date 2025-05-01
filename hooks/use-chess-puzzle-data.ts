'use client'

import { useState, useCallback } from 'react'

// Define the structure of the puzzle data based on the backend API response
// (Matching the PuzzleData Pydantic model)
export interface PuzzleData {
  game_id: string
  fen_before_user_blunder: string
  fen_after_user_blunder: string
  user_blunder_move_san: string
  blunder_move_uci: string
  player_color_to_move: 'white' | 'black'
  correct_move_uci: string
  correct_variation_uci: string[]
  blunder_comment: string | null
}

interface UsePuzzleDataReturn {
  puzzle: PuzzleData | null
  isLoading: boolean
  error: Error | null
  fetchPuzzle: () => Promise<void>
}

const API_URL = process.env.NEXT_PUBLIC_CHESS_API_URL || 'http://localhost:8000'

export function usePuzzleData(): UsePuzzleDataReturn {
  const [puzzle, setPuzzle] = useState<PuzzleData | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchPuzzle = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    setPuzzle(null) // Clear previous puzzle
    console.log(`Fetching puzzle from ${API_URL}/puzzle`) // Debug log
    try {
      const response = await fetch(`${API_URL}/puzzle`)
      console.log('Fetch response status:', response.status) // Debug log
      if (!response.ok) {
        const errorData = await response.text() // Read error body
        console.error('Fetch error data:', errorData) // Debug log
        throw new Error(`Failed to fetch puzzle: ${response.status} ${response.statusText} - ${errorData}`)
      }
      const data: PuzzleData = await response.json()
      console.log('Fetched puzzle data:', data) // Debug log
      setPuzzle(data)
    } catch (err) {
      console.error('Error in fetchPuzzle:', err) // Debug log
      setError(err instanceof Error ? err : new Error('An unknown error occurred'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { puzzle, isLoading, error, fetchPuzzle }
}
