"""Tests for sample calculator module."""

import pytest
from calculator import (
    add,
    subtract,
    multiply,
    divide,
    is_positive,
    is_negative,
    compare,
    max_of_three,
    clamp,
    absolute_value,
)


class TestAdd:
    """Tests for add function."""
    
    def test_add_positive_numbers(self):
        assert add(2, 3) == 5
    
    def test_add_negative_numbers(self):
        assert add(-2, -3) == -5
    
    def test_add_mixed_numbers(self):
        assert add(-2, 3) == 1
    
    def test_add_zero(self):
        assert add(5, 0) == 5


class TestSubtract:
    """Tests for subtract function."""
    
    def test_subtract_positive_numbers(self):
        assert subtract(5, 3) == 2
    
    def test_subtract_negative_numbers(self):
        assert subtract(-5, -3) == -2
    
    def test_subtract_result_negative(self):
        assert subtract(2, 5) == -3


class TestMultiply:
    """Tests for multiply function."""
    
    def test_multiply_positive_numbers(self):
        assert multiply(3, 4) == 12
    
    def test_multiply_by_zero(self):
        assert multiply(5, 0) == 0
    
    def test_multiply_negative_numbers(self):
        assert multiply(-3, -4) == 12


class TestDivide:
    """Tests for divide function."""
    
    def test_divide_positive_numbers(self):
        assert divide(10, 2) == 5.0
    
    def test_divide_result_float(self):
        assert divide(7, 2) == 3.5
    
    def test_divide_by_zero_raises(self):
        with pytest.raises(ValueError):
            divide(5, 0)


class TestIsPositive:
    """Tests for is_positive function."""
    
    def test_positive_number(self):
        assert is_positive(5) is True
    
    def test_zero_is_not_positive(self):
        assert is_positive(0) is False
    
    def test_negative_number(self):
        assert is_positive(-5) is False


class TestIsNegative:
    """Tests for is_negative function."""
    
    def test_negative_number(self):
        assert is_negative(-5) is True
    
    def test_zero_is_not_negative(self):
        assert is_negative(0) is False
    
    def test_positive_number(self):
        assert is_negative(5) is False


class TestCompare:
    """Tests for compare function."""
    
    def test_a_greater_than_b(self):
        assert compare(5, 3) == 1
    
    def test_a_less_than_b(self):
        assert compare(3, 5) == -1
    
    def test_a_equal_to_b(self):
        assert compare(5, 5) == 0


class TestMaxOfThree:
    """Tests for max_of_three function."""
    
    def test_first_is_max(self):
        assert max_of_three(5, 3, 2) == 5
    
    def test_second_is_max(self):
        assert max_of_three(2, 5, 3) == 5
    
    def test_third_is_max(self):
        assert max_of_three(2, 3, 5) == 5
    
    def test_all_equal(self):
        assert max_of_three(5, 5, 5) == 5


class TestClamp:
    """Tests for clamp function."""
    
    def test_value_in_range(self):
        assert clamp(5, 0, 10) == 5
    
    def test_value_below_min(self):
        assert clamp(-5, 0, 10) == 0
    
    def test_value_above_max(self):
        assert clamp(15, 0, 10) == 10


class TestAbsoluteValue:
    """Tests for absolute_value function."""
    
    def test_positive_number(self):
        assert absolute_value(5) == 5
    
    def test_negative_number(self):
        assert absolute_value(-5) == 5
    
    def test_zero(self):
        assert absolute_value(0) == 0
