"""
Visualization for mutation testing results.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import json
import base64
from io import BytesIO


@dataclass
class ChartData:
    """Data for chart visualization."""
    labels: List[str]
    datasets: List[Dict[str, Any]]


class MutationVisualizer:
    """
    Creates visualizations for mutation testing results.
    
    Generates charts, graphs, and interactive visualizations
    using various backends.
    """
    
    def __init__(self, output_format: str = "svg"):
        self.output_format = output_format
    
    def create_kill_matrix_heatmap(
        self,
        kill_matrix: Any,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Create a heatmap visualization of the kill matrix.
        
        Rows are mutations, columns are tests.
        Green = killed, Red = survived.
        """
        # Generate HTML/JavaScript for interactive heatmap
        mutations = kill_matrix.mutations
        tests = kill_matrix.tests
        kills = kill_matrix.kills
        
        # Create data arrays
        mutation_labels = [f"M{i+1}" for i in range(len(mutations))]
        test_labels = tests
        
        # Create heatmap data
        heatmap_data = []
        for mutation in mutations:
            row = []
            for test in tests:
                killed = 1 if kill_matrix.did_kill(mutation.id, test) else 0
                row.append(killed)
            heatmap_data.append(row)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Kill Matrix Heatmap</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        #heatmap {{ width: 100%; height: 800px; }}
    </style>
