"""Setup script for Investment Market Simulator v0.1"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="investment-market-simulator",
    version="0.1.0",
    author="Investment Simulator Contributors",
    description="A comprehensive financial market simulation framework with blockchain integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/investment-market-simulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "scipy>=1.10.0",
        "cryptography>=41.0.0",
        "aiohttp>=3.8.0",
        "websockets>=11.0",
        "requests>=2.31.0",
        "flask>=2.3.0",
        "plotly>=5.14.0",
        "networkx>=3.1",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
        "ethereum": [
            "web3>=6.5.0",
            "eth-account>=0.9.0",
            "eth-utils>=2.2.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "tensorflow>=2.13.0",
            "torch>=2.0.0",
        ],
        "distributed": [
            "pyzmq>=25.0.0",
            "grpcio>=1.54.0",
            "grpcio-tools>=1.54.0",
            "protobuf>=4.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "market-sim=market_sim.cli:main",
        ],
    },
) 