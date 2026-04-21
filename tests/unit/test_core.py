"""Unit tests for TestForge core components."""

import pytest
from pathlib import Path
from testforge.core.mutation import (
    Mutation,
    MutationResult,
    MutationStatus,
    KillMatrix,
    MutationSession,
    OperatorType,
)
from testforge.core.mutator import Mutator, MutationStrategy
from testforge.core.scorer import EffectivenessScorer, ScoreGrade
from testforge.core.analyzer import MutationAnalyzer


class TestMutation:
    """Tests for Mutation class."""
    
    def test_mutation_creation(self):
        """Test basic mutation creation."""
        mutation = Mutation(
            id="test123",
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=10,
            original_code="+",
            mutated_code="-",
        )
        
        assert mutation.id == "test123"
        assert mutation.operator_type == OperatorType.AOR
        assert mutation.line_number == 10
        assert mutation.original_code == "+"
        assert mutation.mutated_code == "-"
    
    def test_mutation_auto_id(self):
        """Test automatic ID generation."""
        mutation = Mutation(
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=5,
            original_code="==",
            mutated_code="!=",
        )
        
        assert mutation.id is not None
        assert len(mutation.id) > 0
    
    def test_mutation_to_dict(self):
        """Test mutation serialization."""
        mutation = Mutation(
            id="test456",
            operator_type=OperatorType.LOR,
            source_file=Path("example.py"),
            line_number=20,
            original_code="and",
            mutated_code="or",
        )
        
        data = mutation.to_dict()
        
        assert data["id"] == "test456"
        assert data["operator_type"] == "LogicalOperatorReplacement"
        assert data["line_number"] == 20
    
    def test_mutation_from_dict(self):
        """Test mutation deserialization."""
        data = {
            "id": "test789",
            "operator_type": "ArithmeticOperatorReplacement",
            "source_file": "test.py",
            "line_number": 15,
            "original_code": "*",
            "mutated_code": "/",
        }
        
        mutation = Mutation.from_dict(data)
        
        assert mutation.id == "test789"
        assert mutation.operator_type == OperatorType.AOR
        assert mutation.original_code == "*"


class TestMutationResult:
    """Tests for MutationResult class."""
    
    def test_result_creation(self):
        """Test result creation."""
        mutation = Mutation(
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="+",
            mutated_code="-",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
            test_cases_run=10,
            tests_passed=8,
            tests_failed=2,
        )
        
        assert result.is_killed()
        assert result.test_cases_run == 10
        assert result.tests_failed == 2
    
    def test_survived_result(self):
        """Test survived mutation result."""
        mutation = Mutation(
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=5,
            original_code=">",
            mutated_code="<",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.SURVIVED,
            test_cases_run=5,
            tests_passed=5,
            tests_failed=0,
        )
        
        assert result.is_survived()
        assert not result.is_killed()
    
    def test_kill_ratio(self):
        """Test kill ratio calculation."""
        mutation = Mutation(
            operator_type=OperatorType.LOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="and",
            mutated_code="or",
        )
        
        result = MutationResult(
            mutation=mutation,
            status=MutationStatus.KILLED,
            test_cases_run=4,
            tests_passed=2,
            tests_failed=2,
            killing_tests=["test_a", "test_b"],
        )
        
        assert result.get_kill_ratio() == 0.5


