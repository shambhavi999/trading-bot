import os
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.orders import place_order
from bot.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Initialize Typer and Rich
app = typer.Typer(help="Binance Futures Testnet Trading Bot CLI")
console = Console()
logger = get_logger("CLI")

def get_client() -> BinanceFuturesClient:
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        console.print("[red]Error: API keys not found. Please setup .env file.[/red]")
        raise typer.Exit(1)
        
    return BinanceFuturesClient(api_key, api_secret)

def display_banner():
    banner = r"""[cyan]
  ____  _                             [white]____        _ [/white]
 |  _ \(_)                           [white]|  _ \      | |[/white]
 | |_) |_ _ __   __ _ _ __   ___ ___ [white]| |_) | ___ | |_[/white]
 |  _ <| | '_ \ / _` | '_ \ / __/ _ \ [white]|  _ < / _ \| __|[/white]
 | |_) | | | | | (_| | | | | (_|  __/ [white]| |_) | (_) | |_[/white]
 |____/|_|_| |_|\__,_|_| |_|\___\___| [white]|____/ \___/ \__|[/white]
   [green]Futures Testnet Edition[/green]
[/cyan]"""
    console.print(banner)

@app.callback()
def main(log_level: str = typer.Option("INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR)")):
    """Trading Bot CLI Management."""
    import logging
    setup_logging()
    get_logger("").setLevel(getattr(logging, log_level.upper(), logging.INFO))
    display_banner()

@app.command()
def ping():
    """Test connection to the Binance Testnet."""
    client = get_client()
    try:
        with console.status("[bold cyan]Pinging Binance Testnet..."):
            result = client.get("/fapi/v1/ping", signed=False)
        console.print(Panel("[green]Successfully connected to Binance Futures Testnet![/green]", title="Ping Result", border_style="green"))
    except Exception as e:
        console.print(Panel(f"[red]Failed to connect:[/red] {e}", title="Ping Result", border_style="red"))

@app.command()
def account():
    """Get account balance and information."""
    client = get_client()
    try:
        with console.status("[bold cyan]Fetching account details..."):
            data = client.get("/fapi/v2/account")
        
        balance_table = Table(title="Account Balances", style="cyan")
        balance_table.add_column("Asset", justify="left")
        balance_table.add_column("Wallet Balance", justify="right")
        balance_table.add_column("Unrealized PNL", justify="right")
        
        for asset in data.get("assets", []):
            if float(asset.get("walletBalance", 0)) > 0:
                balance_table.add_row(
                    asset.get("asset"),
                    asset.get("walletBalance"),
                    asset.get("unrealizedProfit")
                )
                
        console.print(balance_table)
    except Exception as e:
        console.print(f"[red]Error fetching account details: {e}[/red]")

@app.command()
def open_orders(symbol: str = typer.Option(None, help="Specific symbol to query")):
    """Get all open orders, optionally filtered by symbol."""
    client = get_client()
    try:
        params = {"symbol": symbol} if symbol else {}
        with console.status("[bold cyan]Fetching open orders..."):
            orders = client.get("/fapi/v1/openOrders", params=params)
            
        if not orders:
            console.print("[yellow]No open orders found.[/yellow]")
            return

        table = Table(title="Open Orders", style="cyan")
        table.add_column("Symbol")
        table.add_column("Order ID")
        table.add_column("Side")
        table.add_column("Type")
        table.add_column("Price")
        table.add_column("Qty")
        table.add_column("Status")
        
        for o in orders:
            side_color = "green" if o.get("side") == "BUY" else "red"
            table.add_row(
                o.get("symbol"),
                str(o.get("orderId")),
                f"[{side_color}]{o.get('side')}[/{side_color}]",
                o.get("type"),
                o.get("price"),
                o.get("origQty"),
                o.get("status")
            )
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching open orders: {e}[/red]")

@app.command()
def place(
    symbol: str = typer.Option(..., help="Trading pair symbol (e.g., BTCUSDT)"),
    side: str = typer.Option(..., help="BUY or SELL"),
    type: str = typer.Option(..., help="Order type: MARKET, LIMIT, STOP_MARKET"),
    qty: float = typer.Option(..., help="Quantity to trade"),
    price: float = typer.Option(None, help="Limit price (Required for LIMIT)"),
    stop_price: float = typer.Option(None, help="Stop price (Required for STOP_MARKET)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate order without hitting the API")
):
    """Place a new order on the Binance Futures Testnet."""
    if dry_run:
        client = None
        console.print(Panel("[yellow]DRY-RUN mode is ON. Simulating order...[/yellow]", border_style="yellow"))
    else:
        client = get_client()
        
    side = side.upper()
    
    # Request Summary Table
    req_table = Table(title="Order Request Summary", show_header=False)
    req_table.add_column("Field", style="cyan")
    req_table.add_column("Value")
    
    side_style = "green" if side == "BUY" else "red"
    req_table.add_row("Symbol", symbol.upper())
    req_table.add_row("Side", f"[{side_style}]{side}[/{side_style}]")
    req_table.add_row("Type", type.upper())
    req_table.add_row("Quantity", str(qty))
    if price: req_table.add_row("Price", str(price))
    if stop_price: req_table.add_row("Stop Price", str(stop_price))
    
    console.print(req_table)
    
    with console.status("[bold cyan]Submitting order..."):
        result = place_order(client, symbol, side, type, qty, price, stop_price, dry_run=dry_run)
        
    if result.success:
        res_table = Table(title="Order Placed Successfully", style="green")
        res_table.add_column("ID")
        res_table.add_column("Status")
        res_table.add_column("Executed Qty")
        res_table.add_column("Avg Price")
        
        res_table.add_row(
            str(result.order_id),
            result.status,
            result.executed_qty,
            result.avg_price
        )
        console.print(res_table)
        if result.dry_run:
            console.print("[yellow]DRY-RUN complete — no real order was sent.[/yellow]")
    else:
        console.print(Panel(f"[red]Error placing order:[/red]\n{result.error}", title="Order Failed", border_style="red"))

if __name__ == "__main__":
    app()
