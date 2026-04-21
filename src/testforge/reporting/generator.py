"""
Report generation for mutation testing results.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

from ..core.mutation import Mutation, MutationResult, MutationStatus, KillMatrix, MutationSession
from ..core.analyzer import MutationAnalyzer, AnalysisResult
from ..core.scorer import EffectivenessScorer, MutationScoreReport


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    format: str = "html"  # html, json, markdown, pdf
    include_kill_matrix: bool = True
    include_source_context: bool = True
    include_charts: bool = True
    include_recommendations: bool = True
    max_surviving_mutations: int = 50
    max_mutations_per_file: int = 20
    output_path: Optional[Path] = None


class ReportGenerator:
    """
    Generates comprehensive mutation testing reports.
    
    Supports multiple output formats and provides detailed
    analysis of mutation testing results.
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self._analyzer = MutationAnalyzer()
        self._scorer = EffectivenessScorer()
    
    def generate_report(
        self,
        session: MutationSession,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a complete mutation testing report.
        
        Args:
            session: Mutation testing session
            output_path: Path to save the report
            
        Returns:
            Generated report content
        """
        output_path = output_path or self.config.output_path
        
        # Analyze results
        analysis = self._analyzer.analyze_session(session)
        score, grade, components = self._scorer.compute_score(session)
        test_rankings = self._scorer.rank_tests(session)
        coverage_metrics = self._scorer.compute_coverage_metrics(session)
        
        # Generate based on format
        if self.config.format == "json":
            return self._generate_json_report(session, analysis, score, grade, test_rankings, output_path)
        elif self.config.format == "markdown":
            return self._generate_markdown_report(session, analysis, score, grade, test_rankings, output_path)
        elif self.config.format == "html":
            return self._generate_html_report(session, analysis, score, grade, test_rankings, coverage_metrics, output_path)
        else:
            return self._generate_markdown_report(session, analysis, score, grade, test_rankings, output_path)
    
    def _generate_json_report(
        self,
        session: MutationSession,
        analysis: AnalysisResult,
        score: float,
        grade: Any,
        test_rankings: List[Dict],
        output_path: Optional[Path],
    ) -> str:
        """Generate JSON report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_id": session.session_id,
                "format_version": "1.0",
            },
            "summary": analysis.summary,
            "analysis": analysis.to_dict(),
            "score": {
                "overall": score,
                "grade": grade.value if hasattr(grade, 'value') else str(grade),
                "components": {
                    "base_score": components.base_score,
                    "coverage_bonus": components.coverage_bonus,
                    "operator_penalty": components.operator_penalty,
                    "time_penalty": components.time_penalty,
                    "redundancy_penalty": components.redundancy_penalty,
                },
            },
            "test_rankings": test_rankings[:20],
            "kill_matrix": session.kill_matrix.to_dict(),
            "surviving_mutations": [
                m.to_dict() for m in session.get_surviving_mutations()
            ][:self.config.max_surviving_mutations],
            "recommendations": analysis.recommendations,
        }
        
        json_str = json.dumps(report, indent=2, default=str)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(json_str)
        
        return json_str
    
    def _generate_markdown_report(
        self,
        session: MutationSession,
        analysis: AnalysisResult,
        score: float,
        grade: Any,
        test_rankings: List[Dict],
        output_path: Optional[Path],
    ) -> str:
        """Generate Markdown report."""
        lines = [
            "# Mutation Testing Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Session ID:** {session.session_id}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|---------|-------|",
            f"| Total Mutations | {analysis.summary.get('total_mutations', 0)} |",
            f"| Killed | {analysis.summary.get('killed', 0)} |",
            f"| Survived | {analysis.summary.get('survived', 0)} |",
            f"| Kill Rate | {analysis.summary.get('kill_percentage', 0):.2f}% |",
            f"| Effectiveness Score | {score:.2f} |",
            f"| Grade | {grade.value if hasattr(grade, 'value') else str(grade)} |",
            "",
            "## Operator Analysis",
            "",
        ]
        
        # Add operator table
        lines.append("| Operator | Total | Killed | Kill Rate |")
        lines.append("|---------|-------|--------|----------|")
        
        for op, stats in sorted(
            analysis.operator_analysis.items(),
            key=lambda x: x[1].get("kill_rate", 0),
            reverse=True,
        ):
            lines.append(
                f"| {op} | {stats.get('total', 0)} | "
                f"{stats.get('killed', 0)} | {stats.get('kill_rate', 0):.1f}% |"
            )
        
        lines.extend(["", "## Top Test Rankings", ""])
        lines.append("| Rank | Test | Mutations Killed | Coverage |")
        lines.append("|------|------|-----------------|----------|")
        
        for i, test in enumerate(test_rankings[:10], 1):
            lines.append(
                f"| {i} | {test.get('test_name', 'N/A')} | "
                f"{test.get('mutations_killed', 0)} | "
                f"{test.get('coverage_percentage', 0):.1f}% |"
            )
        
        # Add recommendations
        if self.config.include_recommendations and analysis.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in analysis.recommendations:
                lines.append(f"- {rec}")
        
        # Add surviving mutations
        surviving = session.get_surviving_mutations()
        if surviving:
            lines.extend(["", f"## Surviving Mutations ({len(surviving)} total)", ""])
            
            for mutation in surviving[:self.config.max_surviving_mutations]:
                lines.append(
                    f"- `{mutation.operator_type.value}` in "
                    f"`{mutation.source_file.name}`:{mutation.line_number} - "
                    f"`{mutation.original_code}` → `{mutation.mutated_code}`"
                )
        
        markdown = "\n".join(lines)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(markdown)
        
        return markdown
    
    def _generate_html_report(
        self,
        session: MutationSession,
        analysis: AnalysisResult,
        score: float,
        grade: Any,
        test_rankings: List[Dict],
        coverage_metrics: Dict,
        output_path: Optional[Path],
    ) -> str:
        """Generate HTML report."""
        kill_pct = analysis.summary.get('kill_percentage', 0)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestForge - Mutation Testing Report</title>
    <style>
        :root {{
            --primary: #4f46e5;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-800: #1f2937;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--gray-800);
            background: var(--gray-100);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            background: white;
            padding: 2rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 1.875rem;
            margin-bottom: 0.5rem;
        }}
        
        .score-display {{
            display: flex;
            align-items: center;
            gap: 2rem;
            margin-top: 1rem;
        }}
        
        .score-circle {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: conic-gradient(
                var(--success) {kill_pct}%,
                var(--gray-200) {kill_pct}%
            );
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        
        .score-circle::before {{
            content: '';
            width: 90px;
            height: 90px;
            background: white;
            border-radius: 50%;
            position: absolute;
        }}
        
        .score-value {{
            position: relative;
            font-size: 1.5rem;
            font-weight: bold;
        }}
        
        .grade-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-size: 1.5rem;
            font-weight: bold;
            background: {'var(--success)' if kill_pct >= 80 else 'var(--warning)' if kill_pct >= 50 else 'var(--danger)'};
            color: white;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .card h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--gray-200);
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--gray-200);
        }}
        
        .stat:last-child {{
            border-bottom: none;
        }}
        
        .stat-value {{
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }}
        
        th {{
            font-weight: 600;
            color: var(--gray-800);
        }}
        
        .operator-tag {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
            background: var(--gray-200);
        }}
        
        .mutation-item {{
            padding: 0.75rem;
            margin: 0.5rem 0;
            background: var(--gray-100);
            border-radius: 0.25rem;
            font-family: monospace;
            font-size: 0.875rem;
        }}
        
        .recommendation {{
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0.25rem;
            background: var(--gray-100);
            border-left: 4px solid var(--primary);
        }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            color: #6b7280;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧪 TestForge Mutation Testing Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="score-display">
                <div class="score-circle">
                    <span class="score-value">{kill_pct:.1f}%</span>
                </div>
                <div>
                    <p>Mutation Score</p>
                    <span class="grade-badge">{grade.value if hasattr(grade, 'value') else str(grade)}</span>
                </div>
            </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>📊 Summary</h2>
                <div class="stat">
                    <span>Total Mutations</span>
                    <span class="stat-value">{analysis.summary.get('total_mutations', 0)}</span>
                </div>
                <div class="stat">
                    <span>Killed</span>
                    <span class="stat-value" style="color: var(--success)">{analysis.summary.get('killed', 0)}</span>
                </div>
                <div class="stat">
                    <span>Survived</span>
                    <span class="stat-value" style="color: var(--danger)">{analysis.summary.get('survived', 0)}</span>
                </div>
                <div class="stat">
                    <span>Errors</span>
                    <span class="stat-value">{analysis.summary.get('errors', 0)}</span>
                </div>
                <div class="stat">
                    <span>Avg Execution Time</span>
                    <span class="stat-value">{analysis.summary.get('average_execution_time', 0):.2f}s</span>
                </div>
            </div>
            
            <div class="card">
                <h2>⚡ Test Rankings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Test</th>
                            <th>Kills</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for i, test in enumerate(test_rankings[:5], 1):
            html += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{test.get('test_name', 'N/A')}</td>
                            <td>{test.get('mutations_killed', 0)}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <h2>🔧 Operator Analysis</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Operator</th>
                            <th>Total</th>
                            <th>Kill Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for op, stats in sorted(
            analysis.operator_analysis.items(),
            key=lambda x: x[1].get("kill_rate", 0),
            reverse=True,
        )[:5]:
            html += f"""
                        <tr>
                            <td><span class="operator-tag">{op}</span></td>
                            <td>{stats.get('total', 0)}</td>
                            <td>{stats.get('kill_rate', 0):.1f}%</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
"""
        
        # Add recommendations
        if self.config.include_recommendations and analysis.recommendations:
            html += """
        <div class="card">
            <h2>💡 Recommendations</h2>
"""
            for rec in analysis.recommendations:
                html += f'<div class="recommendation">{rec}</div>\n'
            html += "</div>\n"
        
        # Add surviving mutations
        surviving = session.get_surviving_mutations()
        if surviving:
            html += """
        <div class="card">
            <h2>⚠️ Surviving Mutations</h2>
            <p>These mutations were not killed by any test:</p>
"""
            for mutation in surviving[:self.config.max_surviving_mutations]:
                html += f"""
            <div class="mutation-item">
                <strong>{mutation.operator_type.value}</strong> in 
                <code>{mutation.source_file.name}:{mutation.line_number}</code><br>
                {mutation.original_code} → {mutation.mutated_code}
            </div>
"""
            html += "</div>\n"
        
        html += f"""
        <footer>
            <p>Generated by TestForge v1.0.0 | Session ID: {session.session_id}</p>
        </footer>
    </div>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(html)
        
        return html
    
    def generate_diff_report(
        self,
        baseline_session: MutationSession,
        current_session: MutationSession,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a differential report comparing two sessions.
        
        Useful for tracking mutation testing improvements over time.
        """
        baseline_analysis = self._analyzer.analyze_session(baseline_session)
        current_analysis = self._analyzer.analyze_session(current_session)
        
        baseline_score, _, _ = self._scorer.compute_score(baseline_session)
        current_score, current_grade, _ = self._scorer.compute_score(current_session)
        
        score_diff = current_score - baseline_score
        killed_diff = (current_analysis.summary.get('killed', 0) - 
                      baseline_analysis.summary.get('killed', 0))
        survived_diff = (current_analysis.summary.get('survived', 0) - 
                        baseline_analysis.summary.get('survived', 0))
        
        lines = [
            "# Mutation Testing Diff Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"| Metric | Baseline | Current | Change |",
            f"|---------|----------|---------|--------|",
            f"| Score | {baseline_score:.2f}% | {current_score:.2f}% | {'+' if score_diff >= 0 else ''}{score_diff:.2f}% |",
            f"| Killed | {baseline_analysis.summary.get('killed', 0)} | "
            f"{current_analysis.summary.get('killed', 0)} | {'+' if killed_diff >= 0 else ''}{killed_diff} |",
            f"| Survived | {baseline_analysis.summary.get('survived', 0)} | "
            f"{current_analysis.summary.get('survived', 0)} | {'+' if survived_diff >= 0 else ''}{survived_diff} |",
            "",
            "## Status",
            "",
        ]
        
        if score_diff > 0:
            lines.append("✅ **Improved!** Mutation score increased.")
        elif score_diff < 0:
            lines.append("⚠️ **Regression!** Mutation score decreased.")
        else:
            lines.append("➡️ **Unchanged.** No improvement or regression.")
        
        markdown = "\n".join(lines)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(markdown)
        
        return markdown
