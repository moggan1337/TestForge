"""
Mutation data structures and types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set, Any
from pathlib import Path
import hashlib
import json


class MutationStatus(Enum):
    """Status of a mutation during testing."""
    CREATED = "created"
    COMPILED = "compiled"
    RUNNING = "running"
    KILLED = "killed"
    SURVIVED = "survived"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


class OperatorType(Enum):
    """Types of mutation operators."""
    # Arithmetic Operators
    AOR = "ArithmeticOperatorReplacement"  # +, -, *, /, %, //
    # Logical Operators
    LOR = "LogicalOperatorReplacement"  # and, or, not
    # Relational Operators
    ROR = "RelationalOperatorReplacement"  # <, <=, >, >=, ==, !=
    # Assignment Operators
    ASR = "AssignmentOperatorReplacement"  # =, +=, -=, *=, /=
    # Conditional Operators
    CRP = "ConditionalReplacement"  # if/else swaps
    # Loop Operators
    LVR = "LoopVariableReplacement"
    # Return Operators
    RVR = "ReturnValueReplacement"
    # Declaration Operators
    DOR = "DeclarationOperatorReplacement"
    # Unary Operators
    UOD = "UnaryOperatorDeletion"
    # Statement Operators
    SOD = "StatementOperatorDeletion"
    # Array Operators
    AORS = "ArrayOperatorReplacement"
    # String Operators
    SVR = "StringValueReplacement"
    # Null Operators
    NVR = "NullValueReplacement"
    # Exception Operators
    ECR = "ExceptionContextReplacement"


@dataclass
class Mutation:
    """
    Represents a single mutation applied to source code.
    
    Attributes:
        id: Unique identifier for the mutation
        operator_type: Type of mutation operator used
        source_file: Path to the source file
        line_number: Line where mutation was applied
        original_code: Original source code snippet
        mutated_code: Mutated source code snippet
        start_pos: Start position in file
        end_pos: End position in file
        context: Surrounding code context for debugging
        target_node: AST node type targeted
    """
    id: str
    operator_type: OperatorType
    source_file: Path
    line_number: int
    original_code: str
    mutated_code: str
    start_pos: int = 0
    end_pos: int = 0
    context: str = ""
    target_node: str = ""
    column: int = 0
    
    def __post_init__(self):
        if isinstance(self.source_file, str):
            self.source_file = Path(self.source_file)
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID based on mutation details."""
        content = f"{self.source_file}:{self.line_number}:{self.original_code}:{self.mutated_code}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mutation to dictionary."""
        return {
            "id": self.id,
            "operator_type": self.operator_type.value,
            "source_file": str(self.source_file),
            "line_number": self.line_number,
            "original_code": self.original_code,
            "mutated_code": self.mutated_code,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "context": self.context,
            "target_node": self.target_node,
            "column": self.column,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mutation":
        """Create mutation from dictionary."""
        return cls(
            id=data["id"],
            operator_type=OperatorType(data["operator_type"]),
            source_file=Path(data["source_file"]),
            line_number=data["line_number"],
            original_code=data["original_code"],
            mutated_code=data["mutated_code"],
            start_pos=data.get("start_pos", 0),
            end_pos=data.get("end_pos", 0),
            context=data.get("context", ""),
            target_node=data.get("target_node", ""),
            column=data.get("column", 0),
        )
    
    def __str__(self) -> str:
        return f"Mutation({self.operator_type.value}:{self.source_file.name}:{self.line_number})"


@dataclass
class MutationResult:
    """
    Result of executing tests against a mutation.
    
    Attributes:
        mutation: The mutation that was tested
        status: Final status after testing
        test_cases_run: Number of test cases executed
        tests_passed: Number of tests that passed
        tests_failed: Number of tests that failed
        execution_time: Time taken to execute
        error_message: Error message if any
        killing_tests: List of tests that killed the mutation
        stdout: Standard output from test execution
        stderr: Standard error output
        coverage_data: Coverage information
        timestamp: When the result was recorded
    """
    mutation: Mutation
    status: MutationStatus
    test_cases_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    execution_time: float = 0.0
    error_message: str = ""
    killing_tests: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    def is_killed(self) -> bool:
        """Check if mutation was killed by any test."""
        return self.status == MutationStatus.KILLED
    
    def is_survived(self) -> bool:
        """Check if mutation survived all tests."""
        return self.status == MutationStatus.SURVIVED
    
    def get_kill_ratio(self) -> float:
        """Calculate ratio of tests that killed the mutation."""
        if self.test_cases_run == 0:
            return 0.0
        return len(self.killing_tests) / self.test_cases_run
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "mutation": self.mutation.to_dict(),
            "status": self.status.value,
            "test_cases_run": self.test_cases_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "killing_tests": self.killing_tests,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "coverage_data": self.coverage_data,
            "timestamp": self.timestamp,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MutationResult":
        """Create result from dictionary."""
        return cls(
            mutation=Mutation.from_dict(data["mutation"]),
            status=MutationStatus(data["status"]),
            test_cases_run=data.get("test_cases_run", 0),
            tests_passed=data.get("tests_passed", 0),
            tests_failed=data.get("tests_failed", 0),
            execution_time=data.get("execution_time", 0.0),
            error_message=data.get("error_message", ""),
            killing_tests=data.get("killing_tests", []),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            coverage_data=data.get("coverage_data", {}),
            timestamp=data.get("timestamp", ""),
            memory_usage=data.get("memory_usage", 0.0),
            cpu_usage=data.get("cpu_usage", 0.0),
        )


@dataclass
class KillMatrix:
    """
    Matrix representing which tests kill which mutations.
    
    This is a core data structure for mutation testing analysis,
    tracking the relationship between mutations and test cases.
    """
    mutations: List[Mutation] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    kills: Dict[str, Set[str]] = field(default_factory=dict)  # mutation_id -> set of killing test names
    
    def add_mutation(self, mutation: Mutation) -> None:
        """Add a mutation to the matrix."""
        if mutation.id not in [m.id for m in self.mutations]:
            self.mutations.append(mutation)
            self.kills[mutation.id] = set()
    
    def add_test(self, test_name: str) -> None:
        """Add a test to the matrix."""
        if test_name not in self.tests:
            self.tests.append(test_name)
    
    def record_kill(self, mutation_id: str, test_name: str) -> None:
        """Record that a test killed a mutation."""
        if mutation_id not in self.kills:
            self.kills[mutation_id] = set()
        self.kills[mutation_id].add(test_name)
    
    def did_kill(self, mutation_id: str, test_name: str) -> bool:
        """Check if a test killed a specific mutation."""
        return test_name in self.kills.get(mutation_id, set())
    
    def get_killing_tests(self, mutation_id: str) -> Set[str]:
        """Get all tests that killed a specific mutation."""
        return self.kills.get(mutation_id, set())
    
    def get_mutation_kill_count(self, mutation_id: str) -> int:
        """Get number of tests that killed a mutation."""
        return len(self.kills.get(mutation_id, set()))
    
    def get_test_kill_count(self, test_name: str) -> int:
        """Get number of mutations killed by a test."""
        return sum(1 for killed in self.kills.values() if test_name in killed)
    
    def get_surviving_mutations(self) -> List[Mutation]:
        """Get all mutations that survived (not killed by any test)."""
        return [m for m in self.mutations if not self.kills.get(m.id)]
    
    def get_covered_mutations(self) -> List[Mutation]:
        """Get all mutations that were killed by at least one test."""
        return [m for m in self.mutations if self.kills.get(m.id)]
    
    def to_matrix(self) -> List[List[bool]]:
        """Convert to boolean matrix representation."""
        matrix = []
        for mutation in self.mutations:
            row = [self.did_kill(mutation.id, test) for test in self.tests]
            matrix.append(row)
        return matrix
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "mutations": [m.to_dict() for m in self.mutations],
            "tests": self.tests,
            "kills": {k: list(v) for k, v in self.kills.items()},
        }
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics of the kill matrix."""
        total_mutations = len(self.mutations)
        killed = len(self.get_covered_mutations())
        survived = len(self.get_surviving_mutations())
        
        return {
            "total_mutations": total_mutations,
            "total_tests": len(self.tests),
            "mutations_killed": killed,
            "mutations_survived": survived,
            "kill_percentage": (killed / total_mutations * 100) if total_mutations > 0 else 0,
            "average_kills_per_mutation": (
                sum(len(v) for v in self.kills.values()) / total_mutations 
                if total_mutations > 0 else 0
            ),
        }


class MutationSession:
    """
    Manages a complete mutation testing session.
    
    Tracks all mutations, results, and provides session-level operations.
    """
    
    def __init__(self, project_root: Path, config: Optional[Dict[str, Any]] = None):
        self.project_root = Path(project_root)
        self.config = config or {}
        self.mutations: List[Mutation] = []
        self.results: List[MutationResult] = []
        self.kill_matrix = KillMatrix()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.session_id = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
    
    def add_mutation(self, mutation: Mutation) -> None:
        """Add a mutation to the session."""
        self.mutations.append(mutation)
        self.kill_matrix.add_mutation(mutation)
    
    def add_result(self, result: MutationResult) -> None:
        """Add a result to the session."""
        self.results.append(result)
        for test in result.killing_tests:
            self.kill_matrix.add_test(test)
            self.kill_matrix.record_kill(result.mutation.id, test)
    
    def get_results_by_status(self, status: MutationStatus) -> List[MutationResult]:
        """Get all results with a specific status."""
        return [r for r in self.results if r.status == status]
    
    def get_surviving_mutations(self) -> List[Mutation]:
        """Get all mutations that survived testing."""
        return self.kill_matrix.get_surviving_mutations()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        kill_summary = self.kill_matrix.summary()
        
        return {
            **kill_summary,
            "session_id": self.session_id,
            "duration": self.end_time - self.start_time if self.end_time and self.start_time else None,
            "total_results": len(self.results),
            "results_by_status": {
                status.value: len(self.get_results_by_status(status))
                for status in MutationStatus
            },
            "mutations_by_operator": self._count_by_operator(),
        }
    
    def _count_by_operator(self) -> Dict[str, int]:
        """Count mutations by operator type."""
        counts = {}
        for mutation in self.mutations:
            op = mutation.operator_type.value
            counts[op] = counts.get(op, 0) + 1
        return counts
    
    def export_results(self, output_path: Path) -> None:
        """Export session results to JSON file."""
        data = {
            "session_id": self.session_id,
            "statistics": self.get_statistics(),
            "kill_matrix": self.kill_matrix.to_dict(),
            "results": [r.to_dict() for r in self.results],
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def import_results(self, input_path: Path) -> None:
        """Import session results from JSON file."""
        with open(input_path) as f:
            data = json.load(f)
        
        self.session_id = data.get("session_id", self.session_id)
        for result_data in data.get("results", []):
            self.add_result(MutationResult.from_dict(result_data))
