"""
Mutation analyzer - analyzes mutation testing results.
"""

from typing import List, Dict, Optional, Set, Tuple, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import json
import statistics

from .mutation import Mutation, MutationResult, MutationStatus, KillMatrix, MutationSession
from .scorer import EffectivenessScorer


@dataclass
class AnalysisConfig:
    """Configuration for mutation analysis."""
    confidence_level: float = 0.95
    min_sample_size: int = 30
    outlier_threshold: float = 2.0
    trend_window: int = 5
    enable_correlation: bool = True
    enable_time_analysis: bool = True


class MutationAnalyzer:
    """
    Analyzes mutation testing results to provide insights.
    
    Computes statistics, identifies patterns, and generates
    recommendations for improving test suites.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self._session: Optional[MutationSession] = None
    
    def analyze_session(self, session: MutationSession) -> "AnalysisResult":
        """Analyze a complete mutation testing session."""
        self._session = session
        
        return AnalysisResult(
            summary=self._compute_summary(session),
            operator_analysis=self._analyze_by_operator(session),
            file_analysis=self._analyze_by_file(session),
            test_analysis=self._analyze_by_test(session),
            time_analysis=self._analyze_execution_time(session) if self.config.enable_time_analysis else {},
            correlation_analysis=self._analyze_correlations(session) if self.config.enable_correlation else {},
            recommendations=self._generate_recommendations(session),
            timestamp=datetime.now().isoformat(),
        )
    
    def analyze_results(
        self,
        mutations: List[Mutation],
        results: List[MutationResult],
    ) -> "AnalysisResult":
        """Analyze mutations and their results."""
        # Build session from mutations and results
        session = MutationSession(Path.cwd())
        for mutation in mutations:
            session.add_mutation(mutation)
        for result in results:
            session.add_result(result)
        
        return self.analyze_session(session)
    
    def _compute_summary(self, session: MutationSession) -> Dict[str, Any]:
        """Compute summary statistics."""
        results = session.results
        if not results:
            return {}
        
        total = len(results)
        killed = sum(1 for r in results if r.is_killed())
        survived = sum(1 for r in results if r.is_survived())
        errors = sum(1 for r in results if r.status == MutationStatus.ERROR)
        timeouts = sum(1 for r in results if r.status == MutationStatus.TIMEOUT)
        
        # Execution time statistics
        execution_times = [r.execution_time for r in results if r.execution_time > 0]
        
        return {
            "total_mutations": total,
            "killed": killed,
            "survived": survived,
            "errors": errors,
            "timeouts": timeouts,
            "skipped": sum(1 for r in results if r.status == MutationStatus.SKIPPED),
            "kill_percentage": (killed / total * 100) if total > 0 else 0,
            "survival_rate": (survived / total * 100) if total > 0 else 0,
            "error_rate": (errors / total * 100) if total > 0 else 0,
            "average_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "median_execution_time": statistics.median(execution_times) if execution_times else 0,
            "stddev_execution_time": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "total_execution_time": sum(execution_times),
        }
    
    def _analyze_by_operator(self, session: MutationSession) -> Dict[str, Any]:
        """Analyze results grouped by mutation operator."""
        operator_stats = defaultdict(lambda: {
            "total": 0, "killed": 0, "survived": 0, "errors": 0, "times": []
        })
        
        for result in session.results:
            op = result.mutation.operator_type.value
            operator_stats[op]["total"] += 1
            operator_stats[op]["times"].append(result.execution_time)
            
            if result.is_killed():
                operator_stats[op]["killed"] += 1
            elif result.is_survived():
                operator_stats[op]["survived"] += 1
            else:
                operator_stats[op]["errors"] += 1
        
        # Compute rates and sort by kill rate
        analysis = {}
        for op, stats in operator_stats.items():
            kill_rate = (stats["killed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            analysis[op] = {
                "total": stats["total"],
                "killed": stats["killed"],
                "survived": stats["survived"],
                "errors": stats["errors"],
                "kill_rate": kill_rate,
                "avg_execution_time": statistics.mean(stats["times"]) if stats["times"] else 0,
            }
        
        return dict(sorted(analysis.items(), key=lambda x: x[1]["kill_rate"]))
    
    def _analyze_by_file(self, session: MutationSession) -> Dict[str, Any]:
        """Analyze results grouped by source file."""
        file_stats = defaultdict(lambda: {
            "total": 0, "killed": 0, "survived": 0, "lines": set()
        })
        
        for result in session.results:
            file_path = str(result.mutation.source_file)
            file_stats[file_path]["total"] += 1
            file_stats[file_path]["lines"].add(result.mutation.line_number)
            
            if result.is_killed():
                file_stats[file_path]["killed"] += 1
            elif result.is_survived():
                file_stats[file_path]["survived"] += 1
        
        analysis = {}
        for file_path, stats in file_stats.items():
            analysis[file_path] = {
                "total_mutations": stats["total"],
                "killed": stats["killed"],
                "survived": stats["survived"],
                "kill_rate": (stats["killed"] / stats["total"] * 100) if stats["total"] > 0 else 0,
                "lines_mutated": len(stats["lines"]),
            }
        
        return analysis
    
    def _analyze_by_test(self, session: MutationSession) -> Dict[str, Any]:
        """Analyze results grouped by test case."""
        test_stats = defaultdict(lambda: {
            "mutations_killed": 0, "mutations_covered": set()
        })
        
        kill_matrix = session.kill_matrix
        
        for mutation in session.mutations:
            killing_tests = kill_matrix.get_killing_tests(mutation.id)
            for test in killing_tests:
                test_stats[test]["mutations_killed"] += 1
                test_stats[test]["mutations_covered"].add(mutation.id)
        
        analysis = {}
        for test_name, stats in test_stats.items():
            analysis[test_name] = {
                "mutations_killed": stats["mutations_killed"],
                "unique_mutations": len(stats["mutations_covered"]),
            }
        
        return dict(sorted(analysis.items(), key=lambda x: x[1]["mutations_killed"], reverse=True))
    
    def _analyze_execution_time(self, session: MutationSession) -> Dict[str, Any]:
        """Analyze execution time patterns."""
        results = session.results
        times = [r.execution_time for r in results]
        
        if not times:
            return {}
        
        # Find outliers using IQR method
        sorted_times = sorted(times)
        q1 = sorted_times[len(sorted_times) // 4]
        q3 = sorted_times[3 * len(sorted_times) // 4]
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [r for r in results if r.execution_time > upper_bound]
        
        # Find slowest mutations
        slowest = sorted(results, key=lambda r: r.execution_time, reverse=True)[:5]
        
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "outlier_count": len(outliers),
            "slowest_mutations": [
                {
                    "mutation_id": m.mutation.id,
                    "file": str(m.mutation.source_file),
                    "line": m.mutation.line_number,
                    "execution_time": m.execution_time,
                }
                for m in slowest
            ],
        }
    
    def _analyze_correlations(self, session: MutationSession) -> Dict[str, Any]:
        """Analyze correlations between different factors."""
        results = session.results
        
        if len(results) < self.config.min_sample_size:
            return {"message": "Insufficient data for correlation analysis"}
        
        # Extract numeric features
        features = {
            "execution_time": [r.execution_time for r in results],
            "line_number": [r.mutation.line_number for r in results],
            "code_length": [len(r.mutation.original_code) for r in results],
            "tests_run": [r.test_cases_run for r in results],
        }
        
        # Compute correlations
        correlations = {}
        feature_names = list(features.keys())
        
        for i, name1 in enumerate(feature_names):
            for name2 in feature_names[i + 1:]:
                corr = self._compute_correlation(
                    features[name1],
                    features[name2],
                )
                correlations[f"{name1}_vs_{name2}"] = corr
        
        return {
            "correlations": correlations,
            "significant_findings": self._find_significant_correlations(correlations),
        }
    
    def _compute_correlation(
        self,
        x: List[float],
        y: List[float],
    ) -> float:
        """Compute Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
        denominator_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5
        
        if denominator_x * denominator_y == 0:
            return 0.0
        
        return numerator / (denominator_x * denominator_y)
    
    def _find_significant_correlations(self, correlations: Dict[str, float]) -> List[str]:
        """Find statistically significant correlations."""
        findings = []
        for pair, corr in correlations.items():
            abs_corr = abs(corr)
            if abs_corr > 0.5:
                direction = "positive" if corr > 0 else "negative"
                findings.append(
                    f"Strong {direction} correlation between {pair.replace('_vs_', ' and ')}: {corr:.3f}"
                )
        return findings
    
    def _generate_recommendations(self, session: MutationSession) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        summary = self._compute_summary(session)
        
        # Check overall effectiveness
        kill_pct = summary.get("kill_percentage", 0)
        if kill_pct < 50:
            recommendations.append(
                f"⚠️ Low mutation score ({kill_pct:.1f}%). "
                "Consider adding more comprehensive tests."
            )
        elif kill_pct > 90:
            recommendations.append(
                f"✅ Excellent mutation score ({kill_pct:.1f}%). "
                "Your test suite is highly effective."
            )
        
        # Check for operator-specific issues
        operator_analysis = self._analyze_by_operator(session)
        for op, stats in operator_analysis.items():
            if stats["kill_rate"] < 30 and stats["total"] >= 5:
                recommendations.append(
                    f"⚠️ {op} has low kill rate ({stats['kill_rate']:.1f}%). "
                    "Consider tests that exercise this operator more."
                )
        
        # Check for file-specific issues
        file_analysis = self._analyze_by_file(session)
        weak_files = [
            f for f, stats in file_analysis.items()
            if stats["kill_rate"] < 40 and stats["total_mutations"] >= 3
        ]
        if weak_files:
            recommendations.append(
                f"⚠️ Files with low coverage: {', '.join(weak_files[:3])}. "
                "Focus testing efforts on these areas."
            )
        
        # Check for slow tests
        if self.config.enable_time_analysis:
            time_analysis = self._analyze_execution_time(session)
            if time_analysis.get("outlier_count", 0) > len(session.results) * 0.1:
                recommendations.append(
                    "⚠️ Many slow mutations detected. "
                    "Consider optimizing test execution or increasing timeout."
                )
        
        # Check for test redundancy/inefficiency
        test_analysis = self._analyze_by_test(session)
        if test_analysis:
            max_kills = max(t["mutations_killed"] for t in test_analysis.values())
            min_kills = min(t["mutations_killed"] for t in test_analysis.values())
            
            if min_kills == 0 and max_kills > 10:
                inactive_tests = [
                    t for t, stats in test_analysis.items()
                    if stats["mutations_killed"] == 0
                ]
                recommendations.append(
                    f"⚠️ {len(inactive_tests)} tests don't kill any mutations. "
                    "Review if they are necessary."
                )
        
        return recommendations


