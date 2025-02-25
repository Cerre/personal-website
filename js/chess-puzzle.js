// Chess Puzzle Feature
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chessBoard = document.getElementById('chess-board');
    const showSolutionBtn = document.getElementById('show-solution');
    const tryAnotherBtn = document.getElementById('try-another');
    const solutionContainer = document.getElementById('solution-container');
    const solutionMove = document.getElementById('solution-move');
    const solutionExplanation = document.getElementById('solution-explanation');
    const gameInfo = document.getElementById('game-info');
    const positionEval = document.getElementById('position-eval');
    const puzzleDifficulty = document.getElementById('puzzle-difficulty');
    
    // Only initialize if we're on a page with the chess puzzle
    if (!chessBoard) return;
    
    // Global variables
    let puzzles = [];
    let currentPuzzleIndex = 0;
    let board = null;
    let game = null;
    
    // Path to the puzzles.json file
    const PUZZLES_FILE = 'puzzles.json';
    
    // Load puzzles
    loadPuzzles();
    
    function loadPuzzles() {
        // Show loading placeholder
        chessBoard.innerHTML = `
            <div class="chess-board-placeholder">
                <i class="fas fa-chess-knight"></i>
                <p>Loading my latest blunder...</p>
            </div>
        `;
        
        // Fetch puzzles from the JSON file
        fetch(PUZZLES_FILE)
            .then(response => response.json())
            .then(data => {
                // Store metadata globally
                window.puzzleMetadata = {
                    platform: data.platform || 'Chess.com',
                    username: data.username || 'Toxima1',
                    generated_at: data.generated_at || new Date().toISOString(),
                    is_placeholder: data.is_placeholder || false,
                    message: data.message || ''
                };
                
                // Sort puzzles by difficulty (easiest first)
                puzzles = data.puzzles.sort((a, b) => {
                    return a.difficulty - b.difficulty;
                });
                
                if (puzzles.length > 0) {
                    // Show the first puzzle
                    displayPuzzle(0);
                    
                    // If it's a placeholder puzzle, show a note
                    if (window.puzzleMetadata.is_placeholder) {
                        const placeholderNote = document.createElement('div');
                        placeholderNote.className = 'placeholder-note';
                        placeholderNote.innerHTML = `
                            <p><em>Note: ${window.puzzleMetadata.message}</em></p>
                        `;
                        
                        // Insert after puzzle details
                        const puzzleDetails = document.querySelector('.puzzle-details');
                        if (puzzleDetails) {
                            puzzleDetails.parentNode.insertBefore(placeholderNote, puzzleDetails.nextSibling);
                        }
                    }
                } else {
                    chessBoard.innerHTML = `
                        <div class="chess-board-content">
                            <p style="text-align: center; padding: 20px;">
                                No puzzles available yet. Check back soon!
                            </p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading puzzles:', error);
                chessBoard.innerHTML = `
                    <div class="chess-board-content">
                        <p style="text-align: center; padding: 20px;">
                            <strong>Error loading chess puzzles</strong><br>
                            Please try again later.
                        </p>
                    </div>
                `;
            });
    }
    
    function displayPuzzle(index) {
        if (puzzles.length === 0) return;
        
        // Ensure index is within bounds
        currentPuzzleIndex = Math.max(0, Math.min(index, puzzles.length - 1));
        
        // Get the current puzzle
        const currentPuzzle = puzzles[currentPuzzleIndex];
        
        // Update puzzle details
        const gameInfoText = `Game from ${window.puzzleMetadata.platform} (${window.puzzleMetadata.username})`;
        
        // Add game link if available
        if (currentPuzzle.game_url) {
            gameInfo.innerHTML = `${gameInfoText} <a href="${currentPuzzle.game_url}" target="_blank" class="game-link"><i class="fas fa-external-link-alt"></i> View Game</a>`;
        } else {
            gameInfo.textContent = gameInfoText;
        }
        
        positionEval.textContent = (currentPuzzle.eval_change / 100).toFixed(1);
        
        // Map difficulty number to text
        const difficultyMap = {
            1: "Very Easy",
            2: "Easy",
            3: "Intermediate",
            4: "Challenging",
            5: "Advanced"
        };
        puzzleDifficulty.textContent = difficultyMap[currentPuzzle.difficulty] || "Intermediate";
        
        // Initialize chess.js with the puzzle position
        game = new Chess(currentPuzzle.fen);
        
        // Initialize or update the chessboard
        if (board === null) {
            board = Chessboard('chess-board', {
                position: currentPuzzle.fen,
                draggable: true,
                orientation: currentPuzzle.player_color === 'white' ? 'white' : 'black',
                onDragStart: onDragStart,
                onDrop: onDrop,
                onSnapEnd: onSnapEnd,
                pieceTheme: 'https://lichess1.org/assets/piece/cburnett/{piece}.svg'
            });
        } else {
            board.position(currentPuzzle.fen, false);
            board.orientation(currentPuzzle.player_color === 'white' ? 'white' : 'black');
        }
        
        // Reset solution display
        solutionContainer.style.display = 'none';
        
        // Convert UCI moves to SAN notation for solution display
        const solution = uciToSan(currentPuzzle.solution[0]);
        solutionMove.textContent = solution;
        
        // Generate a simple explanation based on the evaluation change
        const evalChange = currentPuzzle.eval_change;
        if (evalChange > 500) {
            solutionExplanation.textContent = `This move gains a significant advantage (${(evalChange/100).toFixed(1)} pawns).`;
        } else if (evalChange > 300) {
            solutionExplanation.textContent = `This move wins material worth about ${(evalChange/100).toFixed(1)} pawns.`;
        } else {
            solutionExplanation.textContent = `This tactical move improves the position by ${(evalChange/100).toFixed(1)} pawns.`;
        }
    }
    
    function uciToSan(uci) {
        if (!game || !uci) return uci;
        
        // Create a move from UCI notation
        const move = game.move({
            from: uci.substring(0, 2),
            to: uci.substring(2, 4),
            promotion: uci.length > 4 ? uci.substring(4, 5) : undefined
        });
        
        // Undo the move to restore the position
        if (move) {
            const san = move.san;
            game.undo();
            return san;
        }
        
        return uci;
    }
    
    // Chess.js functions for handling moves
    function onDragStart(source, piece, position, orientation) {
        // Allow moves only for the current player's pieces
        const currentPuzzle = puzzles[currentPuzzleIndex];
        const playerColor = currentPuzzle.player_color.charAt(0);
        
        if (game.game_over() || 
            (game.turn() === 'w' && piece.search(/^b/) !== -1) || 
            (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
            return false;
        }
    }
    
    function onDrop(source, target) {
        // Check if the move is legal
        const move = game.move({
            from: source,
            to: target,
            promotion: 'q' // Always promote to queen for simplicity
        });
        
        // If illegal move, snap back
        if (move === null) return 'snapback';
        
        // Check if the move matches the solution
        const currentPuzzle = puzzles[currentPuzzleIndex];
        const userMoveUci = source + target + (move.promotion || '');
        
        if (userMoveUci === currentPuzzle.solution[0]) {
            // Show success message and solution
            solutionContainer.style.display = 'block';
            solutionMove.innerHTML = `<span class="correct-move">${move.san} ✓</span>`;
        } else {
            // Show that the move was incorrect
            solutionContainer.style.display = 'block';
            solutionMove.innerHTML = `<span class="incorrect-move">${move.san} ✗</span>. The correct move was ${uciToSan(currentPuzzle.solution[0])}.`;
            
            // Undo the move
            setTimeout(() => {
                game.undo();
                board.position(game.fen());
            }, 1000);
        }
    }
    
    function onSnapEnd() {
        // Update the board position after the piece snap animation
        board.position(game.fen());
    }
    
    // Event listeners
    showSolutionBtn.addEventListener('click', function() {
        solutionContainer.style.display = 'block';
    });
    
    tryAnotherBtn.addEventListener('click', function() {
        // Pick a random puzzle
        const randomIndex = Math.floor(Math.random() * puzzles.length);
        // Make sure it's different from the current one if possible
        const newIndex = puzzles.length > 1 && randomIndex === currentPuzzleIndex 
            ? (randomIndex + 1) % puzzles.length 
            : randomIndex;
            
        displayPuzzle(newIndex);
    });
}); 