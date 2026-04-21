"""Integration tests for TestForge."""

import pytest
from pathlib import Path
import tempfile
import os
from testforge.integration.runner import (
    FrameworkIntegration,
    PyTestRunner,
    JestRunner,
    TestResult,
    TestSuiteResult,
)


class TestFrameworkIntegration:
    """Integration tests for framework integration."""
    
    def test_detect_pytest(self):
        """Test pytest detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create pytest.ini
            (tmpdir / "pytest.ini").write_text("[pytest]")
            
            integration = FrameworkIntegration.create_from_project(tmpdir)
            
            assert integration.framework == "pytest"
    
    def test_detect_jest(self):
        """Test Jest detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create package.json
            (tmpdir / "package.json").write_text('{"name": "test"}')
            
            integration = FrameworkIntegration.create_from_project(tmpdir)
            
            assert integration.framework == "jest"


class TestPyTestRunner:
    """Tests for PyTestRunner."""
    
    def test_runner_creation(self):
        """Test runner creation."""
        runner = PyTestRunner()
        
        assert runner.get_framework_name() == "pytest"
    
    def test_parse_empty_output(self):
        """Test parsing empty output."""
        runner = PyTestRunner()
        
        result = runner.parse_output("", "", 0)
        
        assert result.framework == "pytest"
        assert result.total_tests == 0


class TestTestResult:
    """Tests for TestResult class."""
    
    def test_result_creation(self):
        """Test result creation."""
        result = TestResult(
            test_name="test_example",
            passed=True,
            duration=1.5,
        )
        
        assert result.test_name == "test_example"
        assert result.passed
        assert result.duration == 1.5


class TestTestSuiteResult:
    """Tests for TestSuiteResult class."""
    
    def test_suite_result_creation(self):
        """Test suite result creation."""
        result = TestSuiteResult(
            framework="pytest",
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
        )
        
        assert result.total_tests == 10
        assert result.passed_tests == 8
        assert result.failed_tests == 2
    
    def test_get_failed_tests(self):
        """Test getting failed tests."""
        result = TestSuiteResult(
            framework="pytest",
            results=[
                TestResult(test_name="test1", passed=True),
                TestResult(test_name="test2", passed=False),
                TestResult(test_name="test3", passed=False),
            ],
        )
        
        failed = result.get_failed_tests()
        
        assert len(failed) == 2
        assert all(not t.passed for t in failed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
