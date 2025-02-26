#!/usr/bin/env python3
"""
Analyze position evaluations and generate distribution plots of centipawn losses.

This script reads the position_evaluations.json file and generates various visualizations
to help understand patterns in evaluation changes and determine appropriate thresholds
for blunder detection.
"""
import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_evaluations(file_path="position_evaluations.json"):
    """Load position evaluations from JSON file.
    
    Args:
        file_path (str): Path to the position evaluations JSON file.
        
    Returns:
        list: List of position evaluation data.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get("evaluations", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading evaluations: {e}")
        return []

def filter_player_evaluations(evaluations, player_only=True):
    """Filter evaluations to include only player moves if specified.
    
    Args:
        evaluations (list): List of position evaluation data.
        player_only (bool): Whether to include only player moves.
        
    Returns:
        list: Filtered evaluations.
    """
    if not player_only:
        return evaluations
        
    # Determine which moves are player moves based on the player_turn field
    return [eval_data for eval_data in evaluations if eval_data.get("player_turn") in ["white", "black"]]

def compute_statistics(evaluations):
    """Compute statistics about evaluation changes.
    
    Args:
        evaluations (list): List of position evaluation data.
        
    Returns:
        dict: Statistics about evaluation changes.
    """
    stats = {
        "total_evaluations": len(evaluations),
        "average_absolute_change": 0,
        "median_absolute_change": 0,
        "percentiles": {},
        "count_by_range": defaultdict(int),
        "game_stats": defaultdict(lambda: {"moves": 0, "total_change": 0, "max_change": 0})
    }
    
    # Extract all eval changes
    eval_changes = [abs(e.get("eval_change", 0)) for e in evaluations]
    
    if not eval_changes:
        return stats
        
    # Calculate basic statistics
    stats["average_absolute_change"] = np.mean(eval_changes)
    stats["median_absolute_change"] = np.median(eval_changes)
    
    # Calculate percentiles
    for p in [50, 75, 90, 95, 99]:
        stats["percentiles"][p] = np.percentile(eval_changes, p)
    
    # Count by range
    ranges = [0, 50, 100, 200, 300, 500, 800, 1000, 1500, 2000]
    for i in range(len(ranges)-1):
        lower = ranges[i]
        upper = ranges[i+1]
        count = sum(1 for c in eval_changes if lower <= c < upper)
        stats["count_by_range"][f"{lower}-{upper}"] = count
    
    stats["count_by_range"]["2000+"] = sum(1 for c in eval_changes if c >= 2000)
    
    # Game statistics
    for eval_data in evaluations:
        game_id = eval_data.get("game_id", "unknown")
        change = abs(eval_data.get("eval_change", 0))
        
        stats["game_stats"][game_id]["moves"] += 1
        stats["game_stats"][game_id]["total_change"] += change
        stats["game_stats"][game_id]["max_change"] = max(stats["game_stats"][game_id]["max_change"], change)
    
    # Calculate average change per game
    for game_id, game_stat in stats["game_stats"].items():
        if game_stat["moves"] > 0:
            game_stat["average_change"] = game_stat["total_change"] / game_stat["moves"]
    
    return stats

def plot_eval_change_distribution(evaluations, output_dir="plots"):
    """Plot distribution of evaluation changes.
    
    Args:
        evaluations (list): List of position evaluation data.
        output_dir (str): Directory to save plots.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract eval changes and convert to DataFrame
    eval_changes = [e.get("eval_change", 0) for e in evaluations]
    df = pd.DataFrame({"eval_change": eval_changes})
    
    # Create histograms for different ranges
    plt.figure(figsize=(12, 8))
    
    # Plot distribution of all changes
    plt.subplot(2, 2, 1)
    sns.histplot(data=df, x="eval_change", bins=50, kde=True)
    plt.title("Distribution of All Evaluation Changes")
    plt.xlabel("Evaluation Change (centipawns)")
    plt.ylabel("Count")
    
    # Plot distribution of absolute changes (0-500)
    plt.subplot(2, 2, 2)
    df_abs = pd.DataFrame({"abs_change": [abs(c) for c in eval_changes]})
    df_filtered = df_abs[df_abs["abs_change"] <= 500]
    sns.histplot(data=df_filtered, x="abs_change", bins=50, kde=True)
    plt.title("Distribution of Absolute Changes (0-500 cp)")
    plt.xlabel("Absolute Evaluation Change (centipawns)")
    plt.ylabel("Count")
    
    # Plot distribution of absolute changes (500-2000)
    plt.subplot(2, 2, 3)
    df_filtered = df_abs[(df_abs["abs_change"] > 500) & (df_abs["abs_change"] <= 2000)]
    sns.histplot(data=df_filtered, x="abs_change", bins=50, kde=True)
    plt.title("Distribution of Absolute Changes (500-2000 cp)")
    plt.xlabel("Absolute Evaluation Change (centipawns)")
    plt.ylabel("Count")
    
    # Plot distribution of large changes (>2000)
    plt.subplot(2, 2, 4)
    df_filtered = df_abs[df_abs["abs_change"] > 2000]
    if len(df_filtered) > 0:  # Only plot if there are values
        sns.histplot(data=df_filtered, x="abs_change", bins=20, kde=True)
        plt.title("Distribution of Large Changes (>2000 cp)")
        plt.xlabel("Absolute Evaluation Change (centipawns)")
        plt.ylabel("Count")
    else:
        plt.text(0.5, 0.5, "No evaluation changes >2000 cp", 
                ha="center", va="center", fontsize=12)
        plt.title("Distribution of Large Changes (>2000 cp)")
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/eval_change_distribution.png")
    plt.close()
    
    # Create cumulative distribution plot
    plt.figure(figsize=(10, 6))
    sns.ecdfplot(data=df_abs, x="abs_change")
    
    # Add vertical lines at potential thresholds
    thresholds = [300, 500, 800, 1000, 1500]
    
    for threshold in thresholds:
        percent_below = (df_abs["abs_change"] <= threshold).mean() * 100
        plt.axvline(x=threshold, linestyle='--', alpha=0.7,
                   label=f"{threshold} cp: {percent_below:.1f}% of moves below")
    
    plt.title("Cumulative Distribution of Absolute Evaluation Changes")
    plt.xlabel("Absolute Evaluation Change (centipawns)")
    plt.ylabel("Cumulative Proportion")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(f"{output_dir}/eval_change_cdf.png")
    plt.close()

