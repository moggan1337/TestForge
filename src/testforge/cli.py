#!/usr/bin/env python3
"""
TestForge CLI - Command-line interface for mutation testing.
"""

import sys
import os
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from testforge.core.mutator import Mutator, MutationStrategy
from testforge.core.executor import MutationExecutor, ExecutionConfig
from testforge.core.analyzer import MutationAnalyzer
from testforge.core.scorer import EffectivenessScorer
from testforge.core.mutation import MutationSession, OperatorType
from testforge.analysis.coverage import CoverageAnalyzer
from testforge.reporting.generator import ReportGenerator, ReportConfig
from testforge.reporting.visualizer import MutationVisualizer
from testforge.debugging.time_travel import TimeTravelDebugger
from testforge.autogen.test_generator import TestGenerator
from testforge.cicd.pipeline import CIPipeline, CIConfig, CIPlatform
from testforge.utils.helpers import (
    setup_logging,
    load_config,
    parse_cli_args,
    validate_project,
    format_duration,
    format_percentage,
    colorize,
    create_progress_bar,
)
import time


def run_mutation_tests(args, logger):
    """Run mutation testing."""
    logger.info("Starting mutation testing...")
    
    project_root = Path.cwd()
    
    # Validate project
    validation = validate_project(project_root)
    if not validation["valid"]:
        logger.error("Project validation failed:")
        for issue in validation["issues"]:
            logger.error(f"  - {issue}")
        return 1
    
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(warning)
    
    # Load source files
    source_files = []
    if args.files:
        source_files = [Path(f) for f in args.files]
    else:
        # Find source files based on framework
        pattern = validation["test_framework"]
        if pattern == "pytest":
            source_files = list(project_root.rglob("*.py"))
        elif pattern == "jest":
            source_files = list(project_root.rglob("*.js")) + list(project_root.rglob("*.ts"))
        # Filter out test files
        source_files = [f for f in source_files if not f.name.startswith("test_") and not f.name.endswith("_test.py")]
    
    if not source_files:
        logger.error("No source files found")
        return 1
    
    logger.info(f"Found {len(source_files)} source files")
    
    # Parse operators
    operators = None
    if args.operators:
        operators = [OperatorType(o) for o in args.operators]
    
    # Create session
    session = MutationSession(project_root)
    
    # Generate mutations
    logger.info("Generating mutations...")
    start_time = time.time()
    
    for source_file in source_files:
        try:
            mutator = Mutator(
                source_file,
                operators=operators,
                strategy=MutationStrategy.ALL,
                exclude_patterns=args.exclude or [],
            )
            mutations = mutator.generate_mutations()
            
            for mutation in mutations:
                session.add_mutation(mutation)
        except Exception as e:
            logger.warning(f"Failed to process {source_file}: {e}")
    
    mutation_time = time.time() - start_time
    logger.info(f"Generated {len(session.mutations)} mutations in {format_duration(mutation_time)}")
    
    if not session.mutations:
        logger.warning("No mutations generated")
        return 0
    
    # Find test files
    test_files = []
    if validation["test_framework"] == "pytest":
        test_files = list(project_root.rglob("test*.py"))
        test_files += list(project_root.rglob("*_test.py"))
    elif validation["test_framework"] == "jest":
        test_files = list(project_root.rglob("*.test.js"))
        test_files += list(project_root.rglob("*.spec.js"))
    
    logger.info(f"Found {len(test_files)} test files")
    
    # Execute mutations
    logger.info("Executing mutations...")
    exec_config = ExecutionConfig(
        timeout=30.0,
        parallel_workers=args.parallel,
        test_framework=validation["test_framework"],
    )
    
    # Load source code for first file as example
    with open(source_files[0]) as f:
        source_code = f.read()
    
    start_time = time.time()
    
    def progress_callback(current, total):
        bar = create_progress_bar(current, total)
        print(f"\r{bar}", end="", flush=True)
    
    with MutationExecutor(exec_config) as executor:
        results = executor.execute_mutations_parallel(
            session.mutations,
            source_code,
            test_files,
            progress_callback=progress_callback,
        )
    
    print()  # New line after progress
    
    for result in results:
        session.add_result(result)
    
    exec_time = time.time() - start_time
    logger.info(f"Execution completed in {format_duration(exec_time)}")
    
    # Analyze results
    logger.info("Analyzing results...")
    analyzer = MutationAnalyzer()
    analysis = analyzer.analyze_session(session)
    
    # Compute score
    scorer = EffectivenessScorer()
    score, grade, components = scorer.compute_score(session)
    
    # Print summary
    print("\n" + "=" * 60)
    print("MUTATION TESTING RESULTS")
    print("=" * 60)
    print(f"Total Mutations: {analysis.summary.get('total_mutations', 0)}")
    print(f"Killed: {colorize(str(analysis.summary.get('killed', 0)), 'green')}")
    print(f"Survived: {colorize(str(analysis.summary.get('survived', 0)), 'red')}")
    print(f"Errors: {analysis.summary.get('errors', 0)}")
    print(f"Kill Rate: {format_percentage(analysis.summary.get('killed', 0), analysis.summary.get('total_mutations', 1))}")
    print(f"Score: {score:.2f}% (Grade: {grade.value})")
    print("=" * 60)
    
    # Check threshold
    passed = score >= args.threshold
    
    if args.output or args.format:
        report_config = ReportConfig(
            format=args.format or "html",
            output_path=args.output,
        )
        generator = ReportGenerator(report_config)
        
        output_path = args.output or Path(f"mutation_report.{args.format or 'html'}")
        generator.generate_report(session, output_path)
        logger.info(f"Report saved to {output_path}")
    
    # Print recommendations
    if analysis.recommendations:
        print("\nRecommendations:")
        for rec in analysis.recommendations[:5]:
            print(f"  - {rec}")
    
    return 0 if passed else 1


