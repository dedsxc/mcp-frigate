"""
Main FastMCP server implementation for Frigate NVR.

This module contains the MCP server setup and tool definitions.
"""

from datetime import datetime
from typing import Any

import httpx
from fastmcp import FastMCP

from .config import FrigateConfig

# Initialize configuration
config = FrigateConfig()

# Create FastMCP server instance
mcp = FastMCP("Frigate NVR")


# HTTP client for Frigate API calls
async def get_frigate_client() -> httpx.AsyncClient:
    """
    Create an async HTTP client for Frigate API requests.
    
    Returns:
        Configured AsyncClient with base URL and headers
    """
    headers = {}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    
    return httpx.AsyncClient(
        base_url=config.api_base_url,
        headers=headers,
        timeout=config.timeout,
    )


@mcp.tool()
async def get_cameras() -> list[dict[str, Any]]:
    """
    Get the list of all cameras configured in Frigate.
    
    Returns a list of cameras with their names, status, and configuration details.
    
    Returns:
        List of camera objects with name, enabled status, and other properties
    """
    async with await get_frigate_client() as client:
        response = await client.get("/config")
        response.raise_for_status()
        data = response.json()
        
        # Extract camera information
        cameras = []
        for camera_name, camera_config in data.get("cameras", {}).items():
            cameras.append({
                "name": camera_name,
                "enabled": camera_config.get("enabled", True),
                "width": camera_config.get("detect", {}).get("width"),
                "height": camera_config.get("detect", {}).get("height"),
                "fps": camera_config.get("detect", {}).get("fps"),
            })
        
        return cameras


