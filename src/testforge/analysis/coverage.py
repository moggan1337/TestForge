"""
Coverage analysis for mutation testing.

Analyzes code coverage to guide mutation selection and provide
insights into test effectiveness.
"""

from typing import List, Dict, Optional, Set, Tuple, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import json
import subprocess
import re


@dataclass
class CoverageData:
    """Coverage information for source files."""
    files: Dict[str, "FileCoverage"] = field(default_factory=dict)
    total_lines: int = 0
    covered_lines: int = 0
    total_branches: int = 0
    covered_branches: int = 0
    
    def get_coverage_percentage(self) -> float:
        """Get overall line coverage percentage."""
        if self.total_lines == 0:
            return 0.0
        return (self.covered_lines / self.total_lines) * 100
    
    def get_branch_coverage_percentage(self) -> float:
        """Get overall branch coverage percentage."""
        if self.total_branches == 0:
            return 0.0
        return (self.covered_branches / self.total_branches) * 100
    
    def get_covered_lines(self, file_path: str) -> Set[int]:
        """Get set of covered line numbers for a file."""
        if file_path in self.files:
            return self.files[file_path].covered_lines
        return set()
    
    def is_line_covered(self, file_path: str, line_number: int) -> bool:
        """Check if a specific line is covered."""
        return line_number in self.get_covered_lines(file_path)


@dataclass
class FileCoverage:
    """Coverage information for a single file."""
    path: str
    total_lines: int = 0
    covered_lines: Set[int] = field(default_factory=set)
    uncovered_lines: Set[int] = field(default_factory=set)
    branch_coverage: Dict[int, Dict[str, bool]] = field(default_factory=dict)
    
    def get_coverage_percentage(self) -> float:
        """Get coverage percentage for this file."""
        if self.total_lines == 0:
            return 0.0
        return (len(self.covered_lines) / self.total_lines) * 100


