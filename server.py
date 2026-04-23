import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from bot.client import BinanceFuturesClient, NetworkError, BinanceAPIError
from bot.orders import place_order
from bot.logging_config import setup_logging

# Load config and setup
load_dotenv()
setup_logging()

app = Flask(__name__)
# Enable CORS for all routes so the frontend can interact with it
CORS(app)

def get_client() -> BinanceFuturesClient:
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("API credentials not found on server")
    return BinanceFuturesClient(api_key, api_secret)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, ValueError):
        return jsonify({"error": str(e)}), 400
    if isinstance(e, (BinanceAPIError, NetworkError)):
        return jsonify({"error": str(e)}), 502
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/ping", methods=["GET"])
def api_ping():
    client = get_client()
    client.get("/fapi/v1/ping", signed=False)
    return jsonify({"status": "ok", "message": "Connected to Testnet"})

@app.route("/api/account", methods=["GET"])
def api_account():
    client = get_client()
    data = client.get("/fapi/v2/account")
    return jsonify(data)

@app.route("/api/open-orders", methods=["GET"])
def api_open_orders():
    client = get_client()
    symbol = request.args.get("symbol")
    params = {"symbol": symbol} if symbol else {}
    data = client.get("/fapi/v1/openOrders", params=params)
    return jsonify(data)

@app.route("/api/order", methods=["POST"])
def api_place_order():
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
        
    dry_run = request.args.get("dry_run", "false").lower() == "true" or data.get("dryRun", False)
    
    try:
        client = None if dry_run else get_client()
    except ValueError as e:
        if not dry_run:
            raise e
        client = None
        
    result = place_order(
        client=client,
        symbol=data.get("symbol"),
        side=data.get("side"),
        order_type=data.get("type"),
        quantity=data.get("quantity"),
        price=data.get("price"),
        stop_price=data.get("stopPrice"),
        dry_run=dry_run
    )
    
    if result.success:
        return jsonify({"message": "Order placed", "result": result.raw_response, "dryRun": result.dry_run}), 200
    else:
        return jsonify({"error": result.error}), 400

@app.route("/api/cancel-order", methods=["DELETE"])
def api_cancel_order():
    symbol = request.args.get("symbol")
    order_id = request.args.get("orderId")
    if not symbol or not order_id:
        return jsonify({"error": "Missing symbol or orderId parameters"}), 400
        
    client = get_client()
    result = client.delete("/fapi/v1/order", params={"symbol": symbol, "orderId": order_id})
    return jsonify({"message": "Order canceled", "result": result})

@app.route("/api/logs", methods=["GET"])
def api_logs():
    lines = int(request.args.get("lines", 100))
    log_file = "logs/trading_bot.log"
    if not os.path.exists(log_file):
        return jsonify({"logs": []})
        
    # Read the last N lines (this is a simple implementation, for huge files you'd seek from end)
    with open(log_file, "r") as f:
        all_lines = f.readlines()
        
    recent_lines = all_lines[-lines:]
    logs = []
    for line in recent_lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
            
    return jsonify({"logs": logs})

if __name__ == "__main__":
    # Binding to 0.0.0.0 for broader local access
    app.run(host="0.0.0.0", port=5000, debug=True)
