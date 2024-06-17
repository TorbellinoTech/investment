import numpy as np
from scipy.stats import entropy

# Example calculation

# Example performance data (percentage returns over different periods)
# Format: [1 day, 1 week, 1 month, 3 months, 6 months, 1 year, 2 years, 5 years]
portfolio_performance = [1, 3, 9.0, 40.0, 80.0, 120.0, 200.0, 800.0]  # Example data
spy_performance = [0.05, 1, 9.5, 18.5, 30.0, 55.0, 70.0, 180.0]  # Example data

# Weights for each period (can be adjusted based on importance)
weights = np.array([1, 1, 1, 1, 1, 1, 1, 1])

# Calculate weighted average performance
weighted_avg_portfolio = np.average(portfolio_performance, weights=weights)
weighted_avg_spy = np.average(spy_performance, weights=weights)

# Calculate performance ratio
performance_ratio = weighted_avg_portfolio / weighted_avg_spy

# Total number of companies in NYSE and NASDAQ
total_companies = 2272 + 3432

# Example portfolio - replace with your actual portfolio composition
portfolio = {
    "CompanyA": 0.3,
    "CompanyB": 0.25,
    "CompanyC": 0.2,
    "CompanyD": 0.15,
    "CompanyE": 0.1
}

# Number of companies in the portfolio
portfolio_size = len(portfolio)

# Define baseline wealth
baseline_wealth = 200000  # Average EU wealth in EUR

# Define the percentage commission
commission_percentage = 0.1  # 10%

# Calculate the initial entropy of the system (uniform distribution over all companies)
initial_prob = 1 / total_companies
initial_entropy = entropy([initial_prob] * total_companies)

# Sort portfolio by weights in ascending order
sorted_portfolio = dict(sorted(portfolio.items(), key=lambda item: item[1]))

# Function to create tiers based on cumulative weights
def create_tiers(portfolio, tier_thresholds):
    cumulative_weight = 0
    tiers = {'Basic': [], 'Standard': [], 'Premium': []}
    for company, weight in portfolio.items():
        cumulative_weight += weight
        if cumulative_weight <= tier_thresholds['Basic']:
            tiers['Basic'].append(company)
        if cumulative_weight <= tier_thresholds['Standard']:
            tiers['Standard'].append(company)
        tiers['Premium'].append(company)
    return tiers

# Define cumulative weight thresholds for tiers
tier_thresholds = {'Basic': 0.4, 'Standard': 0.7, 'Premium': 1.0}

# Create tiers
tiers = create_tiers(sorted_portfolio, tier_thresholds)

# Function to calculate entropy and price for a given tier
def calculate_price(tier, portfolio, initial_entropy, baseline_wealth, performance_ratio, commission_percentage):
    partial_portfolio = {k: portfolio[k] for k in tier}
    partial_distribution = np.array(list(partial_portfolio.values()))
    partial_entropy = entropy(partial_distribution)
    max_partial_entropy = np.log(len(partial_portfolio))  # Max possible entropy for this tier
    normalized_partial_entropy = partial_entropy / max_partial_entropy if max_partial_entropy != 0 else 0
    partial_prob = 1 / len(partial_portfolio)
    partial_conditional_entropy = entropy([partial_prob] * len(partial_portfolio))
    information_gain = initial_entropy - partial_conditional_entropy
    max_information_gain = initial_entropy
    normalized_information_gain = information_gain / max_information_gain if max_information_gain != 0 else 0

    raw_price = baseline_wealth * normalized_information_gain * normalized_partial_entropy * performance_ratio * commission_percentage
    max_price = baseline_wealth * performance_ratio * commission_percentage

    price = min(raw_price, max_price)
    return price

# Calculate cumulative prices for each tier
cumulative_prices = {}
cumulative_price = 0

for tier_name, companies in tiers.items():
    price = calculate_price(companies, portfolio, initial_entropy, baseline_wealth, performance_ratio, commission_percentage)
    cumulative_price += price
    cumulative_prices[tier_name] = cumulative_price
    print(f"The price for the {tier_name} tier is: €{cumulative_price:.2f}")
