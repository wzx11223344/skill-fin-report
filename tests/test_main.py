#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for skill-fin-report."""

import sys
import os
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report import safe_float, fmt_market_cap, _compute_rsi, _compute_macd


class TestSafeFloat:
    """Tests for safe_float function."""

    def test_safe_float_normal(self):
        """Test safe_float with normal numeric values."""
        assert safe_float("123.45") == 123.45
        assert safe_float(100) == 100.0
        assert safe_float("3.14") == 3.14

    def test_safe_float_invalid(self):
        """Test safe_float with invalid inputs returns default."""
        assert safe_float("abc") == 0.0
        assert safe_float(None) == 0.0

    def test_safe_float_custom_default(self):
        """Test safe_float with custom default value."""
        assert safe_float("abc", default=-1.0) == -1.0
        assert safe_float(None, default=999.0) == 999.0


class TestFmtMarketCap:
    """Tests for fmt_market_cap function."""

    def test_fmt_market_cap_trillion(self):
        """Test formatting for万亿 (trillions)."""
        result = fmt_market_cap(2.5e12)
        assert "2.50" in result
        assert "万亿" in result

    def test_fmt_market_cap_yi(self):
        """Test formatting for亿 (100 millions)."""
        result = fmt_market_cap(5e8)
        assert "亿" in result

    def test_fmt_market_cap_zero_or_negative(self):
        """Test formatting for zero or negative values."""
        assert fmt_market_cap(0) == "--"
        assert fmt_market_cap(-100) == "--"
        assert fmt_market_cap("abc") == "--"


class TestComputeRSI:
    """Tests for _compute_rsi function."""

    def test_rsi_normal(self):
        """Test RSI computation with normal price data."""
        np.random.seed(42)
        closes = np.array([100.0 + i * 0.5 + np.random.randn() * 2 for i in range(50)])
        rsi = _compute_rsi(closes, period=14)
        assert rsi is not None
        assert 0.0 <= rsi <= 100.0

    def test_rsi_insufficient_data(self):
        """Test RSI returns None when data is too short."""
        closes = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        rsi = _compute_rsi(closes, period=14)
        assert rsi is None

    def test_rsi_all_gains(self):
        """Test RSI when all price changes are gains."""
        closes = np.linspace(100, 200, 30)
        rsi = _compute_rsi(closes, period=14)
        assert rsi is not None
        assert rsi > 50.0  # All gains should result in high RSI


class TestComputeMACD:
    """Tests for _compute_macd function."""

    def test_macd_normal(self):
        """Test MACD computation with normal price data."""
        np.random.seed(42)
        closes = np.array([100.0 + i * 0.3 + np.random.randn() * 3 for i in range(80)])
        macd_line, signal_line, histogram = _compute_macd(closes)
        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None
        assert abs(histogram - (macd_line - signal_line)) < 0.01

    def test_macd_insufficient_data(self):
        """Test MACD returns None when data is too short."""
        closes = np.array([100.0, 101.0, 102.0])
        macd_line, signal_line, histogram = _compute_macd(closes)
        assert macd_line is None
        assert signal_line is None
        assert histogram is None

    def test_macd_uptrend(self):
        """Test MACD in a strong uptrend produces histogram above 0."""
        closes = np.linspace(100, 300, 100)
        macd_line, signal_line, histogram = _compute_macd(closes)
        assert histogram is not None
        # In a strong uptrend with linear increase, MACD line > signal line
        assert macd_line > signal_line
        assert histogram > 0
