"""
Smart contract interfaces for market trading.

This module provides Python interfaces to Solidity smart contracts
for decentralized trading and settlement.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ContractABI:
    """Container for smart contract ABI and bytecode."""
    name: str
    abi: List[Dict]
    bytecode: str
    

# Placeholder ABIs - in production these would be generated from Solidity
TRADING_CONTRACT_ABI = {
    "name": "TradingContract",
    "abi": [
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "string", "name": "_asset", "type": "string"},
                {"internalType": "uint256", "name": "_quantity", "type": "uint256"},
                {"internalType": "uint256", "name": "_price", "type": "uint256"}
            ],
            "name": "placeBuyOrder",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "string", "name": "_asset", "type": "string"},
                {"internalType": "uint256", "name": "_quantity", "type": "uint256"},
                {"internalType": "uint256", "name": "_price", "type": "uint256"}
            ],
            "name": "placeSellOrder",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "orderId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "trader", "type": "address"},
                {"indexed": False, "internalType": "string", "name": "asset", "type": "string"},
                {"indexed": False, "internalType": "uint256", "name": "quantity", "type": "uint256"},
                {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"}
            ],
            "name": "OrderPlaced",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "tradeId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "buyer", "type": "address"},
                {"indexed": True, "internalType": "address", "name": "seller", "type": "address"},
                {"indexed": False, "internalType": "uint256", "name": "quantity", "type": "uint256"},
                {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"}
            ],
            "name": "TradeExecuted",
            "type": "event"
        }
    ],
    "bytecode": "0x608060405234801561001057600080fd5b50..."  # Placeholder
}


SETTLEMENT_CONTRACT_ABI = {
    "name": "SettlementContract",
    "abi": [
        {
            "inputs": [
                {"internalType": "uint256", "name": "_tradeId", "type": "uint256"},
                {"internalType": "address", "name": "_buyer", "type": "address"},
                {"internalType": "address", "name": "_seller", "type": "address"},
                {"internalType": "uint256", "name": "_amount", "type": "uint256"}
            ],
            "name": "settleTrade",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "_tradeId", "type": "uint256"}],
            "name": "getSettlementStatus",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "tradeId", "type": "uint256"},
                {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
            ],
            "name": "TradeSettled",
            "type": "event"
        }
    ],
    "bytecode": "0x608060405234801561001057600080fd5b50..."  # Placeholder
}


class TradingContract:
    """
    Python interface for the Trading smart contract.
    """
    
    def __init__(self, eth_integration, contract_address: str = None):
        self.eth = eth_integration
        self.address = contract_address
        self.abi = TRADING_CONTRACT_ABI["abi"]
        
    def deploy(self) -> str:
        """Deploy the trading contract."""
        return self.eth.deploy_contract(
            self.abi,
            TRADING_CONTRACT_ABI["bytecode"]
        )
        
    def place_buy_order(self, asset: str, quantity: int, price: int) -> Optional[str]:
        """Place a buy order on the blockchain."""
        return self.eth.send_contract_transaction(
            self.address,
            "placeBuyOrder",
            [asset, quantity, price]
        )
        
    def place_sell_order(self, asset: str, quantity: int, price: int) -> Optional[str]:
        """Place a sell order on the blockchain."""
        return self.eth.send_contract_transaction(
            self.address,
            "placeSellOrder",
            [asset, quantity, price]
        )
        
    def get_order_events(self, from_block: int = 0) -> List[Dict]:
        """Get all OrderPlaced events."""
        return self.eth.get_events(self.address, "OrderPlaced", from_block)
        
    def get_trade_events(self, from_block: int = 0) -> List[Dict]:
        """Get all TradeExecuted events."""
        return self.eth.get_events(self.address, "TradeExecuted", from_block)


class SettlementContract:
    """
    Python interface for the Settlement smart contract.
    """
    
    def __init__(self, eth_integration, contract_address: str = None):
        self.eth = eth_integration
        self.address = contract_address
        self.abi = SETTLEMENT_CONTRACT_ABI["abi"]
        
    def deploy(self) -> str:
        """Deploy the settlement contract."""
        return self.eth.deploy_contract(
            self.abi,
            SETTLEMENT_CONTRACT_ABI["bytecode"]
        )
        
    def settle_trade(self, trade_id: int, buyer: str, seller: str, 
                    amount: int) -> Optional[str]:
        """Settle a trade on the blockchain."""
        return self.eth.send_contract_transaction(
            self.address,
            "settleTrade",
            [trade_id, buyer, seller, amount]
        )
        
    def is_settled(self, trade_id: int) -> bool:
        """Check if a trade has been settled."""
        return self.eth.call_contract_function(
            self.address,
            "getSettlementStatus",
            [trade_id]
        )
        
    def get_settlement_events(self, from_block: int = 0) -> List[Dict]:
        """Get all TradeSettled events."""
        return self.eth.get_events(self.address, "TradeSettled", from_block)


# Solidity contract templates (for reference)
TRADING_CONTRACT_SOLIDITY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TradingContract {
    address public owner;
    uint256 public orderCounter;
    uint256 public tradeCounter;
    
    struct Order {
        address trader;
        string asset;
        uint256 quantity;
        uint256 price;
        bool isBuy;
        bool isActive;
    }
    
    mapping(uint256 => Order) public orders;
    
    event OrderPlaced(uint256 indexed orderId, address indexed trader, 
                     string asset, uint256 quantity, uint256 price);
    event TradeExecuted(uint256 indexed tradeId, address indexed buyer, 
                       address indexed seller, uint256 quantity, uint256 price);
    
    constructor() {
        owner = msg.sender;
    }
    
    function placeBuyOrder(string memory _asset, uint256 _quantity, 
                          uint256 _price) public returns (uint256) {
        // Implementation would go here
        return orderCounter++;
    }
    
    function placeSellOrder(string memory _asset, uint256 _quantity, 
                           uint256 _price) public returns (uint256) {
        // Implementation would go here
        return orderCounter++;
    }
}
"""

SETTLEMENT_CONTRACT_SOLIDITY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SettlementContract {
    mapping(uint256 => bool) public settledTrades;
    
    event TradeSettled(uint256 indexed tradeId, uint256 timestamp);
    
    function settleTrade(uint256 _tradeId, address _buyer, 
                        address _seller, uint256 _amount) public returns (bool) {
        // Implementation would transfer assets/tokens
        settledTrades[_tradeId] = true;
        emit TradeSettled(_tradeId, block.timestamp);
        return true;
    }
    
    function getSettlementStatus(uint256 _tradeId) public view returns (bool) {
        return settledTrades[_tradeId];
    }
}
""" 