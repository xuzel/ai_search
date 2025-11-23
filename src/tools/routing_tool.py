"""Routing Tool - Get routes and travel information using OpenRouteService"""

from typing import Any, Dict, List, Optional, Tuple

import openrouteservice as ors

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RoutingTool:
    """Get routing and transportation information from OpenRouteService"""

    # Supported profiles
    PROFILES = [
        "driving-car",
        "driving-hgv",  # Heavy goods vehicle
        "cycling-regular",
        "cycling-road",
        "cycling-mountain",
        "cycling-electric",
        "foot-walking",
        "foot-hiking",
        "wheelchair",
    ]

    def __init__(
        self,
        api_key: str,
        default_profile: str = "driving-car",
    ):
        """
        Initialize Routing Tool

        Args:
            api_key: OpenRouteService API key
            default_profile: Default routing profile
        """
        if not api_key:
            raise ValueError("OpenRouteService API key is required")

        if default_profile not in self.PROFILES:
            raise ValueError(f"Invalid profile. Must be one of: {self.PROFILES}")

        self.api_key = api_key
        self.default_profile = default_profile

        try:
            self.client = ors.Client(key=api_key)
            logger.info(f"RoutingTool initialized (profile: {default_profile})")
        except Exception as e:
            logger.error(f"Failed to initialize RoutingTool: {e}")
            raise

    async def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        profile: Optional[str] = None,
        alternatives: int = 0,
    ) -> Dict[str, Any]:
        """
        Get route between two points

        Args:
            start: Start coordinates (lon, lat)
            end: End coordinates (lon, lat)
            profile: Routing profile (default: self.default_profile)
            alternatives: Number of alternative routes (0-3)

        Returns:
            Dict with route information
        """
        profile = profile or self.default_profile

        try:
            route = self.client.directions(
                coordinates=[start, end],
                profile=profile,
                format="geojson",
                instructions=True,
                alternative_routes={"target_count": alternatives} if alternatives > 0 else None,
            )

            # Extract main route
            main_route = route["features"][0]["properties"]
            segments = main_route["segments"][0]

            result = {
                "start": {"lon": start[0], "lat": start[1]},
                "end": {"lon": end[0], "lat": end[1]},
                "profile": profile,
                "distance_km": segments["distance"] / 1000,
                "duration_minutes": segments["duration"] / 60,
                "duration_hours": segments["duration"] / 3600,
                "steps": len(segments["steps"]),
                "instructions": [
                    {
                        "instruction": step["instruction"],
                        "distance_m": step["distance"],
                        "duration_s": step["duration"],
                    }
                    for step in segments["steps"]
                ],
            }

            # Add alternative routes if requested
            if alternatives > 0 and len(route["features"]) > 1:
                result["alternatives"] = []
                for alt_route in route["features"][1:]:
                    alt_segments = alt_route["properties"]["segments"][0]
                    result["alternatives"].append({
                        "distance_km": alt_segments["distance"] / 1000,
                        "duration_minutes": alt_segments["duration"] / 60,
                    })

            logger.info(
                f"Route calculated: {result['distance_km']:.2f}km, "
                f"{result['duration_minutes']:.0f}min ({profile})"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating route: {e}")
            return {
                "error": str(e),
                "start": start,
                "end": end,
            }

    async def geocode(self, address: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Convert address to coordinates

        Args:
            address: Address string
            limit: Maximum number of results

        Returns:
            List of geocoding results
        """
        try:
            results = self.client.pelias_search(text=address, size=limit)

            locations = []
            for feature in results["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]

                locations.append({
                    "address": props.get("label"),
                    "name": props.get("name"),
                    "country": props.get("country"),
                    "city": props.get("locality") or props.get("city"),
                    "lon": coords[0],
                    "lat": coords[1],
                    "confidence": props.get("confidence", 0),
                })

            logger.info(f"Geocoded '{address}': {len(locations)} results")
            return locations

        except Exception as e:
            logger.error(f"Error geocoding {address}: {e}")
            return []

    async def reverse_geocode(
        self,
        lon: float,
        lat: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Convert coordinates to address

        Args:
            lon: Longitude
            lat: Latitude

        Returns:
            Address information
        """
        try:
            result = self.client.pelias_reverse(point=(lon, lat))

            if result["features"]:
                feature = result["features"][0]
                props = feature["properties"]

                address_info = {
                    "address": props.get("label"),
                    "name": props.get("name"),
                    "country": props.get("country"),
                    "city": props.get("locality") or props.get("city"),
                    "street": props.get("street"),
                    "lon": lon,
                    "lat": lat,
                }

                logger.info(f"Reverse geocoded ({lon}, {lat}): {address_info['address']}")
                return address_info

            return None

        except Exception as e:
            logger.error(f"Error reverse geocoding ({lon}, {lat}): {e}")
            return None

    async def get_route_by_address(
        self,
        start_address: str,
        end_address: str,
        profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get route using addresses (with geocoding)

        Args:
            start_address: Starting address
            end_address: Destination address
            profile: Routing profile

        Returns:
            Dict with route information
        """
        # Geocode addresses
        start_results = await self.geocode(start_address, limit=1)
        end_results = await self.geocode(end_address, limit=1)

        if not start_results:
            return {"error": f"Could not geocode start address: {start_address}"}

        if not end_results:
            return {"error": f"Could not geocode end address: {end_address}"}

        # Get route
        start_coords = (start_results[0]["lon"], start_results[0]["lat"])
        end_coords = (end_results[0]["lon"], end_results[0]["lat"])

        result = await self.get_route(start_coords, end_coords, profile)

        # If routing failed with "Could not find routable point", try coordinate adjustment
        if "error" in result and "2010" in str(result.get("error")):
            logger.warning(f"Routing failed, attempting coordinate adjustment...")

            # Try adjusting coordinates
            adjusted_result = await self._retry_with_adjusted_coords(
                start_coords, end_coords, profile, result.get("error", "")
            )

            if adjusted_result and "error" not in adjusted_result:
                logger.info("Routing succeeded with adjusted coordinates")
                result = adjusted_result
                result["coordinate_adjusted"] = True

        # Add address info
        result["start_address"] = start_results[0]["address"]
        result["end_address"] = end_results[0]["address"]

        return result

    async def _retry_with_adjusted_coords(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        profile: Optional[str],
        error_msg: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retry routing with adjusted coordinates when original coordinates are not routable

        Strategy:
        1. Detect which coordinate failed (start=0, end=1)
        2. Generate offset points in 4 directions (N, S, E, W)
        3. Try routing with each offset
        4. Return first successful result

        Args:
            start_coords: Original start coordinates
            end_coords: Original end coordinates
            profile: Routing profile
            error_msg: Error message from failed routing

        Returns:
            Successful route result or None
        """
        # Parse error to find which coordinate failed
        failed_coord_idx = None
        if "coordinate 0" in str(error_msg).lower():
            failed_coord_idx = 0  # Start coordinate
        elif "coordinate 1" in str(error_msg).lower():
            failed_coord_idx = 1  # End coordinate
        else:
            # Can't determine, try both
            failed_coord_idx = None

        # Generate offset distances (in degrees, approximately meters)
        # 1 degree latitude ≈ 111km
        # offset_meters / 111000 = offset_degrees
        offsets_meters = [100, 200, 500, 1000]  # Try progressively larger offsets
        offsets_degrees = [m / 111000 for m in offsets_meters]

        # Directions: [N, S, E, W]
        directions = [
            (0, 1),   # North (lat +)
            (0, -1),  # South (lat -)
            (1, 0),   # East (lon +)
            (-1, 0),  # West (lon -)
        ]

        # Generate candidate coordinates (smart strategy)
        candidates = []

        # If we know which coordinate failed, only adjust that one
        # Otherwise, adjust both but prioritize end coordinate (usually the problematic one)
        coords_to_adjust = []
        if failed_coord_idx == 0:
            coords_to_adjust = [(0, start_coords, end_coords, "start")]
        elif failed_coord_idx == 1:
            coords_to_adjust = [(1, start_coords, end_coords, "end")]
        else:
            # Unknown - try end first (more likely to be problematic), then start
            coords_to_adjust = [
                (1, start_coords, end_coords, "end"),
                (0, start_coords, end_coords, "start"),
            ]

        for coord_idx, start, end, coord_name in coords_to_adjust:
            for offset in offsets_degrees:
                for lon_dir, lat_dir in directions:
                    if coord_idx == 0:
                        # Adjust start
                        adjusted_start = (
                            start[0] + offset * lon_dir,
                            start[1] + offset * lat_dir,
                        )
                        candidates.append((adjusted_start, end, coord_name, offset * 111000))
                    else:
                        # Adjust end
                        adjusted_end = (
                            end[0] + offset * lon_dir,
                            end[1] + offset * lat_dir,
                        )
                        candidates.append((start, adjusted_end, coord_name, offset * 111000))

        # Try each candidate (max 16 attempts to avoid too many API calls)
        max_attempts = min(len(candidates), 16)
        logger.info(f"Trying {max_attempts} coordinate adjustments...")

        for i, (start, end, adjusted_type, offset_meters) in enumerate(candidates[:max_attempts]):
            try:
                result = await self.get_route(start, end, profile)

                if "error" not in result:
                    logger.info(
                        f"Success on attempt {i+1}/{max_attempts} "
                        f"(adjusted {adjusted_type} coordinate by ~{int(offset_meters)}m)"
                    )
                    # Add metadata about adjustment
                    result["adjustment_info"] = {
                        "adjusted_coordinate": adjusted_type,
                        "offset_meters": int(offset_meters),
                        "note": f"Coordinate adjusted by approximately {int(offset_meters)}m to find routable point"
                    }
                    return result

            except Exception as e:
                # Continue trying other candidates
                continue

        logger.warning("All coordinate adjustment attempts failed")
        return None

    def format_route_summary(self, route_data: Dict[str, Any]) -> str:
        """
        Format route data into human-readable summary

        Args:
            route_data: Route data from get_route

        Returns:
            Formatted summary string
        """
        if "error" in route_data:
            return f"无法计算路线: {route_data['error']}"

        # Format duration
        duration_min = route_data["duration_minutes"]
        if duration_min < 60:
            duration_str = f"{duration_min:.0f} 分钟"
        else:
            hours = int(duration_min // 60)
            minutes = int(duration_min % 60)
            duration_str = f"{hours} 小时 {minutes} 分钟"

        summary = f"""🚗 路线信息 ({route_data['profile']})

📍 起点: {route_data.get('start_address', f"({route_data['start']['lon']}, {route_data['start']['lat']})")}
📍 终点: {route_data.get('end_address', f"({route_data['end']['lon']}, {route_data['end']['lat']})")}

📏 距离: {route_data['distance_km']:.2f} 公里
⏱️ 预计时间: {duration_str}
📋 路线步骤: {route_data['steps']} 步"""

        # Add coordinate adjustment note if applicable
        if route_data.get("coordinate_adjusted") or route_data.get("adjustment_info"):
            adjustment_info = route_data.get("adjustment_info", {})
            offset = adjustment_info.get("offset_meters", 0)
            coord_type = adjustment_info.get("adjusted_coordinate", "coordinate")
            summary += f"\n\n💡 注意: {coord_type.capitalize()} coordinate was adjusted by ~{offset}m to find a routable point."

        # Add alternative routes if available
        if route_data.get("alternatives"):
            summary += f"\n\n🔄 备选路线:"
            for i, alt in enumerate(route_data["alternatives"], 1):
                summary += f"\n   {i}. {alt['distance_km']:.2f}km, {alt['duration_minutes']:.0f}分钟"

        return summary