class TestKillMatrix:
    """Tests for KillMatrix class."""
    
    def test_matrix_creation(self):
        """Test matrix creation."""
        matrix = KillMatrix()
        
        assert len(matrix.mutations) == 0
        assert len(matrix.tests) == 0
    
    def test_add_mutation(self):
        """Test adding mutations to matrix."""
        matrix = KillMatrix()
        mutation = Mutation(
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="+",
            mutated_code="-",
        )
        
        matrix.add_mutation(mutation)
        
        assert len(matrix.mutations) == 1
        assert matrix.mutations[0] == mutation
    
    def test_record_kill(self):
        """Test recording a kill."""
        matrix = KillMatrix()
        mutation = Mutation(
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="==",
            mutated_code="!=",
        )
        
        matrix.add_mutation(mutation)
        matrix.add_test("test_add")
        matrix.record_kill(mutation.id, "test_add")
        
        assert matrix.did_kill(mutation.id, "test_add")
        assert not matrix.did_kill(mutation.id, "test_other")
    
    def test_get_surviving_mutations(self):
        """Test getting surviving mutations."""
        matrix = KillMatrix()
        
        mut1 = Mutation(
            operator_type=OperatorType.AOR,
            source_file=Path("test.py"),
            line_number=1,
            original_code="+",
            mutated_code="-",
        )
        mut2 = Mutation(
            operator_type=OperatorType.ROR,
            source_file=Path("test.py"),
            line_number=2,
            original_code="==",
            mutated_code="!=",
        )
        
        matrix.add_mutation(mut1)
        matrix.add_mutation(mut2)
        matrix.add_test("test_a")
        matrix.record_kill(mut1.id, "test_a")
        
        survivors = matrix.get_surviving_mutations()
        
        assert len(survivors) == 1
        assert survivors[0].id == mut2.id
    
    def test_summary(self):
        """Test matrix summary."""
        matrix = KillMatrix()
        
        for i in range(5):
            mutation = Mutation(
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i + 1,
                original_code="+",
                mutated_code="-",
            )
            matrix.add_mutation(mutation)
        
        matrix.add_test("test_a")
        matrix.record_kill(matrix.mutations[0].id, "test_a")
        matrix.record_kill(matrix.mutations[1].id, "test_a")
        
        summary = matrix.summary()
        
        assert summary["total_mutations"] == 5
        assert summary["mutations_killed"] == 2
        assert summary["mutations_survived"] == 3
        assert summary["kill_percentage"] == 40.0


class TestMutator:
    """Tests for Mutator class."""
    
    def test_mutator_creation(self):
        """Test mutator creation."""
        mutator = Mutator(
            source_file=Path("test.py"),
            operators=[OperatorType.AOR, OperatorType.ROR],
        )
        
        assert mutator.source_file == Path("test.py")
        assert OperatorType.AOR in mutator.operators
        assert OperatorType.ROR in mutator.operators
    
    def test_language_detection(self):
        """Test language detection."""
        mutator_py = Mutator(Path("test.py"))
        mutator_js = Mutator(Path("test.js"))
        mutator_ts = Mutator(Path("test.ts"))
        
        assert mutator_py._language == "python"
        assert mutator_js._language == "javascript"
        assert mutator_ts._language == "typescript"
    
    def test_load_source(self):
        """Test loading source code."""
        mutator = Mutator(Path("test.py"))
        # Note: This requires an actual file to work
        # For unit testing, we'd mock this


class TestEffectivenessScorer:
    """Tests for EffectivenessScorer class."""
    
    def test_score_grade_conversion(self):
        """Test score to grade conversion."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(95) == ScoreGrade.EXCELLENT
        assert scorer._score_to_grade(85) == ScoreGrade.GOOD
        assert scorer._score_to_grade(75) == ScoreGrade.ACCEPTABLE
        assert scorer._score_to_grade(55) == ScoreGrade.NEEDS_IMPROVEMENT
        assert scorer._score_to_grade(30) == ScoreGrade.POOR


class TestMutationAnalyzer:
    """Tests for MutationAnalyzer class."""
    
    def test_analyzer_creation(self):
        """Test analyzer creation."""
        analyzer = MutationAnalyzer()
        
        assert analyzer.config is not None
    
    def test_compute_summary_empty(self):
        """Test summary computation with empty session."""
        analyzer = MutationAnalyzer()
        session = MutationSession(Path.cwd())
        
        summary = analyzer._compute_summary(session)
        
        assert summary == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
