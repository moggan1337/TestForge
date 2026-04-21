"""
Framework integration for running tests with various test frameworks.

Supports pytest, Jest, JUnit, Go testing, and more.
"""

from typing import List, Dict, Optional, Any, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import subprocess
import json
import re


@dataclass
class TestResult:
    """Result of a test execution."""
    test_name: str
    passed: bool
    duration: float = 0.0
    error_message: str = ""
    stack_trace: str = ""
    line_number: Optional[int] = None
    file: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Result of running a complete test suite."""
    framework: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get all failed tests."""
        return [r for r in self.results if not r.passed]
    
    def get_passed_tests(self) -> List[TestResult]:
        """Get all passed tests."""
        return [r for r in self.results if r.passed]


class TestRunner(ABC):
    """Abstract base class for test runners."""
    
    @abstractmethod
    def run(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        """Run tests and return results."""
        pass
    
    @abstractmethod
    def get_framework_name(self) -> str:
        """Get the framework name."""
        pass
    
    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        """Parse test output into TestSuiteResult."""
        pass


class PyTestRunner(TestRunner):
    """Test runner for pytest."""
    
    def get_framework_name(self) -> str:
        return "pytest"
    
    def run(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        cmd = ["python", "-m", "pytest", "-v", "--tb=short", "--json-report", "--json-report-file=pytest_report.json"]
        cmd.extend([str(f) for f in test_files])
        
        if additional_args:
            cmd.extend(additional_args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return self.parse_output(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr="Test execution timed out",
            )
        except Exception as e:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr=str(e),
            )
    
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        """Parse pytest output."""
        suite_result = TestSuiteResult(framework=self.get_framework_name())
        
        # Try to load JSON report
        try:
            with open("pytest_report.json") as f:
                report = json.load(f)
                suite_result.total_tests = report.get("summary", {}).get("total", 0)
                suite_result.passed_tests = report.get("summary", {}).get("passed", 0)
                suite_result.failed_tests = report.get("summary", {}).get("failed", 0)
                suite_result.skipped_tests = report.get("summary", {}).get("skipped", 0)
        except:
            # Parse text output
            pass
        
        # Parse text output
        passed_pattern = re.compile(r'PASSED\s+(.+?)\s+')
        failed_pattern = re.compile(r'FAILED\s+(.+?)\s+')
        skipped_pattern = re.compile(r'SKIPPED\s+(.+?)\s+')
        
        for match in passed_pattern.finditer(stdout):
            suite_result.results.append(TestResult(
                test_name=match.group(1).strip(),
                passed=True,
            ))
            suite_result.passed_tests += 1
        
        for match in failed_pattern.finditer(stdout):
            suite_result.results.append(TestResult(
                test_name=match.group(1).strip(),
                passed=False,
            ))
            suite_result.failed_tests += 1
        
        for match in skipped_pattern.finditer(stdout):
            suite_result.results.append(TestResult(
                test_name=match.group(1).strip(),
                passed=True,  # Skipped tests pass
            ))
            suite_result.skipped_tests += 1
        
        suite_result.total_tests = (
            suite_result.passed_tests +
            suite_result.failed_tests +
            suite_result.skipped_tests
        )
        
        suite_result.stdout = stdout
        suite_result.stderr = stderr
        
        return suite_result


class JestRunner(TestRunner):
    """Test runner for Jest."""
    
    def get_framework_name(self) -> str:
        return "jest"
    
    def run(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        cmd = ["npx", "jest", "--json", "--verbose"]
        cmd.extend([str(f) for f in test_files])
        
        if additional_args:
            cmd.extend(additional_args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return self.parse_output(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr="Test execution timed out",
            )
        except Exception as e:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr=str(e),
            )
    
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        """Parse Jest JSON output."""
        suite_result = TestSuiteResult(framework=self.get_framework_name())
        
        try:
            # Try to parse JSON from stdout
            data = json.loads(stdout)
            
            if "testResults" in data:
                for test_file in data["testResults"]:
                    for assertion in test_file.get("assertionResults", []):
                        status = assertion.get("status", "")
                        test_result = TestResult(
                            test_name=assertion.get("title", ""),
                            passed=status == "passed",
                            error_message=assertion.get("failureMessages", [""])[0] if assertion.get("failureMessages") else "",
                        )
                        suite_result.results.append(test_result)
                        
                        if status == "passed":
                            suite_result.passed_tests += 1
                        elif status == "failed":
                            suite_result.failed_tests += 1
                        elif status == "pending":
                            suite_result.skipped_tests += 1
            
            suite_result.total_tests = data.get("numTotalTests", len(suite_result.results))
            
        except json.JSONDecodeError:
            # Fall back to text parsing
            pass
        
        suite_result.stdout = stdout
        suite_result.stderr = stderr
        
        return suite_result


class JUnitRunner(TestRunner):
    """Test runner for JUnit (via Maven or Gradle)."""
    
    def __init__(self, build_tool: str = "maven"):
        self.build_tool = build_tool
    
    def get_framework_name(self) -> str:
        return "junit"
    
    def run(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        if self.build_tool == "maven":
            cmd = ["mvn", "test", "-Dtest=" + ",".join(f.stem for f in test_files)]
        else:
            cmd = ["./gradlew", "test", "--tests=" + " --tests=".join(str(f) for f in test_files)]
        
        if additional_args:
            cmd.extend(additional_args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return self.parse_output(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr="Test execution timed out",
            )
        except Exception as e:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr=str(e),
            )
    
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        """Parse JUnit output."""
        suite_result = TestSuiteResult(framework=self.get_framework_name())
        
        # Parse test results from Maven output
        passed_pattern = re.compile(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)')
        
        for match in passed_pattern.finditer(stdout):
            suite_result.total_tests = int(match.group(1))
            suite_result.failed_tests = int(match.group(2))
            suite_result.skipped_tests = int(match.group(4))
            suite_result.passed_tests = (
                suite_result.total_tests -
                suite_result.failed_tests -
                suite_result.skipped_tests
            )
        
        # Try to parse XML reports
        xml_pattern = re.compile(r'Testsuite.*?tests="(\d+)" failures="(\d+)"')
        for match in xml_pattern.finditer(stdout):
            suite_result.total_tests = int(match.group(1))
            suite_result.failed_tests = int(match.group(2))
        
        suite_result.stdout = stdout
        suite_result.stderr = stderr
        
        return suite_result


class GoTestRunner(TestRunner):
    """Test runner for Go tests."""
    
    def get_framework_name(self) -> str:
        return "go"
    
    def run(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        cmd = ["go", "test", "-v", "-json"]
        
        if test_files:
            # Run tests for specific files
            for tf in test_files:
                if tf.suffix == ".go":
                    cmd.append(f"./{tf.parent}")
                    break
        
        if additional_args:
            cmd.extend(additional_args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return self.parse_output(result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr="Test execution timed out",
            )
        except Exception as e:
            return TestSuiteResult(
                framework=self.get_framework_name(),
                stderr=str(e),
            )
    
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        """Parse Go test JSON output."""
        suite_result = TestSuiteResult(framework=self.get_framework_name())
        
        for line in stdout.split("\n"):
            try:
                data = json.loads(line)
                if data.get("Action") == "pass":
                    suite_result.results.append(TestResult(
                        test_name=data.get("Test", ""),
                        passed=True,
                    ))
                    suite_result.passed_tests += 1
                elif data.get("Action") == "fail":
                    suite_result.results.append(TestResult(
                        test_name=data.get("Test", ""),
                        passed=False,
                        error_message=data.get("Output", [""])[-1] if data.get("Output") else "",
                    ))
                    suite_result.failed_tests += 1
                elif data.get("Action") == "skip":
                    suite_result.skipped_tests += 1
            except json.JSONDecodeError:
                continue
        
        suite_result.total_tests = (
            suite_result.passed_tests +
            suite_result.failed_tests +
            suite_result.skipped_tests
        )
        
        suite_result.stdout = stdout
        suite_result.stderr = stderr
        
        return suite_result


class FrameworkIntegration:
    """
    Integration layer for various test frameworks.
    
    Provides unified interface for running tests across different
    frameworks and extracting results.
    """
    
    RUNNERS = {
        "pytest": PyTestRunner,
        "jest": JestRunner,
        "junit": JUnitRunner,
        "go": GoTestRunner,
    }
    
    def __init__(self, framework: str, config: Optional[Dict[str, Any]] = None):
        self.framework = framework.lower()
        self.config = config or {}
        self._runner: Optional[TestRunner] = None
        
        self._initialize_runner()
    
    def _initialize_runner(self) -> None:
        """Initialize the appropriate test runner."""
        if self.framework in self.RUNNERS:
            runner_class = self.RUNNERS[self.framework]
            if self.framework == "junit":
                build_tool = self.config.get("build_tool", "maven")
                self._runner = runner_class(build_tool)
            else:
                self._runner = runner_class()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")
    
    def run_tests(
        self,
        test_files: List[Path],
        additional_args: Optional[List[str]] = None,
    ) -> TestSuiteResult:
        """Run tests and return results."""
        if not self._runner:
            raise RuntimeError("No test runner initialized")
        
        return self._runner.run(test_files, additional_args)
    
    def run_specific_tests(
        self,
        test_names: List[str],
        test_files: List[Path],
    ) -> TestSuiteResult:
        """Run specific tests by name."""
        if not self._runner:
            raise RuntimeError("No test runner initialized")
        
        # Build filter arguments
        filter_args = []
        for name in test_names:
            filter_args.extend(["-k", name])
        
        return self._runner.run(test_files, filter_args)
    
    def detect_framework(self, project_path: Path) -> Optional[str]:
        """
        Detect test framework from project structure.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Detected framework name or None
        """
        # Check for framework indicators
        indicators = {
            "pytest": ["pytest.ini", "pyproject.toml", "setup.py", "conftest.py"],
            "jest": ["package.json", "jest.config.js", "jest.config.ts"],
            "junit": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "go": ["go.mod", "go.sum"],
        }
        
        for framework, files in indicators.items():
            for f in files:
                if (project_path / f).exists():
                    return framework
        
        return None
    
    @classmethod
    def create_from_project(cls, project_path: Path) -> "FrameworkIntegration":
        """Create integration from project directory."""
        project_path = Path(project_path)
        
        # Try to detect framework
        framework = None
        
        # Check for pytest
        if (project_path / "pytest.ini").exists() or (project_path / "pyproject.toml").exists():
            framework = "pytest"
        # Check for Jest
        elif (project_path / "package.json").exists():
            framework = "jest"
        # Check for JUnit
        elif (project_path / "pom.xml").exists() or (project_path / "build.gradle").exists():
            framework = "junit"
        # Check for Go
        elif (project_path / "go.mod").exists():
            framework = "go"
        
        if framework:
            return cls(framework)
        
        raise ValueError("Could not detect test framework")
