# Personal Portfolio Website

A clean, responsive personal portfolio website to showcase your projects and social links.

## Features

- Responsive design that works on all devices
- Clean, modern UI
- Sections for about me, social links, and projects
- Interactive chess puzzle widget featuring your latest blunders
- Easy to customize with your own content
- Smooth animations
- No complex frameworks or dependencies

## Chess Puzzle Widget

The website includes an interactive chess puzzle widget that displays your latest chess blunders, allowing visitors to solve them.

### How It Works

1. A GitHub Action runs daily to fetch your recent games from Chess.com or Lichess
2. It analyzes the games to find blunders using the Stockfish chess engine
3. The puzzles are stored in `puzzles.json` and served directly from your website
4. Visitors can interact with the chess board to solve the puzzles
5. No backend server is required

### Configuration

You can customize the chess widget by:

1. Setting GitHub Secrets in your repository:
   - `CHESS_USERNAME`: Your Chess.com or Lichess username
   - `CHESS_PLATFORM`: Either "chess.com" or "lichess"

2. Editing the `generate_puzzles.py` script to change:
   - The number of games to analyze (`MAX_GAMES`)
   - The threshold for what counts as a blunder (`BLUNDER_THRESHOLD`)
   - How puzzle difficulty is calculated

3. Manually triggering the GitHub Action to generate new puzzles:
   - Go to the "Actions" tab in your GitHub repository
   - Select the "Generate Chess Puzzles" workflow
   - Click "Run workflow"

## Chess Puzzles Generator

A Python package for generating chess puzzles from your own games. The system analyzes your games, detects blunders, and creates tactical puzzles that you can use to improve your skills.

### Features

- Analyze your games from Lichess or Chess.com
- Detect blunders using configurable detection criteria
- Generate puzzles from the detected blunders
- Save evaluation data for further analysis
- Configurable strictness levels for blunder detection

### Installation

1. Clone this repository
2. Install the requirements:

```bash
pip install -r requirements-chess.txt
```

3. Make sure you have Stockfish installed, or the program will try to download it automatically

### Usage

Run the chess puzzle generator with the wrapper script:

```bash
python run_chess_puzzles.py
```

You can customize the behavior with command-line arguments:

```bash
python run_chess_puzzles.py --username YourUsername --platform lichess --count 10
```

Available options:

- `--username`: Username to fetch games for (default: from config)
- `--platform`: Platform to fetch games from (lichess or chess.com)
- `--output`: Output file for generated puzzles
- `--count`: Number of recent games to analyze
- `--strictness`: Strictness level for blunder detection (strict, standard, relaxed, all)
- `--blunder-threshold`: Threshold for blunder detection in centipawns
- `--pgn`: Analyze games from a local PGN file instead of fetching from online
- `--stockfish-path`: Path to Stockfish executable (will download if not provided)
- `--verbose`: Enable verbose output

### Package Structure

The `chess_puzzles` package is structured as follows:

```
chess_puzzles/
├── __init__.py         # Package initialization
├── config.py           # Configuration settings
├── main.py             # Main entry point
├── analysis/           # Position analysis and blunder detection
├── engine/             # Stockfish engine integration
├── game/               # Game fetching from online platforms
├── puzzle/             # Puzzle generation and formatting
└── utils/              # Helper utilities
```

### Testing

Run the test suite with:

```bash
pytest test_chess_puzzles.py
```

### Configuration

You can configure the behavior by setting environment variables or by modifying `chess_puzzles/config.py`.

Key configuration options:
- `USERNAME`: Username to fetch games for
- `PLATFORM`: Platform to fetch games from (lichess or chess.com)
- `MAX_GAMES`: Number of games to analyze
- `BLUNDER_THRESHOLD`: Threshold for blunder detection in centipawns
- `STRICTNESS_LEVELS`: Configuration for different strictness levels

### Analyzing Evaluation Distributions

The package includes a script to analyze the distribution of evaluation changes and help determine appropriate thresholds for blunder detection. After generating puzzles, you can run:

```bash
python analyze_eval_distribution.py --player-only
```

This script will:
1. Analyze the evaluation changes recorded in the position_evaluations.json file
2. Generate visualizations of the distribution of centipawn losses
3. Provide statistical insights about the evaluation changes
4. Generate recommended thresholds based on your games
5. Save plots to the 'plots' directory

Options:
- `--input/-i`: Path to the position evaluations file (default: "position_evaluations.json")
- `--output-dir/-o`: Directory to save output plots (default: "plots")
- `--player-only/-p`: Analyze only moves made by the player (recommended)

The script will generate multiple visualizations:
- Distribution of evaluation changes across different ranges
- Cumulative distribution with markers at potential thresholds
- Game-by-game average and maximum evaluation changes

## How to Customize

### Basic Information

1. Open `index.html` and replace:
   - "Your Name" with your actual name
   - The tagline with your profession/interests
   - The "About Me" text with your own introduction
   - Update social media links with your own profiles
   - Add your projects with descriptions and links

### Adding More Projects

To add more projects, simply copy one of the existing project card divs and customize it:

```html
<div class="project-card">
    <h3>Your Project Name</h3>
    <p>Description of your project.</p>
    <div class="project-links">
        <a href="#" target="_blank">View Project</a>
        <a href="#" target="_blank">Source Code</a>
    </div>
</div>
```

### Customizing Colors

To change the color scheme, modify the CSS variables in `css/style.css`:

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #3b82f6;
    /* Other color variables */
}
```

## Deployment Options

### 1. GitHub Pages (Free)

1. Create a GitHub repository
2. Push your website files to the repository
3. Go to repository Settings > Pages
4. Choose the branch (usually `main`) and save
5. Your site will be published at `https://yourusername.github.io/repositoryname/`

### 2. Netlify (Free)

1. Sign up on [Netlify](https://www.netlify.com/)
2. Drag and drop your website folder to Netlify's upload area
3. Or connect your GitHub repository for continuous deployment
4. Your site will be published with a Netlify subdomain
5. You can add a custom domain if desired

### 3. Vercel (Free)

1. Sign up on [Vercel](https://vercel.com/)
2. Connect your GitHub repository
3. Configure the deployment settings
4. Your site will be published with a Vercel subdomain
5. You can add a custom domain if desired

## Using a Custom Domain

If you already own a domain name, you can point it to any of the above hosting services. Each service provides instructions for adding custom domains in their documentation.

## Local Development

To preview your site locally, simply open the `index.html` file in a web browser. No server is required for this static website.

## License

Feel free to use this template for your personal website. 