def plot_game_statistics(stats, output_dir="plots"):
    """Plot game-level statistics.
    
    Args:
        stats (dict): Statistics about evaluation changes.
        output_dir (str): Directory to save plots.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract game statistics
    game_ids = list(stats["game_stats"].keys())
    avg_changes = [stats["game_stats"][g]["average_change"] for g in game_ids]
    max_changes = [stats["game_stats"][g]["max_change"] for g in game_ids]
    
    df = pd.DataFrame({
        "game_id": game_ids,
        "average_change": avg_changes,
        "max_change": max_changes,
        "moves": [stats["game_stats"][g]["moves"] for g in game_ids]
    })
    
    # Sort by average change
    df = df.sort_values("average_change", ascending=False)
    
    # Plot average change by game
    plt.figure(figsize=(12, 6))
    plt.bar(df["game_id"], df["average_change"], alpha=0.7)
    plt.axhline(y=stats["average_absolute_change"], linestyle='--', color='r',
               label=f"Overall Average: {stats['average_absolute_change']:.1f} cp")
    plt.title("Average Evaluation Change by Game")
    plt.xlabel("Game ID")
    plt.ylabel("Average Absolute Change (centipawns)")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/game_average_changes.png")
    plt.close()
    
    # Plot max change by game
    plt.figure(figsize=(12, 6))
    plt.bar(df["game_id"], df["max_change"], alpha=0.7)
    plt.title("Maximum Evaluation Change by Game")
    plt.xlabel("Game ID")
    plt.ylabel("Maximum Absolute Change (centipawns)")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/game_max_changes.png")
    plt.close()

def generate_threshold_recommendations(stats):
    """Generate threshold recommendations based on statistics.
    
    Args:
        stats (dict): Statistics about evaluation changes.
        
    Returns:
        dict: Recommended thresholds.
    """
    recommendations = {
        "small_mistake": int(stats["percentiles"][75]),
        "moderate_mistake": int(stats["percentiles"][90]),
        "significant_mistake": int(stats["percentiles"][95]),
        "blunder": int(stats["percentiles"][99])
    }
    
    # Round to nearest 50
    for key in recommendations:
        recommendations[key] = round(recommendations[key] / 50) * 50
    
    return recommendations

def main():
    parser = argparse.ArgumentParser(description="Analyze chess position evaluations.")
    parser.add_argument("--input", "-i", default="position_evaluations.json",
                      help="Path to position evaluations JSON file")
    parser.add_argument("--output-dir", "-o", default="plots",
                      help="Directory to save output plots")
    parser.add_argument("--player-only", "-p", action="store_true",
                      help="Analyze only player moves")
    
    args = parser.parse_args()
    
    # Load evaluations
    logger.info(f"Loading evaluations from {args.input}")
    evaluations = load_evaluations(args.input)
    
    if not evaluations:
        logger.error("No evaluations found. Make sure the file exists and is correctly formatted.")
        return
    
    logger.info(f"Loaded {len(evaluations)} evaluation records")
    
    # Filter evaluations if needed
    evaluations = filter_player_evaluations(evaluations, args.player_only)
    logger.info(f"Using {len(evaluations)} evaluations after filtering")
    
    # Compute statistics
    stats = compute_statistics(evaluations)
    
    # Generate plots
    logger.info("Generating plots")
    plot_eval_change_distribution(evaluations, args.output_dir)
    plot_game_statistics(stats, args.output_dir)
    
    # Generate recommendations
    recommendations = generate_threshold_recommendations(stats)
    
    # Print statistics
    logger.info("\n=== Evaluation Analysis Results ===")
    logger.info(f"Total positions analyzed: {stats['total_evaluations']}")
    logger.info(f"Average absolute eval change: {stats['average_absolute_change']:.2f} centipawns")
    logger.info(f"Median absolute eval change: {stats['median_absolute_change']:.2f} centipawns")
    
    logger.info("\nDistribution by percentile:")
    for p, value in stats["percentiles"].items():
        logger.info(f"  {p}th percentile: {value:.2f} centipawns")
    
    logger.info("\nCount by range:")
    for range_name, count in stats["count_by_range"].items():
        percentage = (count / stats["total_evaluations"]) * 100
        logger.info(f"  {range_name} cp: {count} moves ({percentage:.1f}%)")
    
    logger.info("\nRecommended thresholds based on your data:")
    for category, threshold in recommendations.items():
        logger.info(f"  {category}: {threshold} centipawns")
    
    logger.info(f"\nPlots have been saved to the '{args.output_dir}' directory")
    
    # Save recommendations to a file
    threshold_file = Path(args.output_dir) / "recommended_thresholds.json"
    with open(threshold_file, 'w') as f:
        json.dump(recommendations, f, indent=2)
    
    logger.info(f"Recommended thresholds saved to {threshold_file}")

if __name__ == "__main__":
    main() 