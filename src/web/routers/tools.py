"""Domain Tools Router - Weather, Finance, Routing"""

import json

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from src.utils import get_config, get_logger
from src.llm import LLMManager
from src.tools import WeatherTool, FinanceTool, RoutingTool
from src.web import database
from src.web.dependencies.formatters import convert_markdown_to_html

logger = get_logger(__name__)

router = APIRouter()

# Global instances
config = None
llm_manager = None
weather_tool = None
finance_tool = None
routing_tool = None


async def initialize_tools():
    """Initialize domain tools"""
    global config, llm_manager, weather_tool, finance_tool, routing_tool

    if weather_tool is None or finance_tool is None or routing_tool is None:
        try:
            config = get_config()
            llm_manager = LLMManager(config=config)

            # Initialize Weather Tool
            if config.domain_tools.weather.enabled:
                try:
                    weather_tool = WeatherTool(api_key=config.domain_tools.weather.api_key)
                    logger.info("WeatherTool initialized successfully")
                except Exception as e:
                    logger.warning(f"WeatherTool initialization failed (optional): {e}")
                    weather_tool = None
            else:
                logger.info("WeatherTool disabled in config")
                weather_tool = None

            # Initialize Finance Tool
            if config.domain_tools.finance.enabled:
                try:
                    finance_tool = FinanceTool(alpha_vantage_key=config.domain_tools.finance.alpha_vantage_key)
                    logger.info("FinanceTool initialized successfully")
                except Exception as e:
                    logger.warning(f"FinanceTool initialization failed (optional): {e}")
                    finance_tool = None
            else:
                logger.info("FinanceTool disabled in config")
                finance_tool = None

            # Initialize Routing Tool
            if config.domain_tools.routing.enabled:
                try:
                    routing_tool = RoutingTool(api_key=config.domain_tools.routing.api_key)
                    logger.info("RoutingTool initialized successfully")
                except Exception as e:
                    logger.warning(f"RoutingTool initialization failed (optional): {e}")
                    routing_tool = None
            else:
                logger.info("RoutingTool disabled in config")
                routing_tool = None

            if not (weather_tool or finance_tool or routing_tool):
                logger.error("No domain tools available")
                raise RuntimeError("No domain tools could be initialized")

        except Exception as e:
            logger.error(f"Error initializing domain tools: {e}")
            raise


@router.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request):
    """Render tools page"""
    templates = request.app.state.templates

    # Initialize tools to check availability
    try:
        await initialize_tools()
    except Exception as e:
        logger.warning(f"Failed to initialize tools: {e}")

    return templates.TemplateResponse(
        "pages/tools.html",
        {
            "request": request,
            "breadcrumb_section": "Domain Tools",
            "weather_available": weather_tool is not None,
            "finance_available": finance_tool is not None,
            "routing_available": routing_tool is not None,
        },
    )


