"""
TestForge - Mutation Testing Framework

A comprehensive mutation testing framework for evaluating test suite effectiveness.
Supports multiple programming languages and testing frameworks.
"""

__version__ = "1.0.0"
__author__ = "TestForge Team"
__license__ = "MIT"

from .core.mutator import Mutator
from .core.executor import MutationExecutor
from .core.analyzer import MutationAnalyzer
from .core.scorer import EffectivenessScorer
from .core.mutation import Mutation, MutationResult, MutationStatus, KillMatrix
from .operators.registry import OperatorRegistry
from .analysis.coverage import CoverageAnalyzer
from .reporting.generator import ReportGenerator
from .reporting.visualizer import MutationVisualizer
from .debugging.time_travel import TimeTravelDebugger
from .autogen.test_generator import TestGenerator
from .integration.runner import FrameworkIntegration
from .cicd.pipeline import CIPipeline

__all__ = [
    "Mutator",
    "MutationExecutor",
    "MutationAnalyzer",
    "EffectivenessScorer",
    "KillMatrix",
    "OperatorRegistry",
    "CoverageAnalyzer",
    "ReportGenerator",
    "MutationVisualizer",
    "TimeTravelDebugger",
    "TestGenerator",
    "FrameworkIntegration",
    "CIPipeline",
]
