# ⚡ PrimeTrade — Binance Futures Testnet Bot

A Python trading bot for Binance Futures Testnet (USDT-M).

## Features
- Market, Limit, Stop-Market orders via CLI
- Web dashboard (dashboard/index.html)
- Dry-run mode for safe testing (no API keys needed)
- Structured JSON logging
- Flask REST API backend

## Setup
pip install -r requirements.txt

## Run CLI
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001 --dry-run

## Run Dashboard
python server.py
Then open dashboard/index.html in browser