@router.post("/tools/weather", response_class=HTMLResponse)
async def get_weather(
    request: Request,
    location: str = ...,
    include_forecast: bool = False,
):
    """
    Get weather information for a location

    Args:
        location: City name or location (e.g., "London", "New York")
        include_forecast: Include 7-day forecast
    """
    await initialize_tools()

    if weather_tool is None:
        raise HTTPException(status_code=503, detail="Weather tool not available")

    templates = request.app.state.templates

    try:
        logger.info(f"Getting weather for: {location}")

        # Get weather data
        weather_result = await weather_tool.get_weather(
            location=location, include_forecast=include_forecast
        )

        # Format result
        result = {
            "location": weather_result.get("location", location),
            "temperature": weather_result.get("temperature", "N/A"),
            "feels_like": weather_result.get("feels_like", "N/A"),
            "condition": weather_result.get("condition", "N/A"),
            "humidity": weather_result.get("humidity", "N/A"),
            "wind_speed": weather_result.get("wind_speed", "N/A"),
            "pressure": weather_result.get("pressure", "N/A"),
            "uv_index": weather_result.get("uv_index", "N/A"),
            "visibility": weather_result.get("visibility", "N/A"),
            "forecast": weather_result.get("forecast", []),
        }

        # Create formatted markdown output
        markdown_output = f"""# 天气信息 (Weather Information)

## 当前天气 (Current Weather)

**位置**: {result['location']}

| 指标 | 数值 |
|------|------|
| 温度 | {result['temperature']} |
| 体感温度 | {result['feels_like']} |
| 天气 | {result['condition']} |
| 湿度 | {result['humidity']} |
| 风速 | {result['wind_speed']} |
| 气压 | {result['pressure']} |
| 紫外线指数 | {result['uv_index']} |
| 能见度 | {result['visibility']} |

"""

        if result["forecast"]:
            markdown_output += "## 7日预报 (7-Day Forecast)\n\n"
            markdown_output += "| 日期 | 天气 | 高温 | 低温 |\n|------|------|------|------|\n"
            for day in result["forecast"][:7]:
                markdown_output += f"| {day.get('date', 'N/A')} | {day.get('condition', 'N/A')} | {day.get('high', 'N/A')} | {day.get('low', 'N/A')} |\n"

        result["markdown"] = convert_markdown_to_html(markdown_output)

        # Save to conversation history
        await database.save_conversation(
            mode="weather",
            query=f"Weather: {location}",
            response=result["condition"],
            metadata=json.dumps(
                {
                    "location": result["location"],
                    "temperature": str(result["temperature"]),
                    "has_forecast": bool(result["forecast"]),
                }
            ),
        )

        return templates.TemplateResponse(
            "components/result_weather.html",
            {
                "request": request,
                "query": f"Weather in {location}",
                "result": result,
                "location": location,
            },
        )

    except Exception as e:
        logger.error(f"Error getting weather: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {"request": request, "error_message": f"Weather query failed: {str(e)}"},
        )


