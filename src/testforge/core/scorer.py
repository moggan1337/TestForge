"""
Effectiveness scoring for mutation testing.
"""

from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

from .mutation import Mutation, MutationResult, MutationStatus, KillMatrix, MutationSession


class ScoreGrade(Enum):
    """Grade for mutation score."""
    EXCELLENT = "A"
    GOOD = "B"
    ACCEPTABLE = "C"
    NEEDS_IMPROVEMENT = "D"
    POOR = "F"


@dataclass
class ScoreComponents:
    """Individual score components."""
    base_score: float = 0.0
    coverage_bonus: float = 0.0
    operator_penalty: float = 0.0
    time_penalty: float = 0.0
    redundancy_penalty: float = 0.0
    final_score: float = 0.0


class EffectivenessScorer:
    """
    Computes effectiveness scores for test suites using mutation testing.
    
    Provides multiple scoring methodologies and detailed breakdowns
    of test suite quality.
    """
    
    def __init__(
        self,
        mutation_threshold: float = 0.8,
        coverage_weight: float = 0.2,
        time_weight: float = 0.1,
    ):
        self.mutation_threshold = mutation_threshold
        self.coverage_weight = coverage_weight
        self.time_weight = time_weight
    
    def compute_score(
        self,
        session: MutationSession,
    ) -> Tuple[float, ScoreGrade, ScoreComponents]:
        """
        Compute overall effectiveness score.
        
        Args:
            session: Mutation testing session with results
            
        Returns:
            Tuple of (score, grade, components)
        """
        components = ScoreComponents()
        
        # Base mutation score
        components.base_score = self._compute_mutation_score(session)
        
        # Coverage bonus
        components.coverage_bonus = self._compute_coverage_bonus(session)
        
        # Operator consistency penalty
        components.operator_penalty = self._compute_operator_penalty(session)
        
        # Time efficiency penalty
        components.time_penalty = self._compute_time_penalty(session)
        
        # Redundancy penalty
        components.redundancy_penalty = self._compute_redundancy_penalty(session)
        
        # Calculate final score
        components.final_score = (
            components.base_score * 0.6 +
            components.coverage_bonus * self.coverage_weight +
            components.operator_penalty * 0.1 -
            components.time_penalty * self.time_weight -
            components.redundancy_penalty * 0.1
        )
        
        # Clamp score to 0-100
        components.final_score = max(0.0, min(100.0, components.final_score))
        
        grade = self._score_to_grade(components.final_score)
        
        return components.final_score, grade, components
    
    def _compute_mutation_score(self, session: MutationSession) -> float:
        """Compute basic mutation kill percentage."""
        results = session.results
        if not results:
            return 0.0
        
        killed = sum(1 for r in results if r.is_killed())
        total = len(results)
        
        return (killed / total * 100) if total > 0 else 0.0
    
    def _compute_coverage_bonus(self, session: MutationSession) -> float:
        """Compute bonus for covering mutations in different areas."""
        kill_matrix = session.kill_matrix
        
        # Calculate coverage diversity
        unique_files = len(set(r.mutation.source_file for r in session.results))
        total_mutations = len(session.results)
        
        if total_mutations == 0:
            return 0.0
        
        # Higher bonus for covering diverse files
        file_diversity = unique_files / max(1, total_mutations / 10)
        
        # Calculate line diversity
        unique_lines = len(set(r.mutation.line_number for r in session.results))
        line_diversity = unique_lines / max(1, total_mutations / 5)
        
        return min(10, (file_diversity + line_diversity) * 2)
    
    def _compute_operator_penalty(self, session: MutationSession) -> float:
        """
        Compute penalty for inconsistent operator kill rates.
        
        High consistency across operators is desirable.
        """
        if not session.results:
            return 0.0
        
        # Group by operator
        operator_kills = {}
        for result in session.results:
            op = result.mutation.operator_type.value
            if op not in operator_kills:
                operator_kills[op] = {"killed": 0, "total": 0}
            
            operator_kills[op]["total"] += 1
            if result.is_killed():
                operator_kills[op]["killed"] += 1
        
        # Calculate kill rates per operator
        kill_rates = []
        for op, stats in operator_kills.items():
            if stats["total"] > 0:
                rate = stats["killed"] / stats["total"]
                kill_rates.append(rate)
        
        if len(kill_rates) < 2:
            return 0.0
        
        # Penalize high variance
        variance = statistics.variance(kill_rates)
        return min(10, variance * 50)
    
    def _compute_time_penalty(self, session: MutationSession) -> float:
        """Compute penalty for slow test execution."""
        results = session.results
        if not results:
            return 0.0
        
        times = [r.execution_time for r in results if r.execution_time > 0]
        if not times:
            return 0.0
        
        # Penalize high variance and slow average
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        
        # Normalize penalties
        time_penalty = 0.0
        
        if avg_time > 10:  # Average > 10 seconds per mutation
            time_penalty += min(5, (avg_time - 10) / 2)
        
        if std_time > avg_time:  # High variance
            time_penalty += min(5, (std_time - avg_time) / 5)
        
        return time_penalty
    
    def _compute_redundancy_penalty(self, session: MutationSession) -> float:
        """
        Compute penalty for redundant killing.
        
        Tests that kill the same mutations are somewhat redundant.
        """
        kill_matrix = session.kill_matrix
        
        if not kill_matrix.mutations or not kill_matrix.tests:
            return 0.0
        
        # Count unique mutation sets per test
        test_mutation_sets = {}
        for test in kill_matrix.tests:
            mutations_killed = set()
            for mutation in kill_matrix.mutations:
                if kill_matrix.did_kill(mutation.id, test):
                    mutations_killed.add(mutation.id)
            test_mutation_sets[test] = mutations_killed
        
        # Calculate redundancy
        if len(test_mutation_sets) < 2:
            return 0.0
        
        # Find overlap between tests
        total_overlap = 0
        tests = list(test_mutation_sets.keys())
        
        for i, test1 in enumerate(tests):
            for test2 in tests[i + 1:]:
                set1 = test_mutation_sets[test1]
                set2 = test_mutation_sets[test2]
                if set1 and set2:
                    intersection = len(set1 & set2)
                    union = len(set1 | set2)
                    if union > 0:
                        total_overlap += intersection / union
        
        # Normalize
        num_pairs = len(tests) * (len(tests) - 1) / 2
        avg_overlap = total_overlap / num_pairs if num_pairs > 0 else 0
        
        return min(10, avg_overlap * 15)
    
    def _score_to_grade(self, score: float) -> ScoreGrade:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return ScoreGrade.EXCELLENT
        elif score >= 80:
            return ScoreGrade.GOOD
        elif score >= 70:
            return ScoreGrade.ACCEPTABLE
        elif score >= 50:
            return ScoreGrade.NEEDS_IMPROVEMENT
        else:
            return ScoreGrade.POOR
    
    def compute_test_effectiveness(
        self,
        test_name: str,
        session: MutationSession,
    ) -> Dict[str, Any]:
        """
        Compute effectiveness metrics for a specific test.
        
        Returns detailed metrics about how well a test kills mutations.
        """
        kill_matrix = session.kill_matrix
        
        mutations_killed = 0
        total_mutations = len(session.mutations)
        killing_power = 0.0
        
        for mutation in session.mutations:
            if kill_matrix.did_kill(mutation.id, test_name):
                mutations_killed += 1
                killing_power += 1 / len(kill_matrix.get_killing_tests(mutation.id))
        
        coverage = (mutations_killed / total_mutations * 100) if total_mutations > 0 else 0
        
        return {
            "test_name": test_name,
            "mutations_killed": mutations_killed,
            "total_mutations": total_mutations,
            "coverage_percentage": coverage,
            "killing_power": killing_power,
            "unique_kills": mutations_killed - self._count_duplicate_kills(test_name, session),
        }
    
    def _count_duplicate_kills(
        self,
        test_name: str,
        session: MutationSession,
    ) -> int:
        """Count how many kills were also done by other tests."""
        kill_matrix = session.kill_matrix
        
        duplicate_kills = 0
        for mutation in session.mutations:
            killing_tests = kill_matrix.get_killing_tests(mutation.id)
            if test_name in killing_tests and len(killing_tests) > 1:
                duplicate_kills += 1
        
        return duplicate_kills
    
    def rank_tests(
        self,
        session: MutationSession,
    ) -> List[Dict[str, Any]]:
        """
        Rank tests by their effectiveness.
        
        Returns sorted list of tests with their metrics.
        """
        test_metrics = []
        
        for test in session.kill_matrix.tests:
            metrics = self.compute_test_effectiveness(test, session)
            test_metrics.append(metrics)
        
        # Sort by killing power
        test_metrics.sort(key=lambda x: x["killing_power"], reverse=True)
        
        return test_metrics
    
    def compute_coverage_metrics(
        self,
        session: MutationSession,
    ) -> Dict[str, Any]:
        """
        Compute coverage metrics for the mutation session.
        """
        results = session.results
        
        if not results:
            return {}
        
        # Line coverage
        lines_tested = set()
        lines_killed = set()
        
        for result in results:
            line = (str(result.mutation.source_file), result.mutation.line_number)
            lines_tested.add(line)
            if result.is_killed():
                lines_killed.add(line)
        
        # Operator coverage
        operators_tested = set(m.operator_type for m in session.mutations)
        operators_killed = set(
            m.operator_type for m in session.mutations
            if any(r.is_killed() for r in results if r.mutation.id == m.id)
        )
        
        return {
            "lines": {
                "total": len(lines_tested),
                "killed": len(lines_killed),
                "survived": len(lines_tested - lines_killed),
                "kill_percentage": len(lines_killed) / len(lines_tested) * 100 if lines_tested else 0,
            },
            "operators": {
                "total": len(operators_tested),
                "killed": len(operators_killed),
                "survived": len(operators_tested - operators_killed),
                "kill_percentage": len(operators_killed) / len(operators_tested) * 100 if operators_tested else 0,
            },
        }


