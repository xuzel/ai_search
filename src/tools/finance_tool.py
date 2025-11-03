"""Finance Tool - Fetch stock and financial data"""

from typing import Any, Dict, Optional

import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from tenacity import retry, stop_after_attempt, wait_fixed

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FinanceTool:
    """Fetch financial data with Alpha Vantage (primary) and yfinance (fallback)"""

    def __init__(
        self,
        alpha_vantage_key: Optional[str] = None,
        cache_ttl: int = 300,
    ):
        """
        Initialize Finance Tool

        Args:
            alpha_vantage_key: Alpha Vantage API key (optional)
            cache_ttl: Cache time-to-live in seconds
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.cache_ttl = cache_ttl

        # Initialize Alpha Vantage if key provided
        if alpha_vantage_key:
            try:
                self.alpha_vantage = TimeSeries(
                    key=alpha_vantage_key, output_format="pandas"
                )
                logger.info("FinanceTool initialized with Alpha Vantage")
            except Exception as e:
                logger.warning(f"Alpha Vantage initialization failed: {e}")
                self.alpha_vantage = None
        else:
            self.alpha_vantage = None
            logger.info("FinanceTool initialized with yfinance only (no Alpha Vantage key)")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price with automatic fallback

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")

        Returns:
            Dict with stock price information
        """
        # Try Alpha Vantage first
        if self.alpha_vantage:
            try:
                data, meta_data = self.alpha_vantage.get_quote_endpoint(symbol)

                result = {
                    "symbol": symbol,
                    "price": float(data["05. price"].iloc[0]),
                    "change": float(data["09. change"].iloc[0]),
                    "change_percent": data["10. change percent"].iloc[0],
                    "volume": int(data["06. volume"].iloc[0]),
                    "open": float(data["02. open"].iloc[0]),
                    "high": float(data["03. high"].iloc[0]),
                    "low": float(data["04. low"].iloc[0]),
                    "previous_close": float(data["08. previous close"].iloc[0]),
                    "source": "alpha_vantage",
                }

                logger.info(
                    f"Stock {symbol}: ${result['price']} ({result['change_percent']}) [Alpha Vantage]"
                )
                return result

            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {symbol}: {e}, falling back to yfinance")

        # Fallback to yfinance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

            if current_price is None:
                raise ValueError(f"No price data available for {symbol}")

            # Calculate change
            change = current_price - previous_close if previous_close else None
            change_percent = (
                f"{(change / previous_close * 100):.2f}%"
                if change and previous_close
                else "N/A"
            )

            result = {
                "symbol": symbol,
                "price": current_price,
                "change": change,
                "change_percent": change_percent,
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "previous_close": previous_close,
                "market_cap": info.get("marketCap"),
                "company_name": info.get("longName") or info.get("shortName"),
                "source": "yfinance",
            }

            logger.info(
                f"Stock {symbol}: ${result['price']} ({result['change_percent']}) [yfinance]"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch stock price for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "price": None,
            }

    async def get_stock_history(
        self,
        symbol: str,
        period: str = "1mo",
    ) -> Dict[str, Any]:
        """
        Get historical stock data (yfinance only)

        Args:
            symbol: Stock ticker symbol
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            Dict with historical data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                raise ValueError(f"No historical data for {symbol}")

            # Convert to records
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })

            result = {
                "symbol": symbol,
                "period": period,
                "data_points": len(records),
                "history": records,
                "latest_price": records[-1]["close"] if records else None,
            }

            logger.info(f"Historical data for {symbol}: {len(records)} data points ({period})")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "history": [],
            }

    async def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get cryptocurrency price (yfinance)

        Args:
            symbol: Crypto symbol (e.g., "BTC-USD", "ETH-USD")

        Returns:
            Dict with crypto price information
        """
        # Ensure symbol has -USD suffix
        if "-USD" not in symbol and "-" not in symbol:
            symbol = f"{symbol}-USD"

        return await self.get_stock_price(symbol)

    async def compare_stocks(
        self,
        symbols: list[str],
    ) -> Dict[str, Any]:
        """
        Compare multiple stocks side by side

        Args:
            symbols: List of stock symbols

        Returns:
            Dict with comparison data
        """
        comparison = {
            "symbols": symbols,
            "data": {},
        }

        for symbol in symbols:
            stock_data = await self.get_stock_price(symbol)
            comparison["data"][symbol] = stock_data

        logger.info(f"Compared {len(symbols)} stocks")
        return comparison

    def format_stock_summary(self, stock_data: Dict[str, Any]) -> str:
        """
        Format stock data into human-readable summary

        Args:
            stock_data: Stock data from get_stock_price

        Returns:
            Formatted summary string
        """
        if "error" in stock_data:
            return f"无法获取 {stock_data['symbol']} 的股价信息: {stock_data['error']}"

        symbol = stock_data["symbol"]
        price = stock_data["price"]
        change = stock_data.get("change")
        change_pct = stock_data.get("change_percent", "N/A")

        # Change indicator
        if change and change > 0:
            change_icon = "📈"
            change_str = f"+${change:.2f}"
        elif change and change < 0:
            change_icon = "📉"
            change_str = f"${change:.2f}"
        else:
            change_icon = "➡️"
            change_str = "$0.00"

        summary = f"""📊 {symbol}"""

        # Add company name if available
        if stock_data.get("company_name"):
            summary += f" - {stock_data['company_name']}"

        summary += f"""

💵 当前价格: ${price:.2f}
{change_icon} 涨跌: {change_str} ({change_pct})

📊 今日数据:
   开盘: ${stock_data.get('open', 'N/A'):.2f}
   最高: ${stock_data.get('high', 'N/A'):.2f}
   最低: ${stock_data.get('low', 'N/A'):.2f}
   昨收: ${stock_data.get('previous_close', 'N/A'):.2f}
   成交量: {stock_data.get('volume', 'N/A'):,}"""

        if stock_data.get("market_cap"):
            market_cap_b = stock_data["market_cap"] / 1e9
            summary += f"\n💰 市值: ${market_cap_b:.2f}B"

        summary += f"\n\n📡 数据来源: {stock_data['source']}"

        return summary