@mcp.tool()
async def get_events(
    camera: str | None = None,
    label: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Get recent detection events from Frigate.
    
    Retrieves events based on optional filters for camera and detected object label.
    
    Args:
        camera: Filter by specific camera name (optional)
        label: Filter by detected object label like 'person', 'car', 'dog' (optional)
        limit: Maximum number of events to return (default: 10, max: 100)
    
    Returns:
        List of event objects with detection details, timestamps, and thumbnails
    """
    # Validate limit
    limit = min(max(1, limit), 100)
    
    async with await get_frigate_client() as client:
        params: dict[str, Any] = {"limit": limit}
        
        if camera:
            params["camera"] = camera
        if label:
            params["label"] = label
        
        response = await client.get("/events", params=params)
        response.raise_for_status()
        events = response.json()
        
        # Format events for easier consumption
        formatted_events = []
        for event in events:
            formatted_events.append({
                "id": event.get("id"),
                "camera": event.get("camera"),
                "label": event.get("label"),
                "start_time": event.get("start_time"),
                "end_time": event.get("end_time"),
                "has_clip": event.get("has_clip", False),
                "has_snapshot": event.get("has_snapshot", False),
                "zone": event.get("zones", []),
                "thumbnail": f"{config.base_url}/api/events/{event.get('id')}/thumbnail.jpg"
                if event.get("has_snapshot")
                else None,
            })
        
        return formatted_events


@mcp.tool()
async def get_stats() -> dict[str, Any]:
    """
    Get Frigate system statistics and performance metrics.
    
    Returns information about CPU usage, memory, detector performance,
    camera FPS, and detection metrics.
    
    Returns:
        Dictionary containing system stats, detector info, and camera metrics
    """
    async with await get_frigate_client() as client:
        response = await client.get("/stats")
        response.raise_for_status()
        stats = response.json()
        
        # Extract key statistics
        summary = {
            "service": {
                "uptime": stats.get("service", {}).get("uptime"),
                "version": stats.get("service", {}).get("version"),
                "storage": stats.get("service", {}).get("storage"),
            },
            "detectors": {},
            "cameras": {},
        }
        
        # Detector stats
        for detector_name, detector_stats in stats.get("detectors", {}).items():
            summary["detectors"][detector_name] = {
                "inference_speed": detector_stats.get("inference_speed"),
                "detection_start": detector_stats.get("detection_start"),
            }
        
        # Camera stats
        for camera_name, camera_stats in stats.get("cameras", {}).items():
            summary["cameras"][camera_name] = {
                "camera_fps": camera_stats.get("camera_fps"),
                "process_fps": camera_stats.get("process_fps"),
                "detection_fps": camera_stats.get("detection_fps"),
            }
        
        return summary


@mcp.tool()
async def get_event_details(event_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific detection event.
    
    Retrieves comprehensive details including zones, thumbnails, clips,
    and timeline information for a single event.
    
    Args:
        event_id: The unique ID of the event to retrieve
    
    Returns:
        Dictionary with complete event details including media URLs
    """
    async with await get_frigate_client() as client:
        response = await client.get(f"/events/{event_id}")
        response.raise_for_status()
        event = response.json()
        
        # Format event details
        details = {
            "id": event.get("id"),
            "camera": event.get("camera"),
            "label": event.get("label"),
            "sub_label": event.get("sub_label"),
            "start_time": event.get("start_time"),
            "end_time": event.get("end_time"),
            "duration": (event.get("end_time", 0) - event.get("start_time", 0))
            if event.get("end_time")
            else None,
            "score": event.get("top_score"),
            "zones": event.get("zones", []),
            "has_clip": event.get("has_clip", False),
            "has_snapshot": event.get("has_snapshot", False),
            "retain_indefinitely": event.get("retain_indefinitely", False),
            "media": {
                "thumbnail": f"{config.base_url}/api/events/{event_id}/thumbnail.jpg",
                "snapshot": f"{config.base_url}/api/events/{event_id}/snapshot.jpg",
                "clip": f"{config.base_url}/api/events/{event_id}/clip.mp4"
                if event.get("has_clip")
                else None,
            },
        }
        
        return details


@mcp.tool()
async def get_snapshot(camera: str, timestamp: int | None = None) -> dict[str, str]:
    """
    Get a snapshot from a specific camera.
    
    Returns the URL to access a snapshot image from the camera,
    either current or from a specific timestamp.
    
    Args:
        camera: Name of the camera
        timestamp: Optional Unix timestamp for historical snapshot
    
    Returns:
        Dictionary with snapshot URL and metadata
    """
    # Build snapshot URL
    if timestamp:
        snapshot_url = f"{config.base_url}/api/{camera}/snapshot/{timestamp}.jpg"
    else:
        snapshot_url = f"{config.base_url}/api/{camera}/latest.jpg"
    
    # Verify camera exists
    async with await get_frigate_client() as client:
        response = await client.get("/config")
        response.raise_for_status()
        cameras = response.json().get("cameras", {})
        
        if camera not in cameras:
            available = list(cameras.keys())
            raise ValueError(
                f"Camera '{camera}' not found. Available cameras: {available}"
            )
    
    return {
        "camera": camera,
        "timestamp": timestamp or "latest",
        "url": snapshot_url,
        "description": f"Snapshot from {camera}"
        + (f" at timestamp {timestamp}" if timestamp else " (latest)"),
    }


@mcp.tool()
async def get_recordings(
    camera: str, date: str | None = None
) -> dict[str, Any]:
    """
    Get recording information for a specific camera.
    
    Retrieves the recording summary including available recordings
    and storage information for a camera on a specific date.
    
    Args:
        camera: Name of the camera
        date: Date in YYYY-MM-DD format (optional, defaults to today)
    
    Returns:
        Dictionary with recording summary and available segments
    """
    from datetime import datetime
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    async with await get_frigate_client() as client:
        # Get recording summary
        response = await client.get(f"/{camera}/recordings/summary")
        response.raise_for_status()
        summary = response.json()
        
        # Find recordings for the specified date
        recordings = []
        for item in summary:
            if item.get("day") == date:
                recordings.append({
                    "day": item.get("day"),
                    "hour": item.get("hour"),
                    "duration": item.get("duration"),
                    "events": item.get("events", 0),
                })
        
        return {
            "camera": camera,
            "date": date,
            "recordings_count": len(recordings),
            "recordings": recordings,
            "total_duration": sum(r.get("duration", 0) for r in recordings),
        }


@mcp.tool()
async def get_config() -> dict[str, Any]:
    """
    Get the complete Frigate configuration.
    
    Retrieves the full Frigate configuration including all cameras,
    detectors, motion settings, and system configuration.
    
    Returns:
        Complete Frigate configuration dictionary
    """
    async with await get_frigate_client() as client:
        response = await client.get("/config")
        response.raise_for_status()
        config_data = response.json()
        
        # Return a structured summary instead of the full config
        # (full config can be very large)
        summary = {
            "cameras": list(config_data.get("cameras", {}).keys()),
            "detectors": list(config_data.get("detectors", {}).keys()),
            "mqtt": {
                "enabled": "mqtt" in config_data,
                "host": config_data.get("mqtt", {}).get("host"),
            },
            "model": config_data.get("model", {}).get("path"),
            "version": config_data.get("version"),
            "full_config_available": True,
        }
        
        return summary


def main():
    """
    Entry point for the Frigate MCP server.
    
    Run this to start the server in stdio mode (for MCP clients like Claude Desktop).
    """
    mcp.run()


def serve_sse():
    """
    Start the Frigate MCP server in SSE (Server-Sent Events) mode.
    
    This allows the server to be accessed via HTTP with SSE for real-time updates.
    Useful for web-based clients and debugging.
    
    Server will be available at: http://{host}:{port}/sse
    """
    print(f"🚀 Starting Frigate MCP server in SSE mode...")
    print(f"📡 Server will be available at: http://{config.server_host}:{config.server_port}/sse")
    print(f"🔗 Frigate instance: {config.base_url}")
    print()
    
    # Run with SSE transport
    mcp.run(
        transport="sse",
        host=config.server_host,
        port=config.server_port,
    )


def serve_http():
    """
    Start the Frigate MCP server in HTTP streamable mode.
    
    This provides a standard HTTP interface with streaming support.
    Best for production deployments and API access.
    
    Server will be available at: http://{host}:{port}
    """
    print(f"🚀 Starting Frigate MCP server in HTTP mode...")
    print(f"📡 Server will be available at: http://{config.server_host}:{config.server_port}")
    print(f"🔗 Frigate instance: {config.base_url}")
    print()
    
    # Run with SSE transport (FastMCP's HTTP mode)
    mcp.run(
        transport="sse",
        host=config.server_host,
        port=config.server_port,
    )


if __name__ == "__main__":
    main()
