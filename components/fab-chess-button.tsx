'use client'

import React, { useState, useEffect } from 'react' // Import useState and useEffect
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogPortal // Import DialogPortal
} from "@/components/ui/dialog"
import { ChessPuzzle } from "@/components/chess-puzzle" // Corrected import path if needed
import { usePuzzleData } from '@/hooks/use-chess-puzzle-data' // Import the hook

export function FabChessButton() {
  const [isOpen, setIsOpen] = useState(false) // Restore state
  const { puzzle, isLoading, error, fetchPuzzle } = usePuzzleData() // Use the hook

  // Restore useEffect to fetch puzzle when the dialog opens
  useEffect(() => {
    if (isOpen) {
      console.log('Dialog opened, fetching puzzle...') // Debug log
      fetchPuzzle()
    }
  }, [isOpen, fetchPuzzle])

  return (
    // Restore Dialog structure
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="secondary"
          size="icon"
          className="fixed bottom-6 right-6 z-50 h-12 w-12 rounded-full shadow-lg"
          aria-label="Open Chess Puzzle"
        >
          {/* Use Unicode Knight symbol */}
          <span className="text-2xl" role="img" aria-hidden="true">♘</span>
        </Button>
      </DialogTrigger>
      {/* Wrap DialogContent in DialogPortal */}
      <DialogPortal>
        <DialogContent 
          className="sm:max-w-[425px] md:max-w-[550px] lg:max-w-[650px]" // Adjust width as needed
          onOpenAutoFocus={(e) => e.preventDefault()} // Prevent auto-focus
        >
          <DialogHeader>
            <DialogTitle>Chess Puzzle</DialogTitle>
          </DialogHeader>
          {/* Pass fetched data and state to ChessPuzzle */}
          <ChessPuzzle puzzleData={puzzle} isLoading={isLoading} error={error} />
        </DialogContent>
      </DialogPortal>
    </Dialog>
  )
}
