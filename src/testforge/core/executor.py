"""
Mutation executor - runs tests against mutated code.
"""

import subprocess
import time
import json
import tempfile
import os
import signal
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
import hashlib

from .mutation import Mutation, MutationResult, MutationStatus, MutationSession


@dataclass
class ExecutionConfig:
    """Configuration for mutation execution."""
    timeout: float = 30.0  # Timeout per mutation in seconds
    max_retries: int = 2
    parallel_workers: int = 4
    test_framework: str = "pytest"  # pytest, jest, junit, go
    test_command: str = ""
    test_args: List[str] = field(default_factory=list)
    coverage_command: Optional[str] = None
    working_directory: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    capture_output: bool = True
    stop_on_first_kill: bool = False  # Stop once mutation is killed


class MutationExecutor:
    """
    Executes tests against mutated code and tracks results.
    
    Supports parallel execution, timeouts, and multiple test frameworks.
    """
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self._temp_dir = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
    
    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp(prefix="testforge_")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=False)
    
    def execute_mutation(
        self,
        mutation: Mutation,
        source_code: str,
        test_files: List[Path],
    ) -> MutationResult:
        """
        Execute tests against a single mutation.
        
        Args:
            mutation: The mutation to test
            source_code: Original source code
            test_files: List of test file paths
            
        Returns:
            MutationResult with execution details
        """
        mutated_code = self._apply_mutation(source_code, mutation)
        
        # Write mutated file to temp location
        mutated_path = Path(self._temp_dir) / f"mutated_{mutation.id}.py"
        with open(mutated_path, "w") as f:
            f.write(mutated_code)
        
        # Copy original file path for import resolution
        original_path = mutation.source_file
        backup_path = Path(self._temp_dir) / f"original_{mutation.id}.py"
        
        try:
            # Backup and replace original file
            with open(original_path, "r") as f:
                original_content = f.read()
            
            with open(original_path, "w") as f:
                f.write(mutated_code)
            
            # Run tests
            start_time = time.time()
            result = self._run_tests(mutation, test_files)
            result.execution_time = time.time() - start_time
            
            # Restore original file
            with open(original_path, "w") as f:
                f.write(original_content)
            
            return result
            
        except Exception as e:
            # Ensure original is restored
            try:
                with open(original_path, "w") as f:
                    f.write(original_content)
            except:
                pass
            
            return MutationResult(
                mutation=mutation,
                status=MutationStatus.ERROR,
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
            )
        finally:
            # Cleanup temp files
            if mutated_path.exists():
                mutated_path.unlink()
            if backup_path.exists():
                backup_path.unlink()
    
    def execute_mutations_parallel(
        self,
        mutations: List[Mutation],
        source_code: str,
        test_files: List[Path],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[MutationResult]:
        """
        Execute tests against multiple mutations in parallel.
        
        Args:
            mutations: List of mutations to test
            source_code: Original source code
            test_files: List of test file paths
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of MutationResults
        """
        results = []
        completed = 0
        total = len(mutations)
        
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures = {
                executor.submit(
                    self.execute_mutation,
                    mutation,
                    source_code,
                    test_files,
                ): mutation
                for mutation in mutations
            }
            
            for future in as_completed(futures):
                mutation = futures[future]
                try:
                    result = future.result(timeout=self.config.timeout * 2)
                    results.append(result)
                except Exception as e:
                    results.append(MutationResult(
                        mutation=mutation,
                        status=MutationStatus.ERROR,
                        error_message=f"Execution failed: {str(e)}",
                        timestamp=datetime.now().isoformat(),
                    ))
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        
        return results
    
    def execute_mutations_batch(
        self,
        mutations: List[Mutation],
        source_code: str,
        test_files: List[Path],
        batch_size: int = 10,
    ) -> List[MutationResult]:
        """
        Execute mutations in batches.
        
        Useful for resource-constrained environments.
        """
        results = []
        for i in range(0, len(mutations), batch_size):
            batch = mutations[i : i + batch_size]
            batch_results = self.execute_mutations_parallel(
                batch, source_code, test_files
            )
            results.extend(batch_results)
        return results
    
    def _apply_mutation(self, source_code: str, mutation: Mutation) -> str:
        """Apply a mutation to source code."""
        lines = source_code.split("\n")
        if 0 <= mutation.line_number - 1 < len(lines):
            line = lines[mutation.line_number - 1]
            # Find and replace the original code
            if mutation.original_code in line:
                lines[mutation.line_number - 1] = line.replace(
                    mutation.original_code,
                    mutation.mutated_code,
                    1,
                )
        return "\n".join(lines)
    
    def _run_tests(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run tests against mutated code."""
        framework = self.config.test_framework.lower()
        
        if framework == "pytest":
            return self._run_pytest(mutation, test_files)
        elif framework == "jest":
            return self._run_jest(mutation, test_files)
        elif framework == "junit":
            return self._run_junit(mutation, test_files)
        elif framework == "go":
            return self._run_go_tests(mutation, test_files)
        else:
            return self._run_generic_tests(mutation, test_files)
    
    def _run_pytest(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run pytest tests."""
        cmd = [
            "python", "-m", "pytest",
            "-v", "--tb=short",
            "--no-header",
        ]
        
        # Add coverage if configured
        if self.config.coverage_command:
            cmd = self.config.coverage_command.split() + cmd
        
        cmd.extend([str(f) for f in test_files])
        cmd.extend(self.config.test_args)
        
        return self._execute_command(cmd, mutation)
    
    def _run_jest(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run Jest tests."""
        cmd = ["npx", "jest", "--verbose"]
        cmd.extend([str(f) for f in test_files])
        cmd.extend(self.config.test_args)
        
        return self._execute_command(cmd, mutation)
    
    def _run_junit(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run JUnit tests."""
        cmd = [
            "mvn", "test",
            f"-Dtest={','.join(f.stem for f in test_files)}",
        ]
        cmd.extend(self.config.test_args)
        
        return self._execute_command(cmd, mutation)
    
    def _run_go_tests(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run Go tests."""
        cmd = ["go", "test", "-v"]
        cmd.extend([f"./{f.parent.relative_to(Path.cwd())}" if f.suffix == ".go" else str(f) for f in test_files])
        cmd.extend(self.config.test_args)
        
        return self._execute_command(cmd, mutation)
    
    def _run_generic_tests(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> MutationResult:
        """Run tests using custom command."""
        if not self.config.test_command:
            return MutationResult(
                mutation=mutation,
                status=MutationStatus.SKIPPED,
                error_message="No test command configured",
                timestamp=datetime.now().isoformat(),
            )
        
        cmd = self.config.test_command.split()
        cmd.extend([str(f) for f in test_files])
        cmd.extend(self.config.test_args)
        
        return self._execute_command(cmd, mutation)
    
    def _execute_command(
        self,
        cmd: List[str],
        mutation: Mutation,
    ) -> MutationResult:
        """Execute a test command with timeout and capture output."""
        start_time = time.time()
        stdout = ""
        stderr = ""
        return_code = -1
        
        try:
            env = os.environ.copy()
            env.update(self.config.env_vars)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if self.config.capture_output else None,
                stderr=subprocess.PIPE if self.config.capture_output else None,
                cwd=self.config.working_directory or Path.cwd(),
                env=env,
                text=True,
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.config.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return MutationResult(
                    mutation=mutation,
                    status=MutationStatus.TIMEOUT,
                    test_cases_run=0,
                    execution_time=self.config.timeout,
                    stdout=stdout or "",
                    stderr=f"Test execution timed out after {self.config.timeout}s",
                    timestamp=datetime.now().isoformat(),
                )
            
        except FileNotFoundError:
            return MutationResult(
                mutation=mutation,
                status=MutationStatus.ERROR,
                error_message=f"Command not found: {cmd[0]}",
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            return MutationResult(
                mutation=mutation,
                status=MutationStatus.ERROR,
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
            )
        
        execution_time = time.time() - start_time
        
        # Parse test results based on framework
        killing_tests, tests_passed, tests_failed = self._parse_test_output(
            stdout, stderr, return_code
        )
        
        # Determine status
        if return_code == 0:
            status = MutationStatus.SURVIVED
        else:
            status = MutationStatus.KILLED
        
        return MutationResult(
            mutation=mutation,
            status=status,
            test_cases_run=tests_passed + tests_failed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            killing_tests=killing_tests,
            execution_time=execution_time,
            stdout=stdout or "",
            stderr=stderr or "",
            timestamp=datetime.now().isoformat(),
        )
    
    def _parse_test_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
    ) -> Tuple[List[str], int, int]:
        """
        Parse test output to extract test results.
        
        Returns:
            Tuple of (killing_test_names, tests_passed, tests_failed)
        """
        killing_tests = []
        tests_passed = 0
        tests_failed = 0
        
        combined_output = (stdout or "") + (stderr or "")
        
        # Pytest parsing
        if self.config.test_framework == "pytest":
            import re
            
            # Find passed tests
            passed_matches = re.findall(r"PASSED\s+(?:.*?::)?(\S+)", stdout)
            tests_passed = len(passed_matches)
            
            # Find failed tests
            failed_matches = re.findall(r"FAILED\s+(?:.*?::)?(\S+)", stdout)
            tests_failed = len(failed_matches)
            killing_tests = failed_matches
            
            # Check for coverage info
            coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", combined_output)
        
        # Jest parsing
        elif self.config.test_framework == "jest":
            import re
            
            # Find test results
            pass_match = re.search(r"Tests:\s+(\d+)\s+passed", stdout)
            fail_match = re.search(r"Tests:\s+.*?(\d+)\s+failed", stdout)
            
            if pass_match:
                tests_passed = int(pass_match.group(1))
            if fail_match:
                tests_failed = int(fail_match.group(1))
            
            # Find failing test names
            fail_name_matches = re.findall(r"FAIL\s+(?:.*?::)?(\S+)", stdout)
            killing_tests = fail_name_matches
        
        # Generic fallback
        else:
            if return_code == 0:
                tests_passed = 1
            else:
                tests_failed = 1
                killing_tests = ["generic_test"]
        
        return killing_tests, tests_passed, tests_failed


class ParallelMutationExecutor(MutationExecutor):
    """
    Enhanced executor with advanced parallelization.
    
    Supports process-based parallelization for CPU-bound workloads
    and intelligent work distribution.
    """
    
    def __init__(self, config: ExecutionConfig):
        super().__init__(config)
        self._results_cache: Dict[str, MutationResult] = {}
    
    def execute_mutations_smart(
        self,
        mutations: List[Mutation],
        source_code: str,
        test_files: List[Path],
        coverage_data: Optional[Dict[str, Set[int]]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[MutationResult]:
        """
        Smart parallel execution with optimizations.
        
        Uses coverage data to skip mutations in uncovered code,
        caches results for duplicate mutations, and distributes
        work intelligently based on estimated execution time.
        """
        # Filter by coverage if available
        if coverage_data:
            mutations = self._filter_by_coverage(mutations, coverage_data)
        
        # Check cache for duplicate mutations
        uncached_mutations = []
        cached_results = []
        
        for mutation in mutations:
            cache_key = self._get_cache_key(mutation)
            if cache_key in self._results_cache:
                cached_results.append(self._results_cache[cache_key])
            else:
                uncached_mutations.append(mutation)
        
        # Execute uncached mutations
        new_results = self.execute_mutations_parallel(
            uncached_mutations,
            source_code,
            test_files,
            progress_callback,
        )
        
        # Cache new results
        for result in new_results:
            cache_key = self._get_cache_key(result.mutation)
            self._results_cache[cache_key] = result
        
        # Combine and return
        return cached_results + new_results
    
    def _filter_by_coverage(
        self,
        mutations: List[Mutation],
        coverage_data: Dict[str, Set[int]],
    ) -> List[Mutation]:
        """Filter mutations to only those in covered code."""
        file_key = str(mutations[0].source_file) if mutations else ""
        covered_lines = coverage_data.get(file_key, set())
        
        return [
            m for m in mutations
            if m.line_number in covered_lines
        ]
    
    def _get_cache_key(self, mutation: Mutation) -> str:
        """Generate cache key for a mutation."""
        return hashlib.md5(
            f"{mutation.source_file}:{mutation.line_number}:"
            f"{mutation.original_code}:{mutation.mutated_code}".encode()
        ).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._results_cache)
        killed = sum(1 for r in self._results_cache.values() if r.is_killed())
        survived = total - killed
        
        return {
            "total_cached": total,
            "killed": killed,
            "survived": survived,
            "hit_rate": 0.0,  # Would need tracking of cache hits
        }
