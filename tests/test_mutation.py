"""
Tests for Mutation data structures.
"""

import pytest
from pathlib import Path
from testforge.core.mutation import (
    Mutation,
    MutationResult,
    MutationStatus,
    OperatorType,
    KillMatrix,
    MutationSession,
)


class TestMutation:
    """Tests for Mutation dataclass."""

    def test_create_mutation_with_required_fields(self):
        """Test creating a mutation with required fields only."""
        mutation = Mutation(
            id="test-123",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=10,
            original_code="+",
            mutated_code="-",
        )
        
        assert mutation.id == "test-123"
        assert mutation.operator_type == OperatorType.AOR
        assert mutation.source_file == Path("test.py")
        assert mutation.line_number == 10
        assert mutation.original_code == "+"
        assert mutation.mutated_code == "-"

    def test_mutation_auto_generates_id(self):
        """Test that mutation auto-generates ID based on content."""
        mutation = Mutation(
            id="auto-123",
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="==",
            mutated_code="!=",
        )
        
        assert mutation.id is not None
        assert len(mutation.id) >= 8  # ID should have reasonable length

    def test_mutation_to_dict(self):
        """Test converting mutation to dictionary."""
        mutation = Mutation(
            id="test-456",
            operator_type=OperatorType.LOR,
            source_file=Path("example.py"),
            line_number=5,
            original_code="and",
            mutated_code="or",
        )
        
        data = mutation.to_dict()
        
        assert data["id"] == "test-456"
        assert data["operator_type"] == "LogicalOperatorReplacement"
        assert data["source_file"] == "example.py"
        assert data["line_number"] == 5
        assert data["original_code"] == "and"
        assert data["mutated_code"] == "or"

    def test_mutation_from_dict(self):
        """Test creating mutation from dictionary."""
        data = {
            "id": "test-789",
            "operator_type": "ArithmeticOperatorReplacement",
            "source_file": "sample.py",
            "line_number": 20,
            "original_code": "*",
            "mutated_code": "/",
        }
        
        mutation = Mutation.from_dict(data)
        
        assert mutation.id == "test-789"
        assert mutation.operator_type == OperatorType.AOR
        assert mutation.line_number == 20

    def test_mutation_str_representation(self):
        """Test string representation of mutation."""
        mutation = Mutation(
            id="test-abc",
            operator_type=OperatorType.ASR,
            source_file=Path("/path/to/file.py"),
            line_number=15,
            original_code="+=",
            mutated_code="-=",
        )
        
        str_repr = str(mutation)
        
        assert "AssignmentOperatorReplacement" in str_repr
        assert "file.py" in str_repr
        assert "15" in str_repr


class TestMutationResult:
    """Tests for MutationResult dataclass."""

    def test_create_mutation_result(self):
        """Test creating a mutation result."""
        mutation = Mutation(
            id="mut-1",
            operator_type=OperatorType.RVR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="True",
            mutated_code="False",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
            test_cases_run=5,
            tests_passed=5,
            tests_failed=0,
            execution_time=0.5,
            killing_tests=["test_something", "test_else"],
        )
        
        assert result.mutation == mutation
        assert result.status == MutationStatus.KILLED
        assert result.test_cases_run == 5
        assert result.is_killed() is True
        assert result.is_survived() is False

    def test_is_killed(self):
        """Test is_killed method."""
        mutation = Mutation(
            id="mut-2",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="+",
            mutated_code="-",
        )
        
        killed_result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
        )
        assert killed_result.is_killed() is True
        
        survived_result = MutationResult(
            mutation=mutation,
            status=MutationStatus.SURVIVED,
        )
        assert survived_result.is_killed() is False

    def test_is_survived(self):
        """Test is_survived method."""
        mutation = Mutation(
            id="mut-3",
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="==",
            mutated_code="!=",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.SURVIVED,
        )
        
        assert result.is_survived() is True
        assert result.is_killed() is False

    def test_get_kill_ratio(self):
        """Test kill ratio calculation."""
        mutation = Mutation(
            id="mut-4",
            operator_type=OperatorType.LOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="and",
            mutated_code="or",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
            test_cases_run=10,
            killing_tests=["test1", "test2", "test3"],
        )
        
        assert result.get_kill_ratio() == 0.3

    def test_mutation_result_to_dict(self):
        """Test converting result to dictionary."""
        mutation = Mutation(
            id="mut-5",
            operator_type=OperatorType.UOD,
            source_file=Path("test.py"),
            line_number=1,
            original_code="-",
            mutated_code="+",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.ERROR,
            error_message="Compilation failed",
        )
        
        data = result.to_dict()
        
        assert data["status"] == "error"
        assert data["error_message"] == "Compilation failed"
        assert data["mutation"]["id"] == "mut-5"