def init_testforge(args, logger):
    """Initialize TestForge in a project."""
    project_root = Path.cwd()
    
    # Create directory structure
    (project_root / ".testforge").mkdir(exist_ok=True)
    
    # Create config file
    config = {
        "version": "1.0.0",
        "threshold": 80.0,
        "parallel_workers": 4,
        "operators": ["AOR", "LOR", "ROR", "ASR", "RVR"],
        "exclude_patterns": ["test_", "_test", "conftest"],
        "report_format": "html",
    }
    
    config_path = project_root / ".testforge" / "config.json"
    import json
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created configuration at {config_path}")
    
    # Generate CI configuration if requested
    if args.ci:
        ci_config = CIConfig()
        pipeline = CIPipeline(ci_config)
        
        if args.ci == "github":
            path = project_root / ".github" / "workflows" / "mutation-testing.yml"
            path.parent.mkdir(parents=True, exist_ok=True)
            pipeline.generate_github_actions(project_root, path)
            logger.info(f"Created GitHub Actions workflow at {path}")
        elif args.ci == "gitlab":
            path = project_root / ".gitlab-ci.yml"
            pipeline.generate_gitlab_ci(project_root, path)
            logger.info(f"Created GitLab CI config at {path}")
        elif args.ci == "jenkins":
            path = project_root / "Jenkinsfile"
            pipeline.generate_jenkinsfile(project_root, path)
            logger.info(f"Created Jenkinsfile at {path}")
    
    logger.info("TestForge initialized successfully!")
    return 0


def generate_report(args, logger):
    """Generate report from mutation testing results."""
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    # Load results
    import json
    with open(args.input) as f:
        data = json.load(f)
    
    # Create session from data
    session = MutationSession(Path.cwd())
    for result_data in data.get("results", []):
        from testforge.core.mutation import MutationResult
        session.add_result(MutationResult.from_dict(result_data))
    
    # Generate report
    report_config = ReportConfig(
        format=args.format,
        output_path=args.output,
    )
    
    generator = ReportGenerator(report_config)
    output_path = args.output or Path(f"mutation_report.{args.format}")
    generator.generate_report(session, output_path)
    
    logger.info(f"Report saved to {output_path}")
    return 0


def debug_mutation(args, logger):
    """Debug a surviving mutation."""
    debugger = TimeTravelDebugger(Path.cwd())
    
    # Load session data
    session_path = Path(".testforge") / "last_session.json"
    if not session_path.exists():
        logger.error("No mutation session found. Run 'testforge run' first.")
        return 1
    
    import json
    with open(session_path) as f:
        data = json.load(f)
    
    # Find mutation
    mutation_data = None
    for result in data.get("results", []):
        if result.get("mutation", {}).get("id") == args.mutation_id:
            mutation_data = result
            break
    
    if not mutation_data:
        logger.error(f"Mutation not found: {args.mutation_id}")
        return 1
    
    from testforge.core.mutation import MutationResult, Mutation
    mutation = Mutation.from_dict(mutation_data["mutation"])
    result = MutationResult.from_dict(mutation_data)
    
    # Debug
    debug_session = debugger.create_debug_session(mutation, result)
    debugger.trace_execution(mutation, [])
    
    # Generate report
    output_path = args.output or Path(f"debug_{args.mutation_id}.md")
    debugger.generate_debug_report(debug_session, output_path)
    
    logger.info(f"Debug report saved to {output_path}")
    return 0


def generate_tests(args, logger):
    """Generate tests for surviving mutations."""
    # Load session
    session_path = args.input or Path(".testforge") / "last_session.json"
    if not session_path.exists():
        logger.error("No mutation session found. Run 'testforge run' first.")
        return 1
    
    import json
    with open(session_path) as f:
        data = json.load(f)
    
    # Extract surviving mutations
    from testforge.core.mutation import Mutation, MutationStatus
    surviving = []
    for result in data.get("results", []):
        if result.get("status") == "survived":
            surviving.append(Mutation.from_dict(result["mutation"]))
    
    if not surviving:
        logger.info("No surviving mutations found!")
        return 0
    
    logger.info(f"Found {len(surviving)} surviving mutations")
    
    # Generate tests
    generator = TestGenerator()
    
    # Find source file
    if surviving:
        source_file = surviving[0].source_file
        with open(source_file) as f:
            source_code = f.read()
        
        tests = generator.generate_tests_for_mutations(surviving, source_code)
        
        # Write tests
        output_path = args.output
        generator.write_test_file(tests, output_path)
        
        logger.info(f"Generated {len(tests)} tests to {output_path}")
    
    return 0


def main():
    """Main entry point."""
    args = parse_cli_args()
    
    # Set up logging
    logger = setup_logging(
        level="DEBUG" if args.verbose else "INFO",
        log_file=args.log_file,
        verbose=args.verbose,
    )
    
    # Load config if provided
    if args.config:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
    
    # Dispatch command
    try:
        if args.command == "run":
            return run_mutation_tests(args, logger)
        elif args.command == "init":
            return init_testforge(args, logger)
        elif args.command == "report":
            return generate_report(args, logger)
        elif args.command == "debug":
            return debug_mutation(args, logger)
        elif args.command == "generate":
            return generate_tests(args, logger)
        else:
            # Default: run
            return run_mutation_tests(args, logger)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