class CoverageAnalyzer:
    """
    Analyzes code coverage data to guide mutation testing.
    
    Supports multiple coverage formats and provides utilities
    for coverage-guided mutation selection.
    """
    
    def __init__(self, coverage_command: Optional[str] = None):
        self.coverage_command = coverage_command
        self._cache: Dict[str, CoverageData] = {}
    
    def run_coverage(
        self,
        test_command: str,
        source_files: List[Path],
        output_format: str = "json",
    ) -> CoverageData:
        """
        Run tests with coverage collection.
        
        Args:
            test_command: Command to run tests (e.g., "pytest")
            source_files: List of source files to track
            output_format: Coverage output format
            
        Returns:
            CoverageData with coverage information
        """
        # Build coverage command
        cmd = self._build_coverage_command(test_command, output_format)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if output_format == "json":
                return self._parse_coverage_json(result.stdout, source_files)
            elif output_format == "cobertura":
                return self._parse_cobertura_xml(result.stdout, source_files)
            else:
                return self._parse_generic_coverage(result.stdout, source_files)
                
        except subprocess.TimeoutExpired:
            raise TimeoutError("Coverage collection timed out")
        except Exception as e:
            raise RuntimeError(f"Coverage collection failed: {e}")
    
    def load_coverage_file(self, coverage_file: Path) -> CoverageData:
        """
        Load coverage data from a file.
        
        Supports JSON, Cobertura XML, and LCOV formats.
        """
        with open(coverage_file) as f:
            content = f.read()
        
        suffix = coverage_file.suffix.lower()
        if suffix == ".json":
            return self._parse_coverage_json(content, [])
        elif suffix in [".xml", ".cobertura"]:
            return self._parse_cobertura_xml(content, [])
        elif suffix in [".lcov", ".info"]:
            return self._parse_lcov(content, [])
        else:
            raise ValueError(f"Unknown coverage format: {suffix}")
    
    def _build_coverage_command(
        self,
        test_command: str,
        output_format: str,
    ) -> List[str]:
        """Build coverage command based on test framework."""
        # Common coverage tools
        coverage_tools = {
            "pytest": ["pytest", "--cov=.", "--cov-report=", "term-missing"],
            "jest": ["jest", "--coverage"],
            "go": ["go", "test", "-coverprofile=coverage.out"],
            "cargo": ["cargo", "test", "--coverage"],
            "maven": ["mvn", "test", "jacoco:report"],
        }
        
        # Parse test command
        parts = test_command.split()
        if not parts:
            raise ValueError("Empty test command")
        
        framework = parts[0]
        
        if framework in coverage_tools:
            return coverage_tools[framework]
        else:
            return parts
    
    def _parse_coverage_json(
        self,
        content: str,
        source_files: List[Path],
    ) -> CoverageData:
        """Parse coverage data from JSON format."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return CoverageData()
        
        coverage = CoverageData()
        
        # Handle coverage.py format
        if "files" in data:
            for file_path, file_data in data["files"].items():
                file_cov = FileCoverage(
                    path=file_path,
                    total_lines=file_data.get("totals", {}).get("num_statements", 0),
                )
                
                # Parse line coverage
                if "executed_lines" in file_data:
                    file_cov.covered_lines = set(file_data["executed_lines"])
                if "missing_lines" in file_data:
                    file_cov.uncovered_lines = set(file_data["missing_lines"])
                
                coverage.files[file_path] = file_cov
                
                coverage.total_lines += file_cov.total_lines
                coverage.covered_lines += len(file_cov.covered_lines)
        
        # Handle other JSON formats (Codecov, etc.)
        elif isinstance(data, dict):
            for file_path, file_data in data.items():
                if isinstance(file_data, dict):
                    file_cov = FileCoverage(path=file_path)
                    
                    if "coverage" in file_data:
                        lines = file_data["coverage"]
                        for i, covered in enumerate(lines):
                            if covered is not None and covered > 0:
                                file_cov.covered_lines.add(i + 1)
                            else:
                                file_cov.uncovered_lines.add(i + 1)
                            file_cov.total_lines = len(lines)
                    
                    coverage.files[file_path] = file_cov
                    coverage.total_lines += file_cov.total_lines
                    coverage.covered_lines += len(file_cov.covered_lines)
        
        return coverage
    
    def _parse_cobertura_xml(
        self,
        content: str,
        source_files: List[Path],
    ) -> CoverageData:
        """Parse coverage data from Cobertura XML format."""
        coverage = CoverageData()
        
        # Simple XML parsing for coverage data
        line_pattern = re.compile(r'<line number="(\d+)" hits="(\d+)"')
        class_pattern = re.compile(r'<class name="([^"]+)" filename="([^"]+)"')
        
        current_file = None
        for line in content.split("\n"):
            class_match = class_pattern.search(line)
            if class_match:
                current_file = class_match.group(2)
                if current_file not in coverage.files:
                    coverage.files[current_file] = FileCoverage(path=current_file)
            
            line_match = line_pattern.search(line)
            if line_match and current_file:
                line_num = int(line_match.group(1))
                hits = int(line_match.group(2))
                
                if hits > 0:
                    coverage.files[current_file].covered_lines.add(line_num)
                else:
                    coverage.files[current_file].uncovered_lines.add(line_num)
                
                coverage.files[current_file].total_lines += 1
        
        # Calculate totals
        for file_cov in coverage.files.values():
            coverage.total_lines += file_cov.total_lines
            coverage.covered_lines += len(file_cov.covered_lines)
        
        return coverage
    
    def _parse_lcov(
        self,
        content: str,
        source_files: List[Path],
    ) -> CoverageData:
        """Parse coverage data from LCOV format."""
        coverage = CoverageData()
        
        current_file = None
        line_pattern = re.compile(r'^DA:(\d+),(\d+)')
        
        for line in content.split("\n"):
            if line.startswith("SF:"):
                current_file = line[3:]
                if current_file not in coverage.files:
                    coverage.files[current_file] = FileCoverage(path=current_file)
            
            elif line.startswith("DA:") and current_file:
                match = line_pattern.match(line)
                if match:
                    line_num = int(match.group(1))
                    hits = int(match.group(2))
                    
                    if hits > 0:
                        coverage.files[current_file].covered_lines.add(line_num)
                    else:
                        coverage.files[current_file].uncovered_lines.add(line_num)
            
            elif line.startswith("LH:") and current_file:
                coverage.files[current_file].covered_lines = set()
            elif line.startswith("LF:") and current_file:
                coverage.files[current_file].total_lines = int(line[3:])
        
        # Calculate totals
        for file_cov in coverage.files.values():
            coverage.total_lines += file_cov.total_lines
            coverage.covered_lines += len(file_cov.covered_lines)
        
        return coverage
    
    def _parse_generic_coverage(
        self,
        content: str,
        source_files: List[Path],
    ) -> CoverageData:
        """Parse generic coverage output."""
        coverage = CoverageData()
        
        # Try to extract line numbers from various formats
        line_pattern = re.compile(r':(\d+):.*(?:covered|hit|executed)')
        
        for line_num in line_pattern.findall(content):
            for source_file in source_files:
                file_key = str(source_file)
                if file_key not in coverage.files:
                    coverage.files[file_key] = FileCoverage(path=file_key)
                coverage.files[file_key].covered_lines.add(int(line_num))
                coverage.total_lines += 1
                coverage.covered_lines += 1
        
        return coverage
    
    def get_coverage_for_mutations(
        self,
        mutations: List[Any],
        coverage_data: CoverageData,
    ) -> List[Tuple[Any, bool]]:
        """
        Determine which mutations are covered by tests.
        
        Returns list of (mutation, is_covered) tuples.
        """
        results = []
        
        for mutation in mutations:
            file_path = str(mutation.source_file)
            is_covered = coverage_data.is_line_covered(
                file_path, mutation.line_number
            )
            results.append((mutation, is_covered))
        
        return results
    
    def filter_covered_mutations(
        self,
        mutations: List[Any],
        coverage_data: CoverageData,
    ) -> List[Any]:
        """Filter mutations to only those in covered code."""
        covered = []
        
        for mutation in mutations:
            file_path = str(mutation.source_file)
            if coverage_data.is_line_covered(file_path, mutation.line_number):
                covered.append(mutation)
        
        return covered
    
    def get_uncovered_areas(
        self,
        coverage_data: CoverageData,
        source_dir: Path,
    ) -> List[Dict[str, Any]]:
        """
        Identify areas of code with no coverage.
        
        Useful for prioritizing test development.
        """
        uncovered_areas = []
        
        for file_path, file_cov in coverage_data.files.items():
            if len(file_cov.covered_lines) == 0 and file_cov.total_lines > 0:
                uncovered_areas.append({
                    "file": file_path,
                    "reason": "completely_uncovered",
                    "lines": file_cov.total_lines,
                })
            elif file_cov.uncovered_lines:
                # Find contiguous uncovered regions
                regions = self._find_uncovered_regions(
                    file_cov.uncovered_lines
                )
                for start, end in regions:
                    uncovered_areas.append({
                        "file": file_path,
                        "start_line": start,
                        "end_line": end,
                        "uncovered_lines": end - start + 1,
                    })
        
        return uncovered_areas
    
    def _find_uncovered_regions(
        self,
        uncovered_lines: Set[int],
    ) -> List[Tuple[int, int]]:
        """Find contiguous regions of uncovered lines."""
        if not uncovered_lines:
            return []
        
        sorted_lines = sorted(uncovered_lines)
        regions = []
        start = end = sorted_lines[0]
        
        for line in sorted_lines[1:]:
            if line == end + 1:
                end = line
            else:
                regions.append((start, end))
                start = end = line
        
        regions.append((start, end))
        return regions
    
    def generate_coverage_report(
        self,
        coverage_data: CoverageData,
        output_path: Path,
    ) -> None:
        """Generate a coverage report file."""
        report = {
            "summary": {
                "total_lines": coverage_data.total_lines,
                "covered_lines": coverage_data.covered_lines,
                "coverage_percentage": coverage_data.get_coverage_percentage(),
                "total_branches": coverage_data.total_branches,
                "covered_branches": coverage_data.covered_branches,
                "branch_coverage_percentage": coverage_data.get_branch_coverage_percentage(),
            },
            "files": {
                path: {
                    "total_lines": fc.total_lines,
                    "covered_lines": len(fc.covered_lines),
                    "coverage_percentage": fc.get_coverage_percentage(),
                    "covered_line_numbers": sorted(list(fc.covered_lines)),
                    "uncovered_line_numbers": sorted(list(fc.uncovered_lines)),
                }
                for path, fc in coverage_data.files.items()
            },
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
