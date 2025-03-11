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
    const PUZZLES_FILE = 'chess_puzzles/puzzles.json';
    
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
                
                // Get puzzle array and sort by timestamp (newest first)
                puzzles = data.puzzles.slice();
                
                // Add timestamp sorting capability - convert timestamps to Date objects for comparison
                puzzles.sort((a, b) => {
                    const dateA = new Date(a.timestamp || '');
                    const dateB = new Date(b.timestamp || '');
                    // Sort in descending order (newest first)
                    return dateB - dateA;
                });
                
                // Filter puzzles to ensure they all meet the minimum threshold (500 centipawns)
                puzzles = puzzles.filter(puzzle => puzzle.eval_change >= 500);
                console.log(`Filtered to ${puzzles.length} puzzles with eval_change >= 500 centipawns`);
                
                if (puzzles.length > 0) {
                    // Show the first puzzle (newest one)
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
        
        // Display eval change in pawns (divide centipawns by 100)
        positionEval.textContent = (currentPuzzle.eval_change / 100).toFixed(1) + " pawns";
        
        // Map difficulty number to text
        const difficultyMap = {
            1: "Very Easy",
            2: "Easy",
            3: "Intermediate",
            4: "Challenging",
            5: "Advanced"
        };
        puzzleDifficulty.textContent = difficultyMap[currentPuzzle.difficulty] || "Intermediate";
        
        // Reset solution display
        solutionContainer.style.display = 'none';
        
        // Clear any highlights
        clearHighlightedSquares();
        
        // Initialize chess.js with the position before the blunder
        game = new Chess(currentPuzzle.pre_blunder_fen || currentPuzzle.fen);
        
        // Initialize or update the chessboard with position before the blunder
        if (board === null) {
            board = Chessboard('chess-board', {
                position: currentPuzzle.pre_blunder_fen || currentPuzzle.fen,
                draggable: true,
                orientation: currentPuzzle.player_color === 'white' ? 'white' : 'black',
                onDragStart: onDragStart,
                onDrop: onDrop,
                onSnapEnd: onSnapEnd,
                pieceTheme: 'https://lichess1.org/assets/piece/cburnett/{piece}.svg'
            });
        } else {
            board.position(currentPuzzle.pre_blunder_fen || currentPuzzle.fen, false);
            board.orientation(currentPuzzle.player_color === 'white' ? 'white' : 'black');
        }
        
        // Update turn indicator (showing whose turn it is in the initial position)
        updateTurnIndicator();
        
        // Update puzzle instructions to show we're going to animate the blunder
        const puzzleInfoEl = document.querySelector('.chess-puzzle-info h3');
        if (puzzleInfoEl) {
            puzzleInfoEl.textContent = "Watch My Blunder...";
        }
        
        // Disable dragging during animation using the proper API
        board = Chessboard('chess-board', {
            position: game.fen(),
            draggable: false,
            orientation: currentPuzzle.player_color === 'white' ? 'white' : 'black',
            onDragStart: onDragStart,
            onDrop: onDrop,
            onSnapEnd: onSnapEnd,
            pieceTheme: 'https://lichess1.org/assets/piece/cburnett/{piece}.svg'
        });
        
        // After a short delay, animate Toxima's blunder move
        setTimeout(() => {
            // Extract the blundered move from the puzzle data
            const blunderedMoveSAN = currentPuzzle.blundered_move;
            const blunderedMoveUCI = currentPuzzle.blundered_move_uci;
            console.log(`Animating blundered move: ${blunderedMoveSAN} (UCI: ${blunderedMoveUCI})`);
            
            // Make the blundered move in the chess.js game
            let move;
            try {
                // First try to make the move using UCI notation if available
                if (blunderedMoveUCI) {
                    const from = blunderedMoveUCI.substring(0, 2);
                    const to = blunderedMoveUCI.substring(2, 4);
                    const promotion = blunderedMoveUCI.length > 4 ? blunderedMoveUCI.substring(4, 5) : undefined;
                    
                    move = game.move({
                        from: from,
                        to: to,
                        promotion: promotion
                    });
                } else {
                    // Fallback to SAN notation
                    move = game.move(blunderedMoveSAN);
                }
            } catch (e) {
                console.error('Error making blundered move:', e);
                // Fallback approach - try to find the move
                const moves = game.moves({ verbose: true });
                const moveObj = moves.find(m => game.san(m) === blunderedMoveSAN);
                if (moveObj) {
                    move = game.move(moveObj);
                }
            }
            
            if (move) {
                // Highlight and animate the blundered move
                highlightSquares(move.from, move.to);
                board.position(game.fen(), true); // true enables animation
                
                // Update the turn indicator after the blunder
                updateTurnIndicator();
                
                // After the animation completes, allow the user to solve the puzzle
                setTimeout(() => {
                    // Update puzzle instructions
                    if (puzzleInfoEl) {
                        puzzleInfoEl.textContent = "Now Find the Best Response!";
                    }
                    
                    // Make sure we're showing the position after the blunder
                    board.position(currentPuzzle.fen, false);
                    
                    // Re-enable dragging with the proper API
                    board = Chessboard('chess-board', {
                        position: currentPuzzle.fen,
                        draggable: true,
                        orientation: currentPuzzle.player_color === 'white' ? 'white' : 'black',
                        onDragStart: onDragStart,
                        onDrop: onDrop,
                        onSnapEnd: onSnapEnd,
                        pieceTheme: 'https://lichess1.org/assets/piece/cburnett/{piece}.svg'
                    });
                    
                    // Convert UCI moves to SAN notation for solution display
                    const solution = uciToSan(currentPuzzle.solution[0]);
                    solutionMove.textContent = solution;
                    
                    // Check if we should show solution explanations
                    if (currentPuzzle.show_solution_text === false) {
                        // Don't show any solution explanation text
                        solutionExplanation.textContent = "";
                    } else {
                        // Generate a simple explanation based on the evaluation change
                        const evalChange = currentPuzzle.eval_change;
                        const evalInPawns = (evalChange / 100).toFixed(1);
                        if (evalChange > 500) {
                            solutionExplanation.textContent = `This move turns a good position into a significant disadvantage (${evalInPawns} pawns worse).`;
                        } else if (evalChange > 300) {
                            solutionExplanation.textContent = `This blunder loses material worth about ${evalInPawns} pawns from an even position.`;
                        } else {
                            solutionExplanation.textContent = `This mistake costs ${evalInPawns} pawns from a favorable position.`;
                        }
                    }
                }, 1500); // Delay after animation
            } else {
                console.error(`Failed to make blundered move: ${blunderedMoveSAN}`);
                // If we can't make the move, just proceed to the solving phase
                if (puzzleInfoEl) {
                    puzzleInfoEl.textContent = "Find the Best Move!";
                }
                // Re-enable dragging with the proper API
                board = Chessboard('chess-board', {
                    position: game.fen(),
                    draggable: true,
                    orientation: currentPuzzle.player_color === 'white' ? 'white' : 'black',
                    onDragStart: onDragStart,
                    onDrop: onDrop,
                    onSnapEnd: onSnapEnd,
                    pieceTheme: 'https://lichess1.org/assets/piece/cburnett/{piece}.svg'
                });
            }
        }, 1000); // Initial delay before animation
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
        
        // Compare with the correct solution
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
        
        console.log(`Highlighting squares: from ${source} to ${target}`);
        
        // Highlight the source and target squares
        const boardEl = document.getElementById('chess-board');
        const sourceSquare = boardEl.querySelector('.square-' + source);
        const targetSquare = boardEl.querySelector('.square-' + target);
        
        if (sourceSquare) {
            sourceSquare.classList.add('highlight-square');
            console.log('Added highlight to source square:', sourceSquare);
        } else {
            console.warn('Source square not found:', source);
        }
        
        if (targetSquare) {
            targetSquare.classList.add('highlight-square');
            console.log('Added highlight to target square:', targetSquare);
        } else {
            console.warn('Target square not found:', target);
        }
        
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
        console.log(`Adding board feedback: ${type}`);
        
        const boardEl = document.getElementById('chess-board');
        if (!boardEl) {
            console.warn('Chess board element not found');
            return;
        }
        
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
            
            console.log('Adding overlay to board container');
            // Add the overlay
            boardContainer.appendChild(overlay);
            
            // Remove the overlay after animation
            setTimeout(() => {
                console.log('Starting fade out animation');
                overlay.style.opacity = '0';
                setTimeout(() => {
                    console.log('Removing overlay');
                    overlay.remove();
                }, 1500);
            }, 200);
        } else {
            console.warn('Board container not found');
        }
    }
    
    // Event listeners
    showSolutionBtn.addEventListener('click', function() {
        // Get the current puzzle and its solution
        const currentPuzzle = puzzles[currentPuzzleIndex];
        if (!currentPuzzle || !currentPuzzle.solution || !currentPuzzle.solution.length) return;
        
        console.log('Show Solution button clicked');
        
        // Show the solution container
        solutionContainer.style.display = 'block';
        
        // Extract the source and target squares from UCI notation
        const uci = currentPuzzle.solution[0];
        const source = uci.substring(0, 2);
        const target = uci.substring(2, 4);
        const promotion = uci.length > 4 ? uci.substring(4, 5) : undefined;
        
        console.log(`Solution move: ${source} to ${target}`);
        
        // Make the move on the chess.js instance
        const move = game.move({
            from: source,
            to: target,
            promotion: promotion || 'q'
        });
        
        if (move) {
            console.log(`Move executed: ${move.san}`);
            
            // Update the board with the new position
            board.position(game.fen());
            
            // Highlight the move
            highlightSquares(source, target);
            
            // Update the turn indicator
            updateTurnIndicator();
            
            // Show success message
            solutionMove.innerHTML = `<span class="correct-move">${move.san} ✓</span>`;
            
            // Add visual feedback - Green flash on the board
            addBoardFeedback('correct');
        } else {
            console.warn('Failed to execute solution move');
        }
    });
    
    tryAnotherBtn.addEventListener('click', function() {
        // Pick a random puzzle, excluding the first/current one
        let randomIndex;
        
        // If there's more than 1 puzzle, avoid the first puzzle (latest one)
        if (puzzles.length > 1) {
            if (currentPuzzleIndex === 0) {
                // If we're on the first puzzle, pick any other puzzle
                randomIndex = Math.floor(Math.random() * (puzzles.length - 1)) + 1;
            } else {
                // If we're already on another puzzle, pick any random puzzle except the current one
                randomIndex = Math.floor(Math.random() * (puzzles.length - 1));
                if (randomIndex >= currentPuzzleIndex) randomIndex++;
            }
        } else {
            // If there's only one puzzle, just show it again
            randomIndex = 0;
        }
            
        displayPuzzle(randomIndex);
    });
    
    // Add a hidden debug function to force refresh
    window.forceRefreshPuzzles = function() {
        console.log('Forcing cache refresh...');
        
        // Add a random parameter to break the cache
        const cacheBuster = new Date().getTime();
        const puzzleFileWithCacheBuster = `${PUZZLES_FILE}?v=${cacheBuster}`;
        
        console.log(`Fetching with cache buster: ${puzzleFileWithCacheBuster}`);
        
        fetch(puzzleFileWithCacheBuster, { cache: 'no-store' })
            .then(response => response.json())
            .then(data => {
                console.log('Successfully fetched fresh data with cache busting');
                window.location.reload(true); // Force reload from server
            })
            .catch(error => {
                console.error('Error during cache busting:', error);
                alert('Failed to refresh. Try pressing Ctrl+F5 (or Cmd+Shift+R on Mac).');
            });
    };
}); 