</head>
<body>
    <h1>Mutation Kill Matrix</h1>
    <div id="heatmap"></div>
    <script>
        var data = [{{
            z: {json.dumps(heatmap_data)},
            x: {json.dumps(test_labels)},
            y: {json.dumps(mutation_labels)},
            type: 'heatmap',
            colorscale: [
                [0, '#ef4444'],
                [1, '#22c55e']
            ],
            showscale: true,
            colorbar: {{
                title: 'Killed',
                titleside: 'right'
            }}
        }}];
        
        var layout = {{
            title: 'Mutation Kill Matrix Heatmap',
            xaxis: {{ title: 'Tests', tickangle: -45 }},
            yaxis: {{ title: 'Mutations', autorange: 'reversed' }},
            width: 1200,
            height: 800
        }};
        
        Plotly.newPlot('heatmap', data, layout);
    </script>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(html)
        
        return html
    
    def create_operator_chart(
        self,
        operator_analysis: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> str:
        """Create a bar chart of operator kill rates."""
        labels = list(operator_analysis.keys())
        kill_rates = [stats.get("kill_rate", 0) for stats in operator_analysis.values()]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Operator Kill Rates</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="chart"></div>
    <script>
        var data = [{{
            x: {json.dumps(labels)},
            y: {json.dumps(kill_rates)},
            type: 'bar',
            marker: {{
                color: {json.dumps(kill_rates)},
                colorscale: 'RdYlGn'
            }}
        }}];
        
        var layout = {{
            title: 'Mutation Kill Rates by Operator',
            xaxis: {{ title: 'Operator' }},
            yaxis: {{ title: 'Kill Rate (%)', range: [0, 100] }},
            width: 1000,
            height: 600
        }};
        
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(html)
        
        return html
    
    def create_timeline_chart(
        self,
        results: List[Any],
        output_path: Optional[Path] = None,
    ) -> str:
        """Create a timeline of mutation execution."""
        # Sort by execution time
        sorted_results = sorted(results, key=lambda r: r.execution_time, reverse=True)
        
        labels = [f"M{i+1}" for i in range(len(sorted_results))]
        times = [r.execution_time for r in sorted_results]
        colors = ["#22c55e" if r.is_killed() else "#ef4444" for r in sorted_results]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mutation Execution Timeline</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="chart"></div>
    <script>
        var data = [{{
            x: {json.dumps(labels[:20])},
            y: {json.dumps(times[:20])},
            type: 'bar',
            marker: {{ color: {json.dumps(colors[:20])} }},
            orientation: 'v'
        }}];
        
        var layout = {{
            title: 'Top 20 Slowest Mutations (Green=Killed, Red=Survived)',
            xaxis: {{ title: 'Mutation' }},
            yaxis: {{ title: 'Execution Time (s)' }},
            width: 1000,
            height: 600
        }};
        
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(html)
        
        return html
    
    def create_dashboard(
        self,
        session: Any,
        analysis: Any,
        output_path: Optional[Path] = None,
    ) -> str:
        """Create a complete dashboard with multiple visualizations."""
        kill_pct = analysis.summary.get('kill_percentage', 0)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>TestForge Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .chart-card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🧪 TestForge Mutation Testing Dashboard</h1>
            <p>Generated: {session.session_id}</p>
        </div>
        
        <div class="grid">
            <div class="stat-card">
                <div class="stat-value" style="color: #4f46e5;">{analysis.summary.get('total_mutations', 0)}</div>
                <div class="stat-label">Total Mutations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #22c55e;">{analysis.summary.get('killed', 0)}</div>
                <div class="stat-label">Killed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ef4444;">{analysis.summary.get('survived', 0)}</div>
                <div class="stat-label">Survived</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #f59e0b;">{kill_pct:.1f}%</div>
                <div class="stat-label">Kill Rate</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="chart-card" style="grid-column: span 2;">
                <h3>Kill Rate by Operator</h3>
                <div id="operator-chart"></div>
            </div>
            <div class="chart-card" style="grid-column: span 2;">
                <h3>Mutation Status</h3>
                <div id="pie-chart"></div>
            </div>
        </div>
        
        <div class="chart-card">
            <h3>Execution Time Distribution</h3>
            <div id="histogram"></div>
        </div>
    </div>
    
    <script>
        // Operator chart
        var operatorData = {{
            x: {json.dumps(list(analysis.operator_analysis.keys()))},
            y: {json.dumps([s.get('kill_rate', 0) for s in analysis.operator_analysis.values()])},
            type: 'bar',
            marker: {{ color: '#4f46e5' }}
        }};
        Plotly.newPlot('operator-chart', [operatorData], {{
            xaxis: {{ title: 'Operator' }},
            yaxis: {{ title: 'Kill Rate (%)', range: [0, 100] }},
            margin: {{ t: 30, b: 80 }}
        }});
        
        // Pie chart
        var pieData = [{{
            values: [{analysis.summary.get('killed', 0)}, {analysis.summary.get('survived', 0)}, {analysis.summary.get('errors', 0)}],
            labels: ['Killed', 'Survived', 'Errors'],
            type: 'pie',
            colors: ['#22c55e', '#ef4444', '#f59e0b']
        }}];
        Plotly.newPlot('pie-chart', pieData, {{ margin: {{ t: 30, b: 30 }}}});
        
        // Histogram
        var histData = [{{
            x: {json.dumps([r.execution_time for r in session.results if hasattr(r, 'execution_time')])},
            type: 'histogram',
            marker: {{ color: '#4f46e5' }}
        }}];
        Plotly.newPlot('histogram', histData, {{
            xaxis: {{ title: 'Execution Time (s)' }},
            yaxis: {{ title: 'Count' }}
        }});
    </script>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(html)
        
        return html
    
    def generate_svg_chart(
        self,
        data: ChartData,
        chart_type: str = "bar",
    ) -> str:
        """Generate SVG chart without external dependencies."""
        if chart_type == "bar":
            return self._generate_bar_chart_svg(data)
        elif chart_type == "pie":
            return self._generate_pie_chart_svg(data)
        else:
            return ""
    
    def _generate_bar_chart_svg(self, data: ChartData) -> str:
        """Generate SVG bar chart."""
        if not data.labels or not data.datasets:
            return ""
        
        width = 600
        height = 400
        padding = 50
        
        max_value = max(
            max(ds.get("data", [0])) 
            for ds in data.datasets
        ) if data.datasets else 100
        
        bar_width = (width - 2 * padding) / len(data.labels)
        
        svg_lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
        ]
        
        # Y axis
        svg_lines.append(
            f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="black"/>'
        )
        
        # X axis
        svg_lines.append(
            f'<line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="black"/>'
        )
        
        # Bars
        for i, label in enumerate(data.labels):
            for ds in data.datasets:
                values = ds.get("data", [])
                if i < len(values):
                    value = values[i]
                    bar_height = (value / max_value) * (height - 2 * padding)
                    x = padding + i * bar_width + 5
                    y = height - padding - bar_height
                    
                    color = ds.get("color", "#4f46e5")
                    svg_lines.append(
                        f'<rect x="{x}" y="{y}" width="{bar_width - 10}" height="{bar_height}" fill="{color}"/>'
                    )
        
        svg_lines.append("</svg>")
        
        return "\n".join(svg_lines)
    
    def _generate_pie_chart_svg(self, data: ChartData) -> str:
        """Generate SVG pie chart."""
        if not data.datasets or not data.datasets[0].get("data"):
            return ""
        
        values = data.datasets[0]["data"]
        total = sum(values)
        
        width = 400
        height = 400
        cx = width / 2
        cy = height / 2
        radius = min(cx, cy) - 20
        
        colors = ["#4f46e5", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6"]
        
        svg_lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
        ]
        
        current_angle = -90  # Start at top
        
        for i, value in enumerate(values):
            if total == 0:
                continue
            
            angle = (value / total) * 360
            end_angle = current_angle + angle
            
            # Calculate arc path
            x1 = cx + radius * (current_angle / 360 * 6.28).cos()
            y1 = cy + radius * (current_angle / 360 * 6.28).sin()
            
            # This is simplified - real implementation would need proper arc calculation
            
            current_angle = end_angle
        
        svg_lines.append("</svg>")
        
        return "\n".join(svg_lines)
