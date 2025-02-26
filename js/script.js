// Puzzle toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleChessPuzzle');
    const chessPuzzleSection = document.getElementById('chessPuzzleSection');
    
    if (toggleButton && chessPuzzleSection) {
        toggleButton.addEventListener('click', function() {
            // Toggle active class on chess puzzle section
            chessPuzzleSection.classList.toggle('active');
            
            // Update button text based on state
            if (chessPuzzleSection.classList.contains('active')) {
                toggleButton.innerHTML = '<i class="fas fa-chess-knight"></i> Hide Chess Puzzle Challenge';
            } else {
                toggleButton.innerHTML = '<i class="fas fa-chess-knight"></i> Show Chess Puzzle Challenge';
            }
        });
    }
}); 