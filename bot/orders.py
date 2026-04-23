from dataclasses import dataclass
from typing import Optional, Any
from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.validators import validate_order_inputs
from bot.logging_config import get_logger

logger = get_logger("Orders")

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[int]
    client_order_id: Optional[str]
    status: Optional[str]
    executed_qty: Optional[str]
    avg_price: Optional[str]
    error: Optional[str]
    raw_response: Optional[dict]
    dry_run: bool = False

    def summary(self) -> dict:
        return {
            "success": self.success,
            "order_id": self.order_id,
            "client_order_id": self.client_order_id,
            "status": self.status,
            "executed_qty": self.executed_qty,
            "avg_price": self.avg_price,
            "error": self.error,
            "dryRun": self.dry_run,
        }

import random
import time

def _mock_response(symbol: str, side: str, order_type: str, quantity: str, price: str = None) -> dict:
    time.sleep(0.3)
    order_id = random.randint(4000000000, 4999999999)
    status = "FILLED" if order_type == "MARKET" else "NEW"
    executed_qty = quantity if order_type == "MARKET" else "0"
    mock_prices = {"BTCUSDT": 43250.50, "ETHUSDT": 2280.75, "BNBUSDT": 315.40}
    avg_price = str(mock_prices.get(symbol, 100.00)) if order_type == "MARKET" else "0"
    
    logger.info(f"[DRY-RUN] Simulating order response for {order_type} {side} {symbol}")
    return {
        "orderId": order_id,
        "clientOrderId": f"dryrun_{order_id}",
        "status": status,
        "executedQty": executed_qty,
        "avgPrice": avg_price
    }

def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
    stop_price: float = None,
    dry_run: bool = False
) -> OrderResult:
    """Core function to validate inputs and place an order."""
    
    try:
        validated = validate_order_inputs(symbol, side, order_type, quantity, price, stop_price)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        return OrderResult(
            success=False, order_id=None, client_order_id=None, status=None,
            executed_qty=None, avg_price=None, error=str(e), raw_response=None
        )

    endpoint = "/fapi/v1/order"
    
    payload = {
        "symbol": validated["symbol"],
        "side": validated["side"],
        "type": validated["type"],
        "quantity": format(validated["quantity"], 'f'),
    }

    if validated["type"] == "LIMIT":
        payload["timeInForce"] = "GTC"
        payload["price"] = format(validated["price"], 'f')
        
    if validated["type"] == "STOP_MARKET":
        payload["stopPrice"] = format(validated["stopPrice"], 'f')

    logger.info(f"Placing {validated['type']} order: {payload}")

    if dry_run:
        logger.info(f"[DRY-RUN] Intercepted {validated['type']} order: {payload}")
        qty_str = format(validated["quantity"], 'f')
        price_str = format(validated["price"], 'f') if validated.get("price") else None
        response = _mock_response(validated["symbol"], validated["side"], validated["type"], qty_str, price=price_str)
        logger.info(f"[DRY-RUN] Order successfully simulated. ID: {response.get('orderId')}")
        
        return OrderResult(
            success=True,
            order_id=response.get("orderId"),
            client_order_id=response.get("clientOrderId"),
            status=response.get("status"),
            executed_qty=response.get("executedQty"),
            avg_price=response.get("avgPrice"),
            error=None,
            raw_response=response,
            dry_run=True
        )

    try:
        response = client.post(endpoint, data=payload)
        logger.info(f"Order successfully placed. ID: {response.get('orderId')}")
        
        return OrderResult(
            success=True,
            order_id=response.get("orderId"),
            client_order_id=response.get("clientOrderId"),
            status=response.get("status"),
            executed_qty=response.get("executedQty"),
            avg_price=response.get("avgPrice"),
            error=None,
            raw_response=response,
            dry_run=False
        )
    except (BinanceAPIError, NetworkError) as e:
        logger.error(f"Failed to place order: {e}")
        return OrderResult(
            success=False, order_id=None, client_order_id=None, status=None,
            executed_qty=None, avg_price=None, error=str(e), raw_response=None,
            dry_run=False
        )

def place_market_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: float, dry_run: bool = False) -> OrderResult:
    return place_order(client, symbol, side, "MARKET", quantity, dry_run=dry_run)

def place_limit_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: float, price: float, dry_run: bool = False) -> OrderResult:
    return place_order(client, symbol, side, "LIMIT", quantity, price=price, dry_run=dry_run)

def place_stop_market_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: float, stop_price: float, dry_run: bool = False) -> OrderResult:
    return place_order(client, symbol, side, "STOP_MARKET", quantity, stop_price=stop_price, dry_run=dry_run)
