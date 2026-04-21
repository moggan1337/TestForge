"""
Utility functions for TestForge.
"""

import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        verbose: Enable verbose output
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger("testforge")
    
    # Clear existing handlers
    logger.handlers = []
    
    # Set level
    if verbose:
        level = "DEBUG"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON or YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    with open(config_path) as f:
        if config_path.suffix == ".json":
            return json.load(f)
        elif config_path.suffix in [".yaml", ".yml"]:
            import yaml
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")


def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """
    Save configuration to a JSON or YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save config to
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        if config_path.suffix == ".json":
            json.dump(config, f, indent=2)
        elif config_path.suffix in [".yaml", ".yml"]:
            import yaml
            yaml.dump(config, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")


def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for TestForge.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv)
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="TestForge - Mutation Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run mutation testing")
    run_parser.add_argument(
        "files",
        nargs="*",
        help="Source files to mutate (default: all)",
    )
    run_parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=80.0,
        help="Minimum mutation score to pass (default: 80)",
    )
    run_parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    run_parser.add_argument(
        "--operators", "-o",
        nargs="+",
        help="Mutation operators to use",
    )
    run_parser.add_argument(
        "--format", "-f",
        choices=["html", "json", "markdown"],
        default="html",
        help="Report format (default: html)",
    )
    run_parser.add_argument(
        "--output", "-O",
        type=Path,
        help="Output file path",
    )
    run_parser.add_argument(
        "--exclude",
        nargs="+",
        help="Patterns to exclude",
    )
    run_parser.add_argument(
        "--framework",
        choices=["pytest", "jest", "junit", "go"],
        default="pytest",
        help="Test framework (default: pytest)",
    )
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize TestForge in project")
    init_parser.add_argument(
        "--ci",
        choices=["github", "gitlab", "jenkins", "circle", "azure"],
        help="Generate CI/CD configuration",
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report from results")
    report_parser.add_argument(
        "input",
        type=Path,
        help="Input results file",
    )
    report_parser.add_argument(
        "--output", "-O",
        type=Path,
        help="Output file path",
    )
    report_parser.add_argument(
        "--format", "-f",
        choices=["html", "json", "markdown"],
        default="html",
        help="Report format",
    )
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug surviving mutations")
    debug_parser.add_argument(
        "mutation_id",
        help="Mutation ID to debug",
    )
    debug_parser.add_argument(
        "--output", "-O",
        type=Path,
        help="Output file path",
    )
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate tests for surviving mutations")
    gen_parser.add_argument(
        "--input",
        type=Path,
        help="Input results file",
    )
    gen_parser.add_argument(
        "--output", "-O",
        type=Path,
        default=Path("test_mutation_generated.py"),
        help="Output test file",
    )
    
    # Global options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Log file path",
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Config file path",
    )
    
    return parser.parse_args(args)


def validate_project(project_root: Path) -> Dict[str, Any]:
    """
    Validate a project structure for mutation testing.
    
    Args:
        project_root: Path to project root
        
    Returns:
        Validation results with any issues found
    """
    issues = []
    warnings = []
    info = {}
    
    project_root = Path(project_root)
    
    # Check for test framework indicators
    test_framework = None
    if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists():
        test_framework = "pytest"
        info["test_framework"] = "pytest"
    elif (project_root / "package.json").exists():
        test_framework = "jest"
        info["test_framework"] = "jest"
    elif (project_root / "pom.xml").exists() or (project_root / "build.gradle").exists():
        test_framework = "junit"
        info["test_framework"] = "junit"
    elif (project_root / "go.mod").exists():
        test_framework = "go"
        info["test_framework"] = "go"
    else:
        warnings.append("Could not detect test framework")
    
    # Check for source files
    source_extensions = [".py", ".js", ".ts", ".java", ".go", ".c", ".cpp"]
    source_files = []
    for ext in source_extensions:
        source_files.extend(project_root.rglob(f"*{ext}"))
    
    info["source_files"] = len(source_files)
    
    if not source_files:
        issues.append("No source files found")
    
    # Check for test files
    test_files = []
    for pattern in ["test*.py", "*_test.py", "*.test.js", "*.spec.js", "*Test.java"]:
        test_files.extend(project_root.rglob(pattern))
    
    info["test_files"] = len(test_files)
    
    if not test_files:
        warnings.append("No test files found")
    
    # Check for required directories
    required_dirs = ["src", "lib", "app"]
    found_dirs = [d for d in required_dirs if (project_root / d).exists()]
    info["source_dirs"] = found_dirs
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "info": info,
        "test_framework": test_framework,
    }


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_percentage(value: float, total: float) -> str:
    """
    Format a percentage with appropriate precision.
    
    Args:
        value: Numerator
        total: Denominator
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    
    pct = (value / total) * 100
    
    if pct == 100 or pct == 0:
        return f"{pct:.0f}%"
    elif pct == int(pct):
        return f"{pct:.0f}%"
    else:
        return f"{pct:.1f}%"


def truncate_string(s: str, max_length: int = 50) -> str:
    """
    Truncate a string with ellipsis if too long.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    
    return s[:max_length - 3] + "..."


def colorize(text: str, color: str) -> str:
    """
    Add ANSI color codes to text.
    
    Args:
        text: Text to colorize
        color: Color name (red, green, yellow, blue, magenta, cyan, white)
        
    Returns:
        Colorized text
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    
    color_code = colors.get(color.lower(), "")
    reset_code = colors["reset"]
    
    return f"{color_code}{text}{reset_code}"


def create_progress_bar(
    current: int,
    total: int,
    width: int = 40,
    fill_char: str = "█",
    empty_char: str = "░",
) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        current: Current progress
        total: Total items
        width: Width of bar in characters
        fill_char: Character for filled portion
        empty_char: Character for empty portion
        
    Returns:
        Progress bar string
    """
    if total == 0:
        pct = 0
    else:
        pct = int((current / total) * 100)
    
    filled = int(width * current / total) if total > 0 else 0
    empty = width - filled
    
    bar = fill_char * filled + empty_char * empty
    
    return f"[{bar}] {pct}% ({current}/{total})"