@dataclass
class MutationScoreReport:
    """Detailed report of mutation testing score."""
    overall_score: float
    grade: ScoreGrade
    components: ScoreComponents
    test_rankings: List[Dict[str, Any]]
    coverage_metrics: Dict[str, Any]
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "components": {
                "base_score": self.components.base_score,
                "coverage_bonus": self.components.coverage_bonus,
                "operator_penalty": self.components.operator_penalty,
                "time_penalty": self.components.time_penalty,
                "redundancy_penalty": self.components.redundancy_penalty,
                "final_score": self.components.final_score,
            },
            "test_rankings": self.test_rankings,
            "coverage_metrics": self.coverage_metrics,
            "timestamp": self.timestamp,
        }
    
    def print_report(self) -> str:
        """Generate human-readable report."""
        lines = [
            "=" * 60,
            "MUTATION TESTING EFFECTIVENESS REPORT",
            "=" * 60,
            "",
            f"Overall Score: {self.overall_score:.2f}%",
            f"Grade: {self.grade.value}",
            "",
            "Score Components:",
            f"  Base Score: {self.components.base_score:.2f}",
            f"  Coverage Bonus: +{self.components.coverage_bonus:.2f}",
            f"  Operator Penalty: -{self.components.operator_penalty:.2f}",
            f"  Time Penalty: -{self.components.time_penalty:.2f}",
            f"  Redundancy Penalty: -{self.components.redundancy_penalty:.2f}",
            "",
            "Top 5 Most Effective Tests:",
        ]
        
        for i, test in enumerate(self.test_rankings[:5], 1):
            lines.append(
                f"  {i}. {test['test_name']}: "
                f"{test['killing_power']:.2f} power, "
                f"{test['coverage_percentage']:.1f}% coverage"
            )
        
        if self.coverage_metrics:
            lines.extend([
                "",
                "Coverage Metrics:",
                f"  Lines killed: {self.coverage_metrics['lines']['kill_percentage']:.1f}%",
                f"  Operators killed: {self.coverage_metrics['operators']['kill_percentage']:.1f}%",
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