@dataclass
class AnalysisResult:
    """Result of mutation analysis."""
    summary: Dict[str, Any]
    operator_analysis: Dict[str, Any]
    file_analysis: Dict[str, Any]
    test_analysis: Dict[str, Any]
    time_analysis: Dict[str, Any]
    correlation_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": self.summary,
            "operator_analysis": self.operator_analysis,
            "file_analysis": self.file_analysis,
            "test_analysis": self.test_analysis,
            "time_analysis": self.time_analysis,
            "correlation_analysis": self.correlation_analysis,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }
    
    def to_json(self, path: Optional[Path] = None) -> str:
        """Export to JSON."""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, default=str)
        
        if path:
            with open(path, "w") as f:
                f.write(json_str)
        
        return json_str
    
    def get_score(self) -> Tuple[float, str]:
        """Get overall mutation score with grade."""
        kill_pct = self.summary.get("kill_percentage", 0)
        
        if kill_pct >= 90:
            return kill_pct, "A"
        elif kill_pct >= 80:
            return kill_pct, "B"
        elif kill_pct >= 70:
            return kill_pct, "C"
        elif kill_pct >= 50:
            return kill_pct, "D"
        else:
            return kill_pct, "F"
    
    def print_summary(self) -> str:
        """Generate human-readable summary."""
        score, grade = self.get_score()
        
        lines = [
            "=" * 60,
            "MUTATION TESTING ANALYSIS",
            "=" * 60,
            "",
            f"Overall Score: {score:.2f}% (Grade: {grade})",
            f"Total Mutations: {self.summary.get('total_mutations', 0)}",
            f"Killed: {self.summary.get('killed', 0)}",
            f"Survived: {self.summary.get('survived', 0)}",
            f"Errors: {self.summary.get('errors', 0)}",
            "",
            "-" * 40,
            "TOP OPERATOR KILL RATES:",
            "-" * 40,
        ]
        
        sorted_ops = sorted(
            self.operator_analysis.items(),
            key=lambda x: x[1].get("kill_rate", 0),
            reverse=True,
        )[:5]
        
        for op, stats in sorted_ops:
            lines.append(
                f"  {op}: {stats.get('kill_rate', 0):.1f}% "
                f"({stats.get('killed', 0)}/{stats.get('total', 0)})"
            )
        
        if self.recommendations:
            lines.extend(["", "-" * 40, "RECOMMENDATIONS:", "-" * 40])
            for rec in self.recommendations:
                lines.append(f"  {rec}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class ComparativeAnalyzer:
    """
    Compares mutation testing results across different runs or configurations.
    """
    
    def compare(
        self,
        baseline: AnalysisResult,
        current: AnalysisResult,
    ) -> Dict[str, Any]:
        """Compare two analysis results."""
        comparison = {
            "score_change": current.summary.get("kill_percentage", 0) - 
                           baseline.summary.get("kill_percentage", 0),
            "total_mutations_change": current.summary.get("total_mutations", 0) -
                                     baseline.summary.get("total_mutations", 0),
            "killed_change": current.summary.get("killed", 0) -
                            baseline.summary.get("killed", 0),
            "survived_change": current.summary.get("survived", 0) -
                              baseline.summary.get("survived", 0),
            "operator_changes": {},
            "file_changes": {},
        }
        
        # Compare operators
        all_ops = set(baseline.operator_analysis.keys()) | set(current.operator_analysis.keys())
        for op in all_ops:
            base_stats = baseline.operator_analysis.get(op, {})
            curr_stats = current.operator_analysis.get(op, {})
            
            comparison["operator_changes"][op] = {
                "kill_rate_change": curr_stats.get("kill_rate", 0) - base_stats.get("kill_rate", 0),
                "total_change": curr_stats.get("total", 0) - base_stats.get("total", 0),
            }
        
        # Compare files
        all_files = set(baseline.file_analysis.keys()) | set(current.file_analysis.keys())
        for file in all_files:
            base_stats = baseline.file_analysis.get(file, {})
            curr_stats = current.file_analysis.get(file, {})
            
            comparison["file_changes"][file] = {
                "kill_rate_change": curr_stats.get("kill_rate", 0) - base_stats.get("kill_rate", 0),
            }
        
        return comparison
