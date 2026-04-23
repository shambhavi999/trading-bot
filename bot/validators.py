from decimal import Decimal, InvalidOperation

def validate_symbol(symbol: str):
    if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
        raise ValueError("Symbol must be a non-empty string.")
    return symbol.upper()

def validate_side(side: str):
    valid_sides = {"BUY", "SELL"}
    side_upper = side.upper()
    if side_upper not in valid_sides:
        raise ValueError(f"Side must be one of {valid_sides}.")
    return side_upper

def validate_order_type(order_type: str):
    valid_types = {"MARKET", "LIMIT", "STOP_MARKET"}
    type_upper = order_type.upper()
    if type_upper not in valid_types:
        raise ValueError(f"Order type must be one of {valid_types}.")
    return type_upper

def validate_quantity(quantity: str | float):
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError("Quantity must be a valid numeric value.")
    
    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    return qty

def validate_price(price: str | float | None, order_type: str):
    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        try:
            p = Decimal(str(price))
            if p <= 0:
                raise ValueError("Price must be greater than zero.")
            return p
        except InvalidOperation:
            raise ValueError("Price must be a valid numeric value.")
    return None

def validate_stop_price(stop_price: str | float | None, order_type: str):
    if order_type == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        try:
            sp = Decimal(str(stop_price))
            if sp <= 0:
                raise ValueError("Stop price must be greater than zero.")
            return sp
        except InvalidOperation:
            raise ValueError("Stop price must be a valid numeric value.")
    return None

def validate_order_inputs(symbol: str, side: str, order_type: str, quantity: float, price: float = None, stop_price: float = None):
    """Composite validator for all order inputs."""
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }
    
    validated["price"] = validate_price(price, validated["type"])
    validated["stopPrice"] = validate_stop_price(stop_price, validated["type"])
    
    return validated
