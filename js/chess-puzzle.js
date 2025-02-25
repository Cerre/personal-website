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
    const turnIndicator = document.getElementById('turn-indicator');
    
    // Only initialize if we're on a page with the chess puzzle
    if (!chessBoard) return;
    
    // Global variables
    let puzzles = [];
    let currentPuzzleIndex = 0;
    let board = null;
    let game = null;
    let lastMove = null; // Store the last move for animation
    
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
        
        // Update turn indicator
        updateTurnIndicator();
        
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
        
        // Clear any highlights
        clearHighlightedSquares();
        
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
        
        // Highlight the move
        highlightSquares(source, target);
        
        // Update turn indicator
        updateTurnIndicator();
        
        // Check if the move matches the solution
        const currentPuzzle = puzzles[currentPuzzleIndex];
        const userMoveUci = source + target + (move.promotion || '');
        
        if (userMoveUci === currentPuzzle.solution[0]) {
            // Show success message and solution
            solutionContainer.style.display = 'block';
            solutionMove.innerHTML = `<span class="correct-move">${move.san} ✓</span>`;
            
            // Add visual feedback - Green flash on the board
            addBoardFeedback('correct');
        } else {
            // Show that the move was incorrect
            solutionContainer.style.display = 'block';
            solutionMove.innerHTML = `<span class="incorrect-move">${move.san} ✗</span>. The correct move was ${uciToSan(currentPuzzle.solution[0])}.`;
            
            // Add visual feedback - Red flash on the board
            addBoardFeedback('incorrect');
            
            // Undo the move after a delay
            setTimeout(() => {
                game.undo();
                board.position(game.fen());
                clearHighlightedSquares();
                updateTurnIndicator();
            }, 1500);
        }
    }
    
    function onSnapEnd() {
        // Update the board position after the piece snap animation
        board.position(game.fen());
    }
    
    // Function to update the turn indicator
    function updateTurnIndicator() {
        if (game) {
            const turn = game.turn() === 'w' ? 'White' : 'Black';
            turnIndicator.textContent = turn;
            turnIndicator.className = game.turn() === 'w' ? 'white' : 'black';
        }
    }
    
    // Function to highlight squares
    function highlightSquares(source, target) {
        // Remove any existing highlights
        clearHighlightedSquares();
        
        // Highlight the source and target squares
        const boardEl = document.getElementById('chess-board');
        const sourceSquare = boardEl.querySelector('.square-' + source);
        const targetSquare = boardEl.querySelector('.square-' + target);
        
        if (sourceSquare) sourceSquare.classList.add('highlight-square');
        if (targetSquare) targetSquare.classList.add('highlight-square');
        
        // Store the move
        lastMove = { from: source, to: target };
    }
    
    // Function to clear highlighted squares
    function clearHighlightedSquares() {
        const highlights = document.querySelectorAll('.highlight-square');
        highlights.forEach(el => el.classList.remove('highlight-square'));
    }
    
    // Function to add visual feedback on the board for correct/incorrect moves
    function addBoardFeedback(type) {
        const boardEl = document.getElementById('chess-board');
        if (!boardEl) return;
        
        // Create an overlay div for the feedback
        const overlay = document.createElement('div');
        overlay.className = `board-feedback ${type}`;
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.backgroundColor = type === 'correct' ? 'rgba(0, 255, 0, 0.2)' : 'rgba(255, 0, 0, 0.2)';
        overlay.style.zIndex = '1000';
        overlay.style.pointerEvents = 'none';
        overlay.style.transition = 'opacity 1.5s';
        overlay.style.opacity = '1';
        
        // Make sure the board container has position relative
        const boardContainer = boardEl.closest('.chess-board-container');
        if (boardContainer) {
            if (getComputedStyle(boardContainer).position === 'static') {
                boardContainer.style.position = 'relative';
            }
            
            // Add the overlay
            boardContainer.appendChild(overlay);
            
            // Remove the overlay after animation
            setTimeout(() => {
                overlay.style.opacity = '0';
                setTimeout(() => {
                    overlay.remove();
                }, 1500);
            }, 200);
        }
    }
    
    // Event listeners
    showSolutionBtn.addEventListener('click', function() {
        // Get the current puzzle and its solution
        const currentPuzzle = puzzles[currentPuzzleIndex];
        if (!currentPuzzle || !currentPuzzle.solution || !currentPuzzle.solution.length) return;
        
        // Show the solution container
        solutionContainer.style.display = 'block';
        
        // Extract the source and target squares from UCI notation
        const uci = currentPuzzle.solution[0];
        const source = uci.substring(0, 2);
        const target = uci.substring(2, 4);
        const promotion = uci.length > 4 ? uci.substring(4, 5) : undefined;
        
        // Make the move on the chess.js instance
        const move = game.move({
            from: source,
            to: target,
            promotion: promotion || 'q'
        });
        
        if (move) {
            // Update the board with the new position
            board.position(game.fen());
            
            // Highlight the move
            highlightSquares(source, target);
            
            // Update the turn indicator
            updateTurnIndicator();
            
            // Show success message
            solutionMove.innerHTML = `<span class="correct-move">${move.san} ✓</span>`;
        }
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