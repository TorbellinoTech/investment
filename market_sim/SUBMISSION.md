# Test Submission — Proof-of-Work Simulator

# BY MOMINA KANWAL

## How to Run

1. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   .venv\Scripts\activate     # Windows
Install dependencies:


pip install -r requirements.txt
pip install pytest matplotlib


Run tests:


pytest -q


Run visualization:


python -c "from market_sim.plot_chain import run_and_plot; run_and_plot()"