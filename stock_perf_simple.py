import yfinance as yf
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_total_return(stocks, quantities, purchase_dates, index_ticker="^GSPC"):
    """
    Given lists of stocks, quantities purchased, and purchase dates, returns:
    - A dataframe summarizing total return for each stock.
    - Portfolio-level returns (absolute and %).
    - Index benchmark return for:
        * Overall (from earliest purchase date to now)
        * 6 months
        * 1 month
    
    Parameters
    ----------
    stocks : list of str
        Stock tickers (e.g. ["AAPL", "MSFT"]).
    quantities : list of int
        Quantities purchased for each corresponding stock.
    purchase_dates : list of str (YYYY-MM-DD format)
        Purchase dates for each corresponding stock.
    index_ticker : str, optional
        Ticker symbol used for comparison, e.g. "^GSPC" (S&P 500).
    
    Returns
    -------
    df_summary : pd.DataFrame
        Per-stock summary: purchase price, current price, absolute return, % return
    total_portfolio_return_value : float
        The total return ($) from purchase to now
    total_portfolio_return_pct : float
        The total return (%) from purchase to now
    index_return_pct_overall : float
        The index return (%) from the earliest purchase date to now
    portfolio_return_6m : float
        The portfolio 6-month return (%)
    index_return_6m : float
        The index 6-month return (%)
    portfolio_return_1m : float
        The portfolio 1-month return (%)
    index_return_1m : float
        The index 1-month return (%)
    """
    if not (len(stocks) == len(quantities) == len(purchase_dates)):
        raise ValueError("stocks, quantities, and purchase_dates must have the same length.")
    
    # Convert purchase_dates to datetime objects
    purchase_datetimes = [datetime.strptime(d, "%Y-%m-%d") for d in purchase_dates]
    earliest_purchase_date = min(purchase_datetimes)
    earliest_purchase_date_str = earliest_purchase_date.strftime("%Y-%m-%d")
    
    # Define 'now' and other key dates
    end_date = datetime.today()
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    six_month_ago = end_date - relativedelta(months=6)
    six_month_ago_str = six_month_ago.strftime("%Y-%m-%d")
    
    one_month_ago = end_date - relativedelta(months=1)
    one_month_ago_str = one_month_ago.strftime("%Y-%m-%d")
    
    # Prepare summary data
    data_dict = {
        "Stock": [],
        "Purchase Date": [],
        "Quantity": [],
        "Purchase Price": [],
        "Current Price": [],
        "Absolute Return ($)": [],
        "Return (%)": []
    }
    
    total_invested = 0.0
    total_current_value = 0.0
    
    # We'll also store daily price history in a dict to compute 6m and 1m portfolio returns
    # Key: stock ticker, Value: DataFrame of historical prices
    price_history = {}
    
    # ------------- 1) LOOP THROUGH STOCKS AND CALCULATE OVERALL RETURNS -------------
    for stock, qty, p_date in zip(stocks, quantities, purchase_datetimes):
        # Download from the purchase date (minus a bit of buffer if you like) to today
        df = yf.download(stock, start=p_date.strftime("%Y-%m-%d"), end=end_date_str, progress=False)
        
        if df.empty:
            print(f"Warning: No data found for {stock}. Skipping.")
            continue
        
        # Store the entire price history so we can look up 6m / 1m prices
        price_history[stock] = df.copy()
        
        # Purchase price = close price on/near purchase date (first row in df)
        purchase_price = df.iloc[0]["Close"]
        # Current price = last close price
        current_price = df.iloc[-1]["Close"]
        
        # Returns
        cost_basis = purchase_price * qty
        current_value = current_price * qty
        abs_return = current_value - cost_basis
        pct_return = (abs_return / cost_basis) * 100
        
        # Populate summary
        data_dict["Stock"].append(stock)
        data_dict["Purchase Date"].append(p_date.strftime("%Y-%m-%d"))
        data_dict["Quantity"].append(qty)
        data_dict["Purchase Price"].append(round(purchase_price, 2))
        data_dict["Current Price"].append(round(current_price, 2))
        data_dict["Absolute Return ($)"].append(round(abs_return, 2))
        data_dict["Return (%)"].append(round(pct_return, 2))
        
        # Totals
        total_invested += cost_basis.iloc[0]
        total_current_value += current_value.iloc[0]
        #total_invested += cost_basis
        #total_current_value += current_value
    
    df_summary = pd.DataFrame(data_dict)
    
    # Overall portfolio return
    total_portfolio_return_value = total_current_value - total_invested
    if total_invested > 0:
        total_portfolio_return_pct = (total_portfolio_return_value / total_invested) * 100
    else:
        total_portfolio_return_pct = 0.0
    
    # ------------- 2) GET INDEX DATA FOR ENTIRE PERIOD -------------
    index_df = yf.download(index_ticker, start=earliest_purchase_date_str, end=end_date_str, progress=False)
    
    if not index_df.empty:
        index_start_price = index_df.iloc[0]["Close"]
        index_end_price = index_df.iloc[-1]["Close"]
        index_return_pct_overall = ((index_end_price - index_start_price) / index_start_price) * 100
    else:
        index_return_pct_overall = float('nan')
    
    # ------------- 3) PORTFOLIO & INDEX VALUE AT 6 MONTHS AGO AND 1 MONTH AGO -------------
    
    # Helper function to get a price from df on/near a date
    # We'll pick the last available close on or before 'the_date_str'.
    def get_price_on_or_before(df_price, the_date_str):
        # df_price index might be a DateTimeIndex
        # We can slice up to the_date_str. This returns all rows up to the_date_str, then take last row.
        sub_df = df_price.loc[:the_date_str]
        if sub_df.empty:
            return None  # No data up to that date
        return sub_df.iloc[-1]["Close"]
    
    # Compute portfolio value at date
    def get_portfolio_value(price_hist_dict, date_str):
        portfolio_value = 0.0
        for (stock, qty, p_date) in zip(stocks, quantities, purchase_datetimes):
            if stock not in price_hist_dict:
                continue
            df_price = price_hist_dict[stock]
            # Get the close price on/near date_str
            price_at_date = get_price_on_or_before(df_price, date_str)
            if price_at_date is not None:
                position_value = price_at_date.iloc[0] * qty
                portfolio_value += position_value
        return portfolio_value
    
    # Portfolio values
    portfolio_value_now = total_current_value  # already computed as sum of last close
    portfolio_value_6m = get_portfolio_value(price_history, six_month_ago_str)
    portfolio_value_1m = get_portfolio_value(price_history, one_month_ago_str)
    
    # Portfolio 6-month return
    if portfolio_value_6m and portfolio_value_6m != 0.0:
        portfolio_return_6m = ((portfolio_value_now - portfolio_value_6m) / portfolio_value_6m) * 100
    else:
        portfolio_return_6m = float('nan')
    
    # Portfolio 1-month return
    if portfolio_value_1m and portfolio_value_1m != 0.0:
        portfolio_return_1m = ((portfolio_value_now - portfolio_value_1m) / portfolio_value_1m) * 100
    else:
        portfolio_return_1m = float('nan')
    
    # Index values at 6 months ago / 1 month ago
    def get_index_return(index_df, date_str):
        # price now vs. price at date_str
        if index_df.empty:
            return float('nan')
        index_price_then = get_price_on_or_before(index_df, date_str).iloc[0]
        if (index_price_then is not None) and (index_price_then != 0.0):
            index_price_now = index_df.iloc[-1]["Close"]
            return ((index_price_now - index_price_then) / index_price_then) * 100
        return float('nan')
    
    index_return_6m = get_index_return(index_df, six_month_ago_str)
    index_return_1m = get_index_return(index_df, one_month_ago_str)
    
    # ------------- 4) RETURN ALL METRICS -------------
    return (
        df_summary,
        round(total_portfolio_return_value, 2),
        round(total_portfolio_return_pct, 2),
        round(index_return_pct_overall, 2),
        round(portfolio_return_6m, 2),
        round(index_return_6m, 2),
        round(portfolio_return_1m, 2),
        round(index_return_1m, 2),
    )