@router.post("/tools/finance", response_class=HTMLResponse)
async def get_stock_data(
    request: Request,
    symbol: str = ...,
    period: str = "1y",  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
):
    """
    Get financial data for a stock symbol

    Args:
        symbol: Stock symbol (e.g., "AAPL", "GOOGL")
        period: Time period for data
    """
    await initialize_tools()

    if finance_tool is None:
        raise HTTPException(status_code=503, detail="Finance tool not available")

    templates = request.app.state.templates

    try:
        logger.info(f"Getting stock data for: {symbol}")

        # Get stock data
        stock_result = await finance_tool.get_stock_data(
            symbol=symbol.upper(), period=period
        )

        # Format result
        result = {
            "symbol": stock_result.get("symbol", symbol.upper()),
            "company_name": stock_result.get("company_name", ""),
            "current_price": stock_result.get("current_price", "N/A"),
            "change": stock_result.get("change", "N/A"),
            "change_percent": stock_result.get("change_percent", "N/A"),
            "market_cap": stock_result.get("market_cap", "N/A"),
            "pe_ratio": stock_result.get("pe_ratio", "N/A"),
            "dividend_yield": stock_result.get("dividend_yield", "N/A"),
            "52_week_high": stock_result.get("52_week_high", "N/A"),
            "52_week_low": stock_result.get("52_week_low", "N/A"),
            "volume": stock_result.get("volume", "N/A"),
            "avg_volume": stock_result.get("avg_volume", "N/A"),
        }

        # Create formatted markdown output
        change_emoji = "📈" if float(str(result["change_percent"]).replace("%", "")) > 0 else "📉"
        markdown_output = f"""# 股票数据 (Stock Data)

## {result.get('company_name', result['symbol'])} ({result['symbol']})

### 价格信息 (Price Information)

| 指标 | 数值 |
|------|------|
| 当前价格 | ${result['current_price']} |
| 变化 | {change_emoji} {result['change']} ({result['change_percent']}) |
| 市值 | {result['market_cap']} |
| P/E比率 | {result['pe_ratio']} |
| 股息收益率 | {result['dividend_yield']} |

### 52周范围 (52-Week Range)

| 指标 | 数值 |
|------|------|
| 52周高点 | ${result['52_week_high']} |
| 52周低点 | ${result['52_week_low']} |

### 成交量 (Volume)

| 指标 | 数值 |
|------|------|
| 成交量 | {result['volume']} |
| 平均成交量 | {result['avg_volume']} |

"""

        result["markdown"] = convert_markdown_to_html(markdown_output)

        # Save to conversation history
        await database.save_conversation(
            mode="finance",
            query=f"Stock: {symbol}",
            response=f"{result['symbol']}: ${result['current_price']}",
            metadata=json.dumps(
                {
                    "symbol": result["symbol"],
                    "price": str(result["current_price"]),
                    "change_percent": str(result["change_percent"]),
                }
            ),
        )

        return templates.TemplateResponse(
            "components/result_finance.html",
            {
                "request": request,
                "query": f"Stock: {symbol}",
                "result": result,
                "symbol": symbol.upper(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting stock data: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": f"Finance query failed: {str(e)}",
            },
        )


@router.post("/tools/routing", response_class=HTMLResponse)
async def get_route(
    request: Request,
    origin: str = ...,
    destination: str = ...,
    mode: str = "driving",  # driving, walking, cycling, foot-walking
):
    """
    Get route information between two locations

    Args:
        origin: Starting location (address or coordinates)
        destination: Destination location (address or coordinates)
        mode: Travel mode (driving, walking, cycling, foot-walking)
    """
    await initialize_tools()

    if routing_tool is None:
        raise HTTPException(status_code=503, detail="Routing tool not available")

    templates = request.app.state.templates

    try:
        logger.info(f"Getting route from {origin} to {destination}")

        # Get route data
        route_result = await routing_tool.get_route(
            origin=origin, destination=destination, mode=mode
        )

        # Format result
        result = {
            "origin": route_result.get("origin", origin),
            "destination": route_result.get("destination", destination),
            "mode": mode,
            "distance": route_result.get("distance", "N/A"),
            "duration": route_result.get("duration", "N/A"),
            "polyline": route_result.get("polyline", ""),
            "steps": route_result.get("steps", []),
        }

        # Create formatted markdown output
        mode_emoji = {"driving": "🚗", "walking": "🚶", "cycling": "🚴", "foot-walking": "🚶"}.get(mode, "🛣️")
        markdown_output = f"""# 路线规划 (Route Information)

## {mode_emoji} {mode.upper()}

**起点**: {result['origin']}
**终点**: {result['destination']}

### 路线信息 (Route Details)

| 信息 | 数值 |
|------|------|
| 距离 | {result['distance']} |
| 预计时间 | {result['duration']} |
| 出行方式 | {mode} |

"""

        if result["steps"]:
            markdown_output += "### 导航步骤 (Navigation Steps)\n\n"
            for i, step in enumerate(result["steps"][:10], 1):
                instruction = step.get("instruction", "")
                distance = step.get("distance", "")
                duration = step.get("duration", "")
                markdown_output += f"{i}. {instruction} ({distance}, {duration})\n"
            if len(result["steps"]) > 10:
                markdown_output += f"\n... 还有 {len(result['steps']) - 10} 步 ...\n"

        result["markdown"] = convert_markdown_to_html(markdown_output)

        # Save to conversation history
        await database.save_conversation(
            mode="routing",
            query=f"Route: {origin} → {destination}",
            response=f"{result['distance']}, {result['duration']}",
            metadata=json.dumps(
                {
                    "origin": result["origin"],
                    "destination": result["destination"],
                    "mode": mode,
                    "distance": str(result["distance"]),
                }
            ),
        )

        return templates.TemplateResponse(
            "components/result_routing.html",
            {
                "request": request,
                "query": f"Route: {origin} → {destination}",
                "result": result,
                "origin": origin,
                "destination": destination,
            },
        )

    except Exception as e:
        logger.error(f"Error getting route: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": f"Routing query failed: {str(e)}",
            },
        )


@router.get("/tools/status")
async def get_status():
    """Get domain tools status"""
    try:
        await initialize_tools()

        return JSONResponse(
            content={
                "weather_available": weather_tool is not None,
                "finance_available": finance_tool is not None,
                "routing_available": routing_tool is not None,
                "message": "Domain tools ready",
            }
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JSONResponse(
            content={
                "weather_available": False,
                "finance_available": False,
                "routing_available": False,
                "message": f"Error: {str(e)}",
            },
            status_code=503,
        )
