"""
Tests for EffectivenessScorer.
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
from testforge.core.scorer import (
    EffectivenessScorer,
    ScoreGrade,
    ScoreComponents,
)


class TestEffectivenessScorer:
    """Tests for EffectivenessScorer class."""

    def test_create_scorer_with_defaults(self):
        """Test creating scorer with default values."""
        scorer = EffectivenessScorer()
        
        assert scorer.mutation_threshold == 0.8
        assert scorer.coverage_weight == 0.2
        assert scorer.time_weight == 0.1

    def test_create_scorer_with_custom_values(self):
        """Test creating scorer with custom values."""
        scorer = EffectivenessScorer(
            mutation_threshold=0.9,
            coverage_weight=0.3,
            time_weight=0.05,
        )
        
        assert scorer.mutation_threshold == 0.9
        assert scorer.coverage_weight == 0.3
        assert scorer.time_weight == 0.05

    def test_compute_score_with_empty_results(self):
        """Test computing score with no results."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        score, grade, components = scorer.compute_score(session)
        
        assert score == 0.0
        assert grade == ScoreGrade.POOR

    def test_compute_score_with_all_killed(self):
        """Test computing score when all mutations are killed."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        for i in range(5):
            mutation = Mutation(
                id=f"all-killed-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            result = MutationResult(
                mutation=mutation,
                status=MutationStatus.KILLED,
                test_cases_run=10,
                killing_tests=[f"test_{i}"],
            )
            session.add_result(result)
        
        score, grade, components = scorer.compute_score(session)
        
        # With all mutations killed, we expect a high score
        assert components.base_score == 100.0
        assert score >= 50.0  # Should be reasonably high

    def test_compute_score_with_survived_mutations(self):
        """Test computing score with surviving mutations."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        # 3 killed, 2 survived
        for i in range(5):
            mutation = Mutation(
                id=f"partial-kill-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            status = MutationStatus.KILLED if i < 3 else MutationStatus.SURVIVED
            result = MutationResult(
                mutation=mutation,
                status=status,
                test_cases_run=5,
                killing_tests=[f"test_{i}"] if status == MutationStatus.KILLED else [],
            )
            session.add_result(result)
        
        score, grade, components = scorer.compute_score(session)
        
        # Base score should be 60% (3 out of 5 killed)
        assert components.base_score == 60.0

    def test_score_to_grade_excellent(self):
        """Test excellent grade threshold."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(95.0) == ScoreGrade.EXCELLENT
        assert scorer._score_to_grade(90.0) == ScoreGrade.EXCELLENT

    def test_score_to_grade_good(self):
        """Test good grade threshold."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(85.0) == ScoreGrade.GOOD
        assert scorer._score_to_grade(80.0) == ScoreGrade.GOOD

    def test_score_to_grade_acceptable(self):
        """Test acceptable grade threshold."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(75.0) == ScoreGrade.ACCEPTABLE
        assert scorer._score_to_grade(70.0) == ScoreGrade.ACCEPTABLE

    def test_score_to_grade_needs_improvement(self):
        """Test needs improvement grade threshold."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(60.0) == ScoreGrade.NEEDS_IMPROVEMENT
        assert scorer._score_to_grade(50.0) == ScoreGrade.NEEDS_IMPROVEMENT

    def test_score_to_grade_poor(self):
        """Test poor grade threshold."""
        scorer = EffectivenessScorer()
        
        assert scorer._score_to_grade(40.0) == ScoreGrade.POOR
        assert scorer._score_to_grade(0.0) == ScoreGrade.POOR

    def test_compute_test_effectiveness(self):
        """Test computing test effectiveness."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        # Create mutations
        for i in range(4):
            mutation = Mutation(
                id=f"test-eff-{i}",
                operator_type=OperatorType.ROR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="==",
                mutated_code="!=",
            )
            session.add_mutation(mutation)
        
        # Test kills 3 of 4 mutations
        for i in range(3):
            mutation_id = f"test-eff-{i}"
            for m in session.mutations:
                if m.id == mutation_id:
                    result = MutationResult(
                        mutation=m,
                        status=MutationStatus.KILLED,
                        killing_tests=["test_under_review"],
                    )
                    session.add_result(result)
                    break
        
        # Add one surviving mutation
        for m in session.mutations:
            if m.id == "test-eff-3":
                result = MutationResult(
                    mutation=m,
                    status=MutationStatus.SURVIVED,
                    killing_tests=[],
                )
                session.add_result(result)
                break
        
        metrics = scorer.compute_test_effectiveness("test_under_review", session)
        
        assert metrics["test_name"] == "test_under_review"
        assert metrics["mutations_killed"] == 3
        assert metrics["total_mutations"] == 4
        assert metrics["coverage_percentage"] == 75.0

    def test_rank_tests(self):
        """Test ranking tests by effectiveness."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        # Create mutations
        for i in range(6):
            mutation = Mutation(
                id=f"rank-{i}",
                operator_type=OperatorType.AOR,
                source_file=Path("test.py"),
                line_number=i,
                original_code="+",
                mutated_code="-",
            )
            session.add_mutation(mutation)
        
        # test_a kills 4 mutations
        for m in session.mutations[:4]:
            result = MutationResult(
                mutation=m,
                status=MutationStatus.KILLED,
                killing_tests=["test_a"],
            )
            session.add_result(result)
        
        # test_b kills 2 mutations
        for m in session.mutations[4:6]:
            result = MutationResult(
                mutation=m,
                status=MutationStatus.KILLED,
                killing_tests=["test_b"],
            )
            session.add_result(result)
        
        rankings = scorer.rank_tests(session)
        
        assert len(rankings) == 2
        assert rankings[0]["test_name"] == "test_a"
        assert rankings[0]["killing_power"] >= rankings[1]["killing_power"]

    def test_compute_coverage_metrics(self):
        """Test computing coverage metrics."""
        scorer = EffectivenessScorer()
        session = MutationSession(Path("/project"))
        
        mutations = []
        for i, op_type in enumerate([OperatorType.AOR, OperatorType.ROR, OperatorType.LOR]):
            mutation = Mutation(
                id=f"cov-{i}",
                operator_type=op_type,
                source_file=Path("test.py"),
                line_number=i * 10,
                original_code="test",
                mutated_code="mutated",
            )
            mutations.append(mutation)
            session.add_mutation(mutation)
            status = MutationStatus.KILLED if i < 2 else MutationStatus.SURVIVED
            result = MutationResult(
                mutation=mutation,
                status=status,
                killing_tests=["test"] if status == MutationStatus.KILLED else [],
            )
            session.add_result(result)
        
        metrics = scorer.compute_coverage_metrics(session)
        
        assert "lines" in metrics
        assert "operators" in metrics
        assert metrics["operators"]["total"] == 3
        assert metrics["operators"]["killed"] == 2


class TestScoreGrade:
    """Tests for ScoreGrade enum."""

    def test_score_grade_values(self):
        """Test ScoreGrade enum values."""
        assert ScoreGrade.EXCELLENT.value == "A"
        assert ScoreGrade.GOOD.value == "B"
        assert ScoreGrade.ACCEPTABLE.value == "C"
        assert ScoreGrade.NEEDS_IMPROVEMENT.value == "D"
        assert ScoreGrade.POOR.value == "F"

    def test_score_grade_count(self):
        """Test number of score grades."""
        assert len(ScoreGrade) == 5
