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
    
    // Mock data for prototype - would be replaced with API call
    const mockPuzzles = [
        {
            fen: 'r1bqkbnr/ppp2ppp/2np4/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 4',
            solution: 'Qxf7+',
            explanation: 'Queen sacrifice leading to checkmate in 2 moves. After Qxf7+, Kxf7, Bd5+ forces the king to move, and then Bxc6+ wins the queen.',
            game: 'Blitz match on Chess.com vs. player rated 1850',
            evaluation: '-4.2',
            difficulty: 'Intermediate'
        },
        {
            fen: 'r2qkb1r/pp2nppp/3p4/2pNN3/2BnP3/3P4/PPP2PPP/R1BbK2R w KQkq - 1 8',
            solution: 'Nf6+',
            explanation: 'Knight fork attacking the king and queen simultaneously. After gxf6, Bxd1 wins the queen.',
            game: 'Daily game on Lichess.org vs. player rated 1720',
            evaluation: '-3.5',
            difficulty: 'Advanced'
        },
        {
            fen: '2r3k1/pp3pp1/2n1p2p/2P5/3P4/PB3qP1/1P1Q1P1P/R3R1K1 b - - 0 1',
            solution: 'Qg2+',
            explanation: 'Forced mate in 3. After Qg2+, Kxg2, Rxc5 threatening the queen, and then Re8# is coming.',
            game: 'Rapid tournament game vs. player rated 1600',
            evaluation: '+5.7',
            difficulty: 'Challenging'
        }
    ];
    
    let currentPuzzle;
    
    // Simulate loading a puzzle with a slight delay
    setTimeout(displayRandomPuzzle, 1500);
    
    // Display a random puzzle from our mock data
    function displayRandomPuzzle() {
        // Remove placeholder if it exists
        const placeholder = chessBoard.querySelector('.chess-board-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Select random puzzle
        currentPuzzle = mockPuzzles[Math.floor(Math.random() * mockPuzzles.length)];
        
        // In a real implementation, we would fetch from our API:
        // fetch('https://api.example.com/chess-blunder')
        //     .then(response => response.json())
        //     .then(data => {
        //         currentPuzzle = data;
        //         displayPuzzle();
        //     });
        
        displayPuzzle();
    }
    
    function displayPuzzle() {
        // Update puzzle details
        gameInfo.textContent = currentPuzzle.game;
        positionEval.textContent = currentPuzzle.evaluation;
        puzzleDifficulty.textContent = currentPuzzle.difficulty;
        
        // Update solution details (hidden initially)
        solutionMove.textContent = currentPuzzle.solution;
        solutionExplanation.textContent = currentPuzzle.explanation;
        solutionContainer.style.display = 'none';
        
        // In a real implementation, we would use chess.js and chessboard.js:
        // const board = Chessboard('chess-board', {
        //     position: currentPuzzle.fen,
        //     draggable: true,
        //     dropOffBoard: 'snapback',
        //     onDrop: handleMove
        // });
        
        // For mockup, just show a message where the board would be
        chessBoard.innerHTML = `
            <div class="chess-board-content">
                <p style="text-align: center; padding: 20px;">
                    <strong>Chess Board Position</strong><br>
                    FEN: ${currentPuzzle.fen}<br><br>
                    <i>The actual chess board would be rendered here using chessboard.js</i>
                </p>
            </div>
        `;
    }
    
    // Event listeners
    showSolutionBtn.addEventListener('click', function() {
        solutionContainer.style.display = 'block';
    });
    
    tryAnotherBtn.addEventListener('click', function() {
        // Hide solution first
        solutionContainer.style.display = 'none';
        
        // Display placeholder while "loading"
        chessBoard.innerHTML = `
            <div class="chess-board-placeholder">
                <i class="fas fa-chess-knight"></i>
                <p>Loading next blunder...</p>
            </div>
        `;
        
        // Load new puzzle with a slight delay
        setTimeout(displayRandomPuzzle, 1000);
    });
}); 