if __name__ == "__main__":
    # Example data usage
    stocks = ["AAPL", "MSFT", "TSLA"]
    quantities = [10, 5, 2]
    purchase_dates = ["2020-01-02", "2020-05-10", "2021-03-01"]
    
    (
        df_summary,
        total_return_val, 
        total_return_pct,
        index_return_pct_overall,
        portfolio_return_6m,
        index_return_6m,
        portfolio_return_1m,
        index_return_1m
    ) = get_total_return(stocks, quantities, purchase_dates, index_ticker="^GSPC")
    
    print("\n=== Portfolio Summary (per stock) ===\n", df_summary)
    print("\n=== Overall Return (From Purchase) ===")
    print(f"Total Portfolio Return (USD): {total_return_val}")
    print(f"Total Portfolio Return (%): {total_return_pct}%")
    print(f"S&P 500 Return (%): {index_return_pct_overall.iloc[0]}%")

    print("\n=== 6-Month Return ===")
    print(f"Portfolio 6-Month Return (%): {portfolio_return_6m}%")
    print(f"S&P 500 6-Month Return (%): {index_return_6m.iloc[0]}%")

    print("\n=== 1-Month Return ===")
    print(f"Portfolio 1-Month Return (%): {portfolio_return_1m}%")
    print(f"S&P 500 1-Month Return (%): {index_return_1m.iloc[0]}%")

