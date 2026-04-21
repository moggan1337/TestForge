# TestForge - Mutation Testing Framework

<div align="center">

![TestForge Logo](https://img.shields.io/badge/TestForge-Mutation%20Testing-blue)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

**A comprehensive mutation testing framework for evaluating and improving test suite effectiveness.**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation) • [CLI Reference](#cli-reference) • [API Reference](#api-reference) • [Configuration](#configuration) • [CI/CD Integration](#cicd-integration)

</div>

---

## 🎬 Demo
![TestForge Demo](demo.gif)

*Mutation testing for test suite quality*

## Screenshots
| Component | Preview |
|-----------|---------|
| Mutation Results | ![results](screenshots/mutation-results.png) |
| Kill Matrix | ![matrix](screenshots/kill-matrix.png) |
| Coverage View | ![coverage](screenshots/coverage.png) |

## Visual Description
Mutation results show killed vs survived mutants with operators. Kill matrix displays test-mutant relationships. Coverage view shows line and branch coverage with mutations.

---


## Table of Contents

1. [Introduction](#introduction)
2. [What is Mutation Testing?](#what-is-mutation-testing)
3. [Features](#features)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Mutation Operators](#mutation-operators)
7. [Coverage Analysis](#coverage-analysis)
8. [Test Effectiveness Scoring](#test-effectiveness-scoring)
9. [Kill Matrix Analysis](#kill-matrix-analysis)
10. [CLI Reference](#cli-reference)
11. [API Reference](#api-reference)
12. [Configuration](#configuration)
13. [CI/CD Integration](#cicd-integration)
14. [Time-Travel Debugging](#time-travel-debugging)
15. [Auto-Test Generation](#auto-test-generation)
16. [Framework Integrations](#framework-integrations)
17. [Report Visualization](#report-visualization)
18. [Advanced Usage](#advanced-usage)
19. [Examples](#examples)
20. [Contributing](#contributing)
21. [License](#license)

---

## Introduction

TestForge is a state-of-the-art mutation testing framework designed to help software teams evaluate and improve the effectiveness of their test suites. Mutation testing is widely recognized as one of the most thorough methods for assessing test quality, but traditional implementations often suffer from performance issues and limited language support.

TestForge addresses these challenges by providing:

- **High Performance**: Parallel mutation execution with intelligent caching
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, Go, and more
- **Comprehensive Analysis**: Detailed reports with actionable insights
- **CI/CD Integration**: Seamless integration with GitHub Actions, GitLab CI, Jenkins, and more
- **Intelligent Suggestions**: AI-powered recommendations for improving test coverage

---

## What is Mutation Testing?

Mutation testing is a fault-based testing technique that evaluates the quality of a test suite by introducing small changes (mutations) to the source code and verifying that the existing tests detect these changes.

### The Core Concept

1. **Create Mutants**: Introduce small changes (mutations) to the source code
2. **Run Tests**: Execute the test suite against each mutated version
3. **Analyze Results**: Determine if tests "kill" the mutant (detect the change) or if it "survives"

### Why Mutation Testing?

Traditional code coverage metrics tell you *which lines* are executed, but not *how well* they are tested. Mutation testing addresses this gap by revealing:

- **Hidden bugs**: Tests that pass but don't actually verify behavior
- **Weak assertions**: Tests that check the wrong things
- **Missing edge cases**: Scenarios not covered by existing tests
- **Flaky tests**: Tests that pass randomly
- **Dead code**: Code that isn't tested at all

### The Mutation Score

The **Mutation Score** (also called the **Adequacy Score**) is the primary metric:

```
Mutation Score = (Mutations Killed / Total Mutations) × 100%
```

| Score Range | Grade | Interpretation |
|-------------|-------|----------------|
| 90-100% | A | Excellent - Tests are highly effective |
| 80-89% | B | Good - Tests are effective with minor improvements possible |
| 70-79% | C | Acceptable - Tests are adequate but should be improved |
| 50-69% | D | Needs Improvement - Significant testing gaps exist |
| 0-49% | F | Poor - Tests are ineffective and need major work |

### Example

Consider this simple function:

```python
def divide(a, b):
    return a / b
```

A mutation testing tool might introduce these mutations:

| Mutation | Original | Changed To | Expected Test Behavior |
|----------|----------|------------|----------------------|
| AOR | `/` | `*` | Test should FAIL (divide becomes multiply) |
| AOR | `/` | `-` | Test should FAIL |
| NVR | `b` | `0` | Test should handle division by zero |
| SOD | `return` | removed | Test should verify return value exists |

If your test suite catches 3 out of 4 mutations, your mutation score is 75%.

---

## Features

### Core Features

- **Code Mutation Operators**: 15+ mutation types including:
  - Arithmetic Operator Replacement (AOR)
  - Logical Operator Replacement (LOR)
  - Relational Operator Replacement (ROR)
  - Assignment Operator Replacement (ASR)
  - Return Value Replacement (RVR)
  - Conditional Replacement (CRP)
  - Statement Operator Deletion (SOD)
  - Null Value Replacement (NVR)
  - Exception Context Replacement (ECR)

- **Test Suite Effectiveness Scoring**
  - Weighted scoring algorithm
  - Coverage bonuses
  - Operator consistency analysis
  - Time efficiency metrics
  - Redundancy detection

- **Kill Matrix Analysis**
  - Visual representation of test-mutation relationships
  - Identification of weak spots
  - Test ranking by effectiveness
  - Correlation analysis

- **Coverage-Guided Mutation Selection**
  - Integration with coverage tools
  - Focus on executed code paths
  - Reduced false positives
  - Faster execution

- **Parallel Mutation Execution**
  - Multi-process execution
  - Intelligent work distribution
  - Result caching
  - Progress tracking

### Integration Features

- **Framework Integrations**:
  - pytest (Python)
  - Jest (JavaScript/TypeScript)
  - JUnit (Java)
  - Go testing (Go)
  - Generic command execution

- **CI/CD Integration**:
  - GitHub Actions
  - GitLab CI
  - Jenkins
  - CircleCI
  - Azure DevOps

### Analysis Features

- **Time-Travel Debugging**
  - Detailed execution traces
  - Variable state inspection
  - Call stack analysis
  - Step-by-step reproduction

- **Auto-Test Generation**
  - AI-powered test creation
  - Targeted mutation coverage
  - Edge case identification
  - Multiple test templates

- **Report Visualization**
  - HTML dashboards
  - Interactive charts
  - Kill matrix heatmaps
  - Trend analysis

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### From PyPI (Recommended)

```bash
pip install testforge
```

### From Source

```bash
# Clone the repository
git clone https://github.com/moggan1337/TestForge.git
cd TestForge

# Install in development mode
pip install -e ".[dev]"

# Or install normally
pip install .
```

### Using uv (Fast Installation)

```bash
uv pip install testforge
```

### Verify Installation

```bash
testforge --version
# TestForge version 1.0.0
```

---

## Quick Start

### Initialize TestForge in Your Project

```bash
cd your-project
testforge init
```

This creates a `.testforge/config.json` configuration file.

### Run Mutation Testing

```bash
# Run with default settings
testforge run

# Run with custom threshold
testforge run --threshold 90

# Run specific files
testforge run src/module1.py src/module2.py

# Run with verbose output
testforge run -v
```

### View the Report

After running, TestForge generates an HTML report:

```bash
# Report is saved to mutation_report.html
open mutation_report.html
```

### Generate CI/CD Configuration

```bash
# GitHub Actions
testforge init --ci github

# GitLab CI
testforge init --ci gitlab

# Jenkins
testforge init --ci jenkins
```

---

## Mutation Operators

TestForge implements a comprehensive set of mutation operators that cover different aspects of code behavior.

### Arithmetic Operator Replacement (AOR)

Replaces arithmetic operators with alternatives to detect calculation errors.

```python
# Original
result = a + b
result = x / y
result = count * 2

# Mutated
result = a - b    # + → -
result = a * b    # + → *
result = a / b    # + → /
result = x * y    # / → *
result = x - y    # / → -
result = count / 2  # * → /
result = count + 2  # * → +
```

### Logical Operator Replacement (LOR)

Swaps logical operators to catch boolean logic errors.

```python
# Original
if user.is_authenticated and user.has_permission:
    grant_access()

# Mutated (AND → OR)
if user.is_authenticated or user.has_permission:
    grant_access()
```

### Relational Operator Replacement (ROR)

Changes comparison operators to detect boundary condition issues.

```python
# Original
if age >= 18:
    allow_vote()
if balance < 0:
    charge_fee()

# Mutated
if age > 18:       # >= → >
if age <= 18:      # >= → <=
if balance <= 0:   # < → <=
if balance == 0:   # < → ==
```

### Assignment Operator Replacement (ASR)

Modifies compound assignment operators.

```python
# Original
counter += 1
total *= multiplier

# Mutated
counter -= 1    # += → -=
counter /= 1    # += → /=
total /= multiplier  # *= → /=
```

### Return Value Replacement (RVR)

Changes return values to verify proper assertions.

```python
# Original
def is_valid(data):
    return True

# Mutated
def is_valid(data):
    return False  # Kills tests that don't check specific values
```

### Conditional Replacement (CRP)

Inverts or swaps conditional logic.

```python
# Original
if status == "active":
    process()
else:
    skip()

# Mutated
if status != "active":  # == → !=
    process()
else:
    skip()
```

### Statement Operator Deletion (SOD)

Removes or empties statements to verify they're not critical.

```python
# Original
def process(data):
    validate(data)
    return transform(data)

# Mutated
def process(data):
    # validate(data) removed
    return transform(data)
```

### Null Value Replacement (NVR)

Substitutes null values to check null handling.

```python
# Original
user = get_user(id)
name = user.name

# Mutated
user = None  # Check null handling
name = user.name  # Should raise or be handled
```

### Exception Context Replacement (ECR)

Modifies exception handling.

```python
# Original
try:
    risky_operation()
except ValueError:
    handle_bad_input()

# Mutated
try:
    risky_operation()
except Exception:  # ValueError → Exception
    handle_bad_input()
```

---

## Coverage Analysis

TestForge integrates with coverage tools to provide intelligent mutation selection.

### How It Works

1. **Run Tests with Coverage**: Execute your test suite with coverage enabled
2. **Identify Covered Lines**: Determine which lines are actually executed
3. **Filter Mutations**: Only create mutations for covered code
4. **Prioritize**: Focus on high-impact mutations

### Benefits

- **Reduced Noise**: Ignore mutations in dead code
- **Faster Execution**: Fewer mutations to test
- **Better Focus**: Target code that's actually used
- **Accurate Metrics**: Coverage-aware scoring

### Supported Coverage Tools

| Language | Tool | Command |
|----------|------|---------|
| Python | coverage.py | `pytest --cov` |
| Python | pytest-cov | `pytest --cov=.` |
| JavaScript | Istanbul | `jest --coverage` |
| Java | JaCoCo | `mvn test jacoco:report` |
| Go | go test -cover | `go test -coverprofile` |

### Example

```python
from testforge.analysis import CoverageAnalyzer

# Run coverage analysis
analyzer = CoverageAnalyzer()
coverage_data = analyzer.run_coverage(
    test_command="pytest --cov=src",
    source_files=["src/module.py"],
)

# Get coverage for specific file
covered_lines = coverage_data.get_covered_lines("src/module.py")
print(f"Covered lines: {covered_lines}")
```

---

## Test Effectiveness Scoring

TestForge provides a sophisticated scoring system that goes beyond simple kill percentage.

### Score Components

1. **Base Score** (60% weight)
   - Raw mutation kill percentage
   - Primary effectiveness indicator

2. **Coverage Bonus** (20% weight)
   - Diversity of covered files
   - Line distribution analysis
   - Up to +10 points

3. **Operator Consistency** (10% weight)
   - Consistent operator kill rates
   - Penalizes high variance

4. **Time Efficiency** (10% weight)
   - Average execution time
   - Execution time variance

5. **Redundancy Penalty** (up to -10%)
   - Overlapping test coverage
   - Duplicate kills

### Computing Your Score

```python
from testforge.core.scorer import EffectivenessScorer

scorer = EffectivenessScorer(
    mutation_threshold=0.8,
    coverage_weight=0.2,
    time_weight=0.1,
)

score, grade, components = scorer.compute_score(session)

print(f"Score: {score:.2f}%")
print(f"Grade: {grade.value}")
print(f"Base: {components.base_score:.2f}")
print(f"Coverage Bonus: +{components.coverage_bonus:.2f}")
```

---

## Kill Matrix Analysis

The Kill Matrix is a fundamental data structure that tracks which tests kill which mutations.

### Structure

```
         | Test A | Test B | Test C | Test D |
---------|--------|--------|--------|--------|
Mut 1    |   X    |        |   X    |        |
Mut 2    |        |   X    |        |   X    |
Mut 3    |   X    |   X    |        |   X    |
Mut 4    |        |        |        |   X    |
```

### Analysis Capabilities

```python
from testforge.core.mutation import KillMatrix

matrix = session.kill_matrix

# Get surviving mutations
survivors = matrix.get_surviving_mutations()

# Get killing tests for a mutation
killing_tests = matrix.get_killing_tests("mutation_id_123")

# Rank tests by effectiveness
from testforge.core.scorer import EffectivenessScorer
scorer = EffectivenessScorer()
rankings = scorer.rank_tests(session)
```

### Visualizations

Generate heatmaps and charts:

```python
from testforge.reporting.visualizer import MutationVisualizer

viz = MutationVisualizer()
viz.create_kill_matrix_heatmap(matrix, output_path="heatmap.html")
```

---

## CLI Reference

### Global Options

```bash
testforge [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `--log-file PATH` | Log file path |
| `-c, --config PATH` | Config file path |

### Commands

#### `run` - Run Mutation Testing

```bash
testforge run [FILES]... [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --threshold` | Minimum score to pass | 80.0 |
| `-p, --parallel` | Parallel workers | 4 |
| `-o, --operators` | Operators to use | All |
| `-f, --format` | Report format | html |
| `-O, --output` | Output file | mutation_report.html |
| `--exclude` | Exclude patterns | - |
| `--framework` | Test framework | pytest |

#### `init` - Initialize Project

```bash
testforge init [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--ci` | Generate CI config (github, gitlab, jenkins, circle, azure) |

#### `report` - Generate Report

```bash
testforge report INPUT [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-O, --output` | Output file |
| `-f, --format` | Report format |

#### `debug` - Debug Mutation

```bash
testforge debug MUTATION_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-O, --output` | Output file |

#### `generate` - Generate Tests

```bash
testforge generate [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--input` | Input results file |
| `-O, --output` | Output test file |

---

## API Reference

### Core Classes

#### `Mutator`

```python
from testforge.core.mutator import Mutator, MutationStrategy

mutator = Mutator(
    source_file="src/module.py",
    operators=[OperatorType.AOR, OperatorType.ROR],
    strategy=MutationStrategy.ALL,
)

mutations = mutator.generate_mutations()
```

#### `MutationExecutor`

```python
from testforge.core.executor import MutationExecutor, ExecutionConfig

config = ExecutionConfig(
    timeout=30.0,
    parallel_workers=4,
    test_framework="pytest",
)

with MutationExecutor(config) as executor:
    results = executor.execute_mutation(mutation, source_code, test_files)
```

#### `MutationAnalyzer`

```python
from testforge.core.analyzer import MutationAnalyzer

analyzer = MutationAnalyzer()
analysis = analyzer.analyze_session(session)

# Access results
print(analysis.summary)
print(analysis.recommendations)
```

#### `EffectivenessScorer`

```python
from testforge.core.scorer import EffectivenessScorer, ScoreGrade

scorer = EffectivenessScorer()
score, grade, components = scorer.compute_score(session)
```

### Reporting

```python
from testforge.reporting.generator import ReportGenerator, ReportConfig

config = ReportConfig(
    format="html",
    include_kill_matrix=True,
    include_charts=True,
)

generator = ReportGenerator(config)
generator.generate_report(session, output_path="report.html")
```

### Debugging

```python
from testforge.debugging.time_travel import TimeTravelDebugger

debugger = TimeTravelDebugger(project_root)
session = debugger.create_debug_session(mutation, result)
debugger.trace_execution(mutation, test_files)
debugger.generate_debug_report(session, output_path="debug.md")
```

### Auto-Test Generation

```python
from testforge.autogen.test_generator import TestGenerator

generator = TestGenerator(language="python")
tests = generator.generate_tests_for_mutations(mutations, source_code)
generator.write_test_file(tests, output_path="generated_tests.py")
```

---

## Configuration

### Configuration File

Create `.testforge/config.json`:

```json
{
    "version": "1.0.0",
    "threshold": 80.0,
    "parallel_workers": 4,
    "operators": ["AOR", "LOR", "ROR", "ASR", "RVR", "CRP", "SOD"],
    "exclude_patterns": ["test_", "_test", "conftest", "__pycache__"],
    "report_format": "html",
    "timeout": 30,
    "test_framework": "pytest",
    "coverage_enabled": true,
    "fail_on_threshold": true
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TESTFORGE_THRESHOLD` | Minimum passing score |
| `TESTFORGE_WORKERS` | Number of parallel workers |
| `TESTFORGE_TIMEOUT` | Execution timeout in seconds |
| `TESTFORGE_CONFIG` | Config file path |

### Programmatic Configuration

```python
from testforge.core.executor import ExecutionConfig

config = ExecutionConfig(
    timeout=60.0,
    max_retries=3,
    parallel_workers=8,
    test_framework="pytest",
    coverage_command="pytest --cov",
    stop_on_first_kill=True,
)
```

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/mutation-testing.yml`:

```yaml
name: Mutation Testing

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  mutation-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install testforge
      - run: testforge run --threshold 80
      - uses: actions/upload-artifact@v4
        with:
          name: mutation-report
          path: mutation_report.html
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
mutation_testing:
  stage: test
  image: python:3.11-slim
  script:
    - pip install testforge
    - testforge run --threshold 80
  artifacts:
    paths:
      - mutation_report.html
    expire_in: 30 days
```

### Jenkins

```groovy
pipeline {
    agent { docker { image 'python:3.11' } }
    
    stages {
        stage('Mutation Testing') {
            steps {
                sh 'pip install testforge'
                sh 'testforge run --threshold 80'
            }
        }
    }
}
```

---

## Time-Travel Debugging

When a mutation survives, TestForge's time-travel debugger helps you understand why.

### Features

1. **Execution Tracing**: Step through the mutation's execution
2. **Variable Inspection**: See variable states at each step
3. **Coverage Analysis**: Understand what was and wasn't executed
4. **Root Cause Identification**: Find exactly why the mutation survived

### Usage

```bash
# Debug a specific mutation
testforge debug mutation_id_abc123 --output debug_report.md
```

### Programmatic Usage

```python
from testforge.debugging.time_travel import TimeTravelDebugger

debugger = TimeTravelDebugger(project_root)
debug_session = debugger.create_debug_session(mutation, result)

# Trace execution
snapshot = debugger.trace_execution(mutation, test_files)

# Analyze survival reasons
analysis = debugger.analyze_survivor(mutation, result)

print(analysis["survival_reasons"])
print(analysis["suggestions"])
```

---

## Auto-Test Generation

TestForge can automatically generate tests to kill surviving mutations.

### Templates

1. **Assertion Tests**: Basic value assertions
2. **Edge Case Tests**: Boundary and extreme value tests
3. **Boundary Tests**: Tests for comparison operators
4. **Comprehensive Tests**: Parameterized test suites

### Usage

```bash
# Generate tests for surviving mutations
testforge generate --output test_mutations.py
```

### Programmatic Usage

```python
from testforge.autogen.test_generator import TestGenerator

generator = TestGenerator(language="python")
tests = generator.generate_tests_for_mutations(
    surviving_mutations,
    source_code,
)

# Validate and write tests
generator.write_test_file(
    tests,
    output_path=Path("test_mutation_killers.py"),
    existing_tests=existing_test_content,
)
```

---

## Framework Integrations

### pytest (Python)

```bash
pip install pytest pytest-cov
testforge run --framework pytest
```

### Jest (JavaScript/TypeScript)

```bash
npm install jest
testforge run --framework jest
```

### JUnit (Java)

```bash
mvn test
testforge run --framework junit
```

### Go Testing

```bash
go test ./...
testforge run --framework go
```

---

## Report Visualization

### HTML Dashboard

Generate interactive HTML reports:

```bash
testforge run --format html --output report.html
```

### JSON Report

For programmatic access:

```bash
testforge run --format json --output report.json
```

### Markdown Report

For documentation:

```bash
testforge run --format markdown --output report.md
```

### Dashboard Features

- **Kill Rate Gauge**: Visual mutation score display
- **Operator Analysis**: Bar chart of operator effectiveness
- **Test Rankings**: Top tests by mutation kills
- **Surviving Mutations**: Detailed list of untested code
- **Recommendations**: Actionable improvements

---

## Advanced Usage

### Coverage-Guided Mutation

```python
from testforge.core.mutator import CoverageGuidedMutator
from testforge.analysis.coverage import CoverageAnalyzer

# Analyze coverage
analyzer = CoverageAnalyzer()
coverage_data = analyzer.run_coverage("pytest --cov", source_files)

# Generate only covered mutations
mutator = CoverageGuidedMutator(
    source_file="module.py",
    coverage_data={
        "module.py": coverage_data.get_covered_lines("module.py"),
    },
)
```

### Smart Mutation Selection

```python
from testforge.core.mutator import SmartMutator

mutator = SmartMutator(
    source_file="module.py",
    strategy=MutationStrategy.SMART,
    max_mutations_per_file=50,
)

mutations = mutator.generate_mutations()
```

### Comparative Analysis

```python
from testforge.core.analyzer import ComparativeAnalyzer

comparator = ComparativeAnalyzer()
comparison = comparator.compare(baseline_session, current_session)

print(f"Score change: {comparison['score_change']:.2f}%")
```

---

## Examples

### Example 1: Basic Python Testing

```bash
# Initialize
cd myproject
testforge init

# Run
testforge run

# View report
open mutation_report.html
```

### Example 2: With Custom Threshold

```bash
testforge run --threshold 95 --parallel 8
```

### Example 3: Specific Files and Operators

```bash
testforge run \
    src/auth.py src/users.py \
    --operators AOR ROR LOR \
    --format html
```

### Example 4: CI Pipeline

```bash
# GitHub Actions
testforge init --ci github
git add .github/workflows/mutation-testing.yml
git commit -m "Add mutation testing"
git push
```

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting.

### Development Setup

```bash
git clone https://github.com/moggan1337/TestForge.git
cd TestForge
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black src/
isort src/
mypy src/
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## Roadmap

- [ ] Support for more languages (Rust, Ruby, PHP)
- [ ] ML-powered test generation
- [ ] IDE plugins (VS Code, PyCharm)
- [ ] Real-time mutation testing during development
- [ ] Integration with code review tools
- [ ] Historical trend analysis dashboard

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

TestForge builds upon decades of research in mutation testing and software engineering. We thank the academic community for their foundational work in this field.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/moggan1337/TestForge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moggan1337/TestForge/discussions)

---

<div align="center">

**Made with ❤️ by the TestForge Team**

</div>
