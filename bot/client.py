import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bot.logging_config import get_logger

logger = get_logger("BinanceFuturesClient")

class BinanceAPIError(Exception):
    """Custom exception for Binance API specific errors."""
    pass

class NetworkError(Exception):
    """Custom exception for networking errors communicating with Binance."""
    pass

class BinanceFuturesClient:
    BASE_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API Key and Secret must be provided.")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json"
        })
        
        # Setup retry strategy (3 retries for specific HTTP status codes)
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _sign_request(self, params: dict) -> dict:
        """Appends timestamp and signature to the parameters."""
        # Clean params by removing None values
        params = {k: v for k, v in params.items() if v is not None}
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params, doseq=True)
        params["signature"] = self._generate_signature(query_string)
        return params

    def _handle_response(self, response: requests.Response) -> dict:
        logger.info(f"Response: [{response.status_code}] {response.text}")
        
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                msg = f"Binance API Error {error_data.get('code')}: {error_data.get('msg')}"
                raise BinanceAPIError(msg) from e
            except ValueError:
                raise NetworkError(f"HTTP Error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}") from e

    def get(self, endpoint: str, params: dict = None, signed: bool = True) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        
        if signed:
            params = self._sign_request(params)
            
        logger.info(f"GET {url} - Params: {params}")
        
        try:
            response = self.session.get(url, params=params)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on GET {endpoint}: {e}")
            raise NetworkError(f"Network request failed: {e}")

    def post(self, endpoint: str, data: dict = None, signed: bool = True) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        data = data or {}
        
        if signed:
            data = self._sign_request(data)
            
        logger.info(f"POST {url} - Data: {data}")
        
        try:
            response = self.session.post(url, data=data)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on POST {endpoint}: {e}")
            raise NetworkError(f"Network request failed: {e}")

    def delete(self, endpoint: str, params: dict = None, signed: bool = True) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        
        if signed:
            params = self._sign_request(params)
            
        logger.info(f"DELETE {url} - Params: {params}")
        try:
            response = self.session.delete(url, params=params)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on DELETE {endpoint}: {e}")
            raise NetworkError(f"Network request failed: {e}")