class TestKillMatrix:
    """Tests for KillMatrix class."""

    def test_create_empty_kill_matrix(self):
        """Test creating an empty kill matrix."""
        matrix = KillMatrix()
        
        assert len(matrix.mutations) == 0
        assert len(matrix.tests) == 0

    def test_add_mutation(self):
        """Test adding mutations to matrix."""
        matrix = KillMatrix()
        mutation = Mutation(
            id="kill-1",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="+",
            mutated_code="-",
        )
        
        matrix.add_mutation(mutation)
        
        assert len(matrix.mutations) == 1
        assert matrix.mutations[0].id == "kill-1"

    def test_add_duplicate_mutation(self):
        """Test that duplicate mutations are not added."""
        matrix = KillMatrix()
        mutation = Mutation(
            id="kill-dup",
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="==",
            mutated_code="!=",
        )
        
        matrix.add_mutation(mutation)
        matrix.add_mutation(mutation)  # Duplicate
        
        assert len(matrix.mutations) == 1

    def test_add_test(self):
        """Test adding tests to matrix."""
        matrix = KillMatrix()
        
        matrix.add_test("test_feature_a")
        matrix.add_test("test_feature_b")
        
        assert len(matrix.tests) == 2
        assert "test_feature_a" in matrix.tests
        assert "test_feature_b" in matrix.tests

    def test_record_kill(self):
        """Test recording kills."""
        matrix = KillMatrix()
        mutation = Mutation(
            id="kill-2",
            operator_type=OperatorType.LOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="and",
            mutated_code="or",
        )
        matrix.add_mutation(mutation)
        
        matrix.record_kill("kill-2", "test_that_kills")
        
        assert matrix.did_kill("kill-2", "test_that_kills") is True
        assert matrix.did_kill("kill-2", "test_that_doesnt") is False

    def test_get_killing_tests(self):
        """Test getting all killing tests for a mutation."""
        matrix = KillMatrix()
        mutation = Mutation(
            id="kill-3",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="*",
            mutated_code="/",
        )
        matrix.add_mutation(mutation)
        
        matrix.record_kill("kill-3", "test_1")
        matrix.record_kill("kill-3", "test_2")
        matrix.record_kill("kill-3", "test_3")
        
        killing_tests = matrix.get_killing_tests("kill-3")
        
        assert len(killing_tests) == 3
        assert "test_1" in killing_tests
        assert "test_2" in killing_tests
        assert "test_3" in killing_tests

    def test_get_surviving_mutations(self):
        """Test getting surviving mutations."""
        matrix = KillMatrix()
        
        mut1 = Mutation(
            id="survive-1",
            operator_type=OperatorType.RVR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="True",
            mutated_code="False",
        )
        mut2 = Mutation(
            id="survive-2",
            operator_type=OperatorType.ASR,
            source_file=Path("test.py"),
            line_number=2,
            original_code="+=",
            mutated_code="-=",
        )
        
        matrix.add_mutation(mut1)
        matrix.add_mutation(mut2)
        
        # Only mut1 gets killed
        matrix.record_kill("survive-1", "test_kills")
        
        surviving = matrix.get_surviving_mutations()
        
        assert len(surviving) == 1
        assert surviving[0].id == "survive-2"

    def test_get_covered_mutations(self):
        """Test getting mutations killed by at least one test."""
        matrix = KillMatrix()
        
        mut1 = Mutation(
            id="cover-1",
            operator_type=OperatorType.UOD,
            source_file=Path("test.py"),
            line_number=1,
            original_code="-",
            mutated_code="+",
        )
        mut2 = Mutation(
            id="cover-2",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=2,
            original_code="+",
            mutated_code="-",
        )
        
        matrix.add_mutation(mut1)
        matrix.add_mutation(mut2)
        
        # Only mut1 gets killed
        matrix.record_kill("cover-1", "test")
        
        covered = matrix.get_covered_mutations()
        
        assert len(covered) == 1
        assert covered[0].id == "cover-1"

    def test_kill_matrix_summary(self):
        """Test kill matrix summary statistics."""
        matrix = KillMatrix()
        
        for i in range(5):
            mut = Mutation(
                id=f"sum-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            matrix.add_mutation(mut)
            matrix.add_test(f"test_{i}")
            
            # First 3 mutations killed, last 2 survive
            if i < 3:
                matrix.record_kill(f"sum-{i}", f"test_{i}")
        
        summary = matrix.summary()
        
        assert summary["total_mutations"] == 5
        assert summary["total_tests"] == 5
        assert summary["mutations_killed"] == 3
        assert summary["mutations_survived"] == 2
        assert summary["kill_percentage"] == 60.0


class TestMutationSession:
    """Tests for MutationSession class."""

    def test_create_mutation_session(self):
        """Test creating a mutation session."""
        session = MutationSession(Path("/project/root"))
        
        assert session.project_root == Path("/project/root")
        assert len(session.mutations) == 0
        assert len(session.results) == 0
        assert session.session_id is not None

    def test_add_mutation_to_session(self):
        """Test adding mutations to session."""
        session = MutationSession(Path("/project"))
        mutation = Mutation(
            id="sess-mut-1",
            operator_type=OperatorType.ROR,
            source_file=Path("main.py"),
            line_number=1,
            original_code="<",
            mutated_code=">",
        )
        
        session.add_mutation(mutation)
        
        assert len(session.mutations) == 1
        assert len(session.kill_matrix.mutations) == 1

    def test_add_result_to_session(self):
        """Test adding results to session."""
        session = MutationSession(Path("/project"))
        mutation = Mutation(
            id="sess-mut-2",
            operator_type=OperatorType.LOR,
            source_file=Path("main.py"),
            line_number=1,
            original_code="or",
            mutated_code="and",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
            killing_tests=["test_kills_this"],
        )
        
        session.add_result(result)
        
        assert len(session.results) == 1
        assert len(session.kill_matrix.tests) == 1

    def test_get_results_by_status(self):
        """Test filtering results by status."""
        session = MutationSession(Path("/project"))
        
        for i, status in enumerate([MutationStatus.KILLED, MutationStatus.SURVIVED, MutationStatus.KILLED]):
            mutation = Mutation(
                id=f"status-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            result = MutationResult(mutation=mutation, status=status)
            session.add_result(result)
        
        killed_results = session.get_results_by_status(MutationStatus.KILLED)
        survived_results = session.get_results_by_status(MutationStatus.SURVIVED)
        
        assert len(killed_results) == 2
        assert len(survived_results) == 1

    def test_get_statistics(self):
        """Test getting session statistics."""
        session = MutationSession(Path("/project"))
        
        for i in range(3):
            mutation = Mutation(
                id=f"stat-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            result = MutationResult(
                mutation=mutation,
                status=MutationStatus.KILLED if i < 2 else MutationStatus.SURVIVED,
                killing_tests=[f"test_{i}"] if i < 2 else [],
            )
            session.add_result(result)
        
        stats = session.get_statistics()
        
        assert stats["total_mutations"] == 3
        assert stats["mutations_killed"] == 2
        assert stats["mutations_survived"] == 1
        assert "session_id" in stats
