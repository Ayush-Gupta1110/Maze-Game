"""Main entry point for Maze Explorer."""

import argparse
import sys

from config import DEFAULT_DIFFICULTY, DIFFICULTY_SETTINGS
from game.app import MazeExplorerApp


def parse_arguments() -> argparse.Namespace:
    """Parse command line flags and options."""
    parser = argparse.ArgumentParser(
        description="Maze Explorer - A polished procedural 2D maze game.",
    )
    parser.add_argument(
        "--difficulty",
        choices=list(DIFFICULTY_SETTINGS.keys()),
        default=None,
        help="Initial difficulty mode (Easy, Medium, Hard).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible maze generation.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without displaying a graphical window (for automated testing).",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Exit automatically after running for N frames (for automated verification).",
    )
    return parser.parse_args()


def main() -> int:
    """Initialize and run Maze Explorer."""
    args = parse_arguments()

    try:
        app = MazeExplorerApp(headless=args.headless, seed=args.seed)
        if args.difficulty:
            app.set_difficulty(args.difficulty)
        app.run(max_frames=args.frames)
        return 0
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"Error running Maze Explorer: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
