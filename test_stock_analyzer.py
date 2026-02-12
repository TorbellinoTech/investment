import pytest
pytestmark = pytest.mark.db
from stock_analysis import StockAnalyzer

analyzer = StockAnalyzer()

# Get high/low analysis for multiple periods
highs_lows = analyzer.get_high_low_analysis(['AAPL', 'MSFT'])  # Gets 13w, 26w, and 52w by default
# or specify custom periods
custom_periods = analyzer.get_high_low_analysis(['AAPL', 'MSFT'], periods=[4, 8, 13, 26, 52])

print(highs_lows)
print(custom_periods)