'use client'

import React from 'react'
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ChessPuzzle } from "@/components/chess-puzzle"

export function FabChessButton() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="secondary"
          size="icon"
          className="fixed bottom-6 right-6 z-50 h-12 w-12 rounded-full shadow-lg"
          aria-label="Open Chess Puzzle"
        >
          <span className="text-2xl" role="img" aria-hidden="true">♟️</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] md:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Chess Puzzle</DialogTitle>
        </DialogHeader>
        <ChessPuzzle />
      </DialogContent>
    </Dialog>
  )
}
