"""
DeFi Protocol Adapter for market simulation.

This module provides integration with DeFi protocols for:
- Automated Market Makers (AMM)
- Lending/Borrowing protocols
- Yield farming strategies
- Liquidity provision
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeFiPool:
    """Represents a DeFi liquidity pool."""
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    fee: float = 0.003  # 0.3% typical for Uniswap
    
    def get_price(self, token: str) -> float:
        """Get the current price of a token in the pool."""
        if token == self.token_a:
            return self.reserve_b / self.reserve_a
        elif token == self.token_b:
            return self.reserve_a / self.reserve_b
        else:
            raise ValueError(f"Token {token} not in pool")
            
    def calculate_swap(self, token_in: str, amount_in: float) -> float:
        """Calculate output amount for a swap."""
        if token_in == self.token_a:
            # Swapping A for B
            amount_in_with_fee = amount_in * (1 - self.fee)
            amount_out = (self.reserve_b * amount_in_with_fee) / (self.reserve_a + amount_in_with_fee)
            return amount_out
        elif token_in == self.token_b:
            # Swapping B for A
            amount_in_with_fee = amount_in * (1 - self.fee)
            amount_out = (self.reserve_a * amount_in_with_fee) / (self.reserve_b + amount_in_with_fee)
            return amount_out
        else:
            raise ValueError(f"Token {token_in} not in pool")


class DeFiAdapter:
    """
    Adapter for integrating DeFi protocols with market simulation.
    """
    
    def __init__(self, eth_integration=None):
        self.eth = eth_integration
        self.pools: Dict[str, DeFiPool] = {}
        self.positions: Dict[str, Dict[str, float]] = {}  # user -> token -> amount
        
    def create_pool(self, pool_id: str, token_a: str, token_b: str, 
                   initial_a: float, initial_b: float) -> DeFiPool:
        """Create a new liquidity pool."""
        pool = DeFiPool(token_a, token_b, initial_a, initial_b)
        self.pools[pool_id] = pool
        logger.info(f"Created pool {pool_id}: {token_a}/{token_b} with reserves {initial_a}/{initial_b}")
        return pool
        
    def add_liquidity(self, pool_id: str, user: str, amount_a: float, amount_b: float) -> Dict[str, float]:
        """Add liquidity to a pool."""
        if pool_id not in self.pools:
            raise ValueError(f"Pool {pool_id} not found")
            
        pool = self.pools[pool_id]
        
        # Calculate LP tokens to mint (simplified)
        if pool.reserve_a == 0 and pool.reserve_b == 0:
            # First liquidity provider
            lp_tokens = (amount_a * amount_b) ** 0.5
        else:
            # Subsequent providers
            lp_tokens = min(
                amount_a * (pool.reserve_a + pool.reserve_b) / pool.reserve_a,
                amount_b * (pool.reserve_a + pool.reserve_b) / pool.reserve_b
            )
            
        # Update reserves
        pool.reserve_a += amount_a
        pool.reserve_b += amount_b
        
        # Track position
        if user not in self.positions:
            self.positions[user] = {}
        self.positions[user][f"{pool_id}_LP"] = self.positions[user].get(f"{pool_id}_LP", 0) + lp_tokens
        
        return {
            'lp_tokens': lp_tokens,
            'pool_share': lp_tokens / (pool.reserve_a + pool.reserve_b)
        }
        
    def swap(self, pool_id: str, user: str, token_in: str, amount_in: float) -> Dict[str, float]:
        """Perform a token swap."""
        if pool_id not in self.pools:
            raise ValueError(f"Pool {pool_id} not found")
            
        pool = self.pools[pool_id]
        amount_out = pool.calculate_swap(token_in, amount_in)
        
        # Update reserves
        if token_in == pool.token_a:
            pool.reserve_a += amount_in
            pool.reserve_b -= amount_out
            token_out = pool.token_b
        else:
            pool.reserve_b += amount_in
            pool.reserve_a -= amount_out
            token_out = pool.token_a
            
        # Update user positions
        if user not in self.positions:
            self.positions[user] = {}
        self.positions[user][token_in] = self.positions[user].get(token_in, 0) - amount_in
        self.positions[user][token_out] = self.positions[user].get(token_out, 0) + amount_out
        
        return {
            'token_out': token_out,
            'amount_out': amount_out,
            'price_impact': 1 - (amount_out * pool.get_price(token_in) / amount_in),
            'effective_price': amount_out / amount_in
        }
        
    def get_arbitrage_opportunity(self, token: str, pools: List[str]) -> Optional[Dict[str, Any]]:
        """Identify arbitrage opportunities across pools."""
        prices = {}
        for pool_id in pools:
            if pool_id in self.pools:
                pool = self.pools[pool_id]
                try:
                    prices[pool_id] = pool.get_price(token)
                except ValueError:
                    continue
                    
        if len(prices) < 2:
            return None
            
        min_pool = min(prices, key=prices.get)
        max_pool = max(prices, key=prices.get)
        
        price_diff = prices[max_pool] - prices[min_pool]
        profit_percent = (price_diff / prices[min_pool]) * 100
        
        if profit_percent > 0.1:  # 0.1% threshold
            return {
                'token': token,
                'buy_pool': min_pool,
                'sell_pool': max_pool,
                'buy_price': prices[min_pool],
                'sell_price': prices[max_pool],
                'profit_percent': profit_percent
            }
            
        return None
        
    def calculate_impermanent_loss(self, pool_id: str, initial_price: float) -> float:
        """Calculate impermanent loss for a liquidity position."""
        if pool_id not in self.pools:
            raise ValueError(f"Pool {pool_id} not found")
            
        pool = self.pools[pool_id]
        current_price = pool.get_price(pool.token_a)
        
        # IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        price_ratio = current_price / initial_price
        il = 2 * (price_ratio ** 0.5) / (1 + price_ratio) - 1
        
        return il * 100  # Return as percentage
        
    def simulate_yield_farming(self, user: str, pool_id: str, duration_blocks: int, 
                             reward_per_block: float) -> Dict[str, float]:
        """Simulate yield farming rewards."""
        if user not in self.positions:
            return {'error': 'No position found'}
            
        lp_balance = self.positions[user].get(f"{pool_id}_LP", 0)
        if lp_balance == 0:
            return {'error': 'No LP tokens found'}
            
        # Simple reward calculation
        total_rewards = lp_balance * reward_per_block * duration_blocks
        
        # Add rewards to position
        self.positions[user]['REWARD'] = self.positions[user].get('REWARD', 0) + total_rewards
        
        return {
            'lp_balance': lp_balance,
            'rewards_earned': total_rewards,
            'apy': (total_rewards / lp_balance) * (365 * 24 * 60 * 4) / duration_blocks * 100  # Assuming 15s blocks
        }
        
    def get_pool_analytics(self, pool_id: str) -> Dict[str, Any]:
        """Get analytics for a specific pool."""
        if pool_id not in self.pools:
            raise ValueError(f"Pool {pool_id} not found")
            
        pool = self.pools[pool_id]
        
        return {
            'pool_id': pool_id,
            'token_pair': f"{pool.token_a}/{pool.token_b}",
            'reserves': {
                pool.token_a: pool.reserve_a,
                pool.token_b: pool.reserve_b
            },
            'total_value_locked': pool.reserve_a + pool.reserve_b,  # Simplified
            'price': {
                pool.token_a: pool.get_price(pool.token_a),
                pool.token_b: pool.get_price(pool.token_b)
            },
            'fee': pool.fee * 100  # As percentage
        }


# Example DeFi strategies
class DeFiStrategies:
    """Common DeFi trading strategies."""
    
    @staticmethod
    def arbitrage_strategy(adapter: DeFiAdapter, capital: float) -> List[Dict]:
        """Execute arbitrage across multiple pools."""
        opportunities = []
        
        # Check all pools for arbitrage
        pool_ids = list(adapter.pools.keys())
        tokens = set()
        for pool in adapter.pools.values():
            tokens.add(pool.token_a)
            tokens.add(pool.token_b)
            
        for token in tokens:
            opp = adapter.get_arbitrage_opportunity(token, pool_ids)
            if opp:
                opportunities.append(opp)
                
        return opportunities
        
    @staticmethod
    def liquidity_provision_strategy(adapter: DeFiAdapter, user: str, 
                                   capital_a: float, capital_b: float) -> Dict:
        """Provide liquidity to the most profitable pool."""
        best_pool = None
        best_fee_income = 0
        
        for pool_id, pool in adapter.pools.items():
            # Estimate daily fee income
            daily_volume = (pool.reserve_a + pool.reserve_b) * 2  # Rough estimate
            pool_share = (capital_a + capital_b) / (pool.reserve_a + pool.reserve_b + capital_a + capital_b)
            daily_fees = daily_volume * pool.fee * pool_share
            
            if daily_fees > best_fee_income:
                best_fee_income = daily_fees
                best_pool = pool_id
                
        if best_pool:
            return adapter.add_liquidity(best_pool, user, capital_a, capital_b)
            
        return {'error': 'No suitable pool found'} 