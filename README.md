# Frigate MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [Frigate NVR](https://frigate.video/), enabling AI assistants to interact with your Frigate security camera system.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🌟 Features

- **Camera Management**: List and monitor all configured cameras
- **Event Detection**: Query detection events with filtering by camera, object type, and time
- **Live Snapshots**: Get current or historical camera snapshots
- **Recordings**: Access recording summaries and segments
- **System Stats**: Monitor Frigate performance, detector speed, and camera FPS
- **Configuration**: Retrieve complete Frigate configuration

## 📋 Prerequisites

- Python 3.10 or higher
- A running [Frigate NVR](https://frigate.video/) instance
- Access to the Frigate HTTP API

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/frigate-mcp.git
cd frigate-mcp
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Configure environment

Create a `.env` file in the project root:

```bash
# Required: URL of your Frigate instance
FRIGATE_FRIGATE_URL=http://localhost:5000

# Optional: API key if authentication is required
# FRIGATE_API_KEY=your_secret_key_here

# Optional: HTTP timeout in seconds (default: 30)
# FRIGATE_TIMEOUT=30
```

## 🔧 Configuration

The server uses environment variables for configuration. You can set them in:

1. **`.env` file** (recommended for development)
2. **Environment variables** (recommended for production)

### Configuration Options

| Variable              | Description                    | Default                 | Required |
| --------------------- | ------------------------------ | ----------------------- | -------- |
| `FRIGATE_FRIGATE_URL` | Base URL of Frigate instance   | `http://localhost:5000` | No       |
| `FRIGATE_API_KEY`     | API key for authentication     | None                    | No       |
| `FRIGATE_TIMEOUT`     | HTTP request timeout (seconds) | `30`                    | No       |
| `FRIGATE_SERVER_HOST` | Server host for SSE/HTTP modes | `0.0.0.0`               | No       |
| `FRIGATE_SERVER_PORT` | Server port for SSE/HTTP modes | `8000`                  | No       |

### Example Configurations

**Local Frigate instance:**
```bash
FRIGATE_FRIGATE_URL=http://localhost:5000
```

**Remote Frigate with authentication:**
```bash
FRIGATE_FRIGATE_URL=http://192.168.1.100:5000
FRIGATE_API_KEY=your_secret_key
FRIGATE_TIMEOUT=60
```

## 🎯 Usage

The server supports three operational modes:

### 1. STDIO Mode (Default)

For direct integration with MCP clients like Claude Desktop:

```bash
python -m frigate_mcp.server
# or
frigate-mcp
```

### 2. SSE Mode (Server-Sent Events)

For web-based clients with real-time updates:

```bash
frigate-mcp-sse
```

The server will start at `http://localhost:8000/sse` (configurable via environment variables).

**Features:**
- Real-time event streaming
- WebSocket-like experience over HTTP
- Easy to debug in browser dev tools
- Compatible with web applications

### 3. HTTP Mode (REST API)

For production deployments and API access:

**STDIO Mode** (for MCP clients):

```bash
python -m frigate_mcp.server
```

**SSE Mode** (for web clients):

```bash
frigate-mcp-sse
```

**HTTP Mode** (for REST API):

```bash
frigate-mcp-http
```

### Integrating with MCP Clients

#### Claude Desktop (STDIO Mode)
### Testing the Connection

Run the included test script to verify your Frigate connection:

```bash
python test_connection.py
```

Expected output:
```
============================================================
Frigate MCP Server - Connection Test
============================================================

🔧 Frigate Configuration:
   URL: http://localhost:5000
   API URL: http://localhost:5000/api
   Timeout: 30s

📹 Testing /api/config (cameras)...
   ✅ Found 1 camera(s)
      - front_door: enabled

📊 Testing /api/stats...
   ✅ Frigate version: 0.16.3
   ✅ Detectors: ['coral']
   ✅ Active cameras: ['front_door']
...
```

### Running the MCP Server

Start the server in stdio mode (for MCP clients):

```bash
python -m frigate_mcp.server
```

#### Claude Desktop (STDIO Mode)

Add to your MCP client configuration (e.g., Claude Desktop `config.json`):

```json
{
  "mcpServers": {
    "frigate": {
      "command": "/path/to/frigate-mcp/.venv/bin/python",
      "args": ["-m", "frigate_mcp.server"],
      "env": {
        "FRIGATE_FRIGATE_URL": "http://localhost:5000"
      }
    }
  }
}
```

#### Web Clients (SSE Mode)

Connect to the SSE endpoint for real-time updates:

```javascript
const eventSource = new EventSource('http://localhost:8000/sse');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

#### REST API (HTTP Mode)

Make standard HTTP requests:

```bash
# Get cameras
curl http://localhost:8000/tools/get_cameras

# Get events
curl http://localhost:8000/tools/get_events?limit=5

# Get stats
curl http://localhost:8000/tools/get_stats
```

Or use any HTTP client:

```python
import requests

response = requests.post(
    'http://localhost:8000/tools/get_events',
    json={'camera': 'front_door', 'limit': 10}
)
print(response.json())   "frigate": {
      "command": "/path/to/frigate-mcp/.venv/bin/python",
      "args": ["-m", "frigate_mcp.server"],
      "env": {
        "FRIGATE_FRIGATE_URL": "http://localhost:5000"
      }
    }
  }
}
```

## 🛠️ Available Tools

The server provides 7 MCP tools for interacting with Frigate:

### 1. `get_cameras()`

List all configured cameras with their status and properties.

**Returns:**
```json
[
  {
    "name": "front_door",
    "enabled": true,
    "width": 1920,
    "height": 1080,
    "fps": 5
  }
]
```

### 2. `get_events(camera, label, limit)`

Get recent detection events with optional filtering.

**Parameters:**
- `camera` (optional): Filter by camera name
- `label` (optional): Filter by object type (`person`, `car`, `dog`, etc.)
- `limit` (default: 10): Maximum events to return (1-100)

**Example:**
```python
get_events(camera="front_door", label="person", limit=5)
```

**Returns:**
```json
[
  {
    "id": "1234567890.123456-abcdef",
    "camera": "front_door",
    "label": "person",
    "start_time": 1704067200.5,
    "end_time": 1704067205.8,
    "has_clip": true,
    "has_snapshot": true,
    "zones": ["entrance"],
    "thumbnail": "http://localhost:5000/api/events/1234.../thumbnail.jpg"
  }
]
```

### 3. `get_stats()`

Get Frigate system statistics and performance metrics.

**Returns:**
```json
{
  "service": {
    "uptime": 86400,
    "version": "0.16.3",
    "storage": {...}
  },
  "detectors": {
    "coral": {
      "inference_speed": 8.5,
      "detection_start": 1704067200.0
    }
  },
  "cameras": {
    "front_door": {
      "camera_fps": 5.0,
      "process_fps": 5.0,
      "detection_fps": 1.2
    }
  }
}
```

### 4. `get_event_details(event_id)`

Get comprehensive details about a specific event.

**Parameters:**
- `event_id`: Unique event identifier

**Returns:**
```json
{
  "id": "1234567890.123456-abcdef",
  "camera": "front_door",
  "label": "person",
  "start_time": 1704067200.5,
  "end_time": 1704067205.8,
  "duration": 5.3,
  "score": 0.87,
  "zones": ["entrance"],
  "has_clip": true,
  "has_snapshot": true,
  "media": {
    "thumbnail": "http://localhost:5000/api/events/.../thumbnail.jpg",
    "snapshot": "http://localhost:5000/api/events/.../snapshot.jpg",
    "clip": "http://localhost:5000/api/events/.../clip.mp4"
  }
}
```

### 5. `get_snapshot(camera, timestamp)`

Get a snapshot URL from a specific camera.

**Parameters:**
- `camera`: Camera name
- `timestamp` (optional): Unix timestamp for historical snapshot

**Returns:**
```json
{
  "camera": "front_door",
  "timestamp": "latest",
  "url": "http://localhost:5000/api/front_door/latest.jpg",
  "description": "Snapshot from front_door (latest)"
}
```

### 6. `get_recordings(camera, date)`

Get recording information for a specific camera and date.

**Parameters:**
- `camera`: Camera name
- `date` (optional): Date in `YYYY-MM-DD` format (defaults to today)

**Returns:**
```json
{
  "camera": "front_door",
  "date": "2024-01-01",
  "recordings_count": 24,
  "total_duration": 86400,
  "recordings": [
    {
      "day": "2024-01-01",
      "hour": "10",
      "duration": 3600,
      "events": 5
    }
  ]
}
```

### 7. `get_config()`

Get Frigate configuration summary.

**Returns:**
```json
{
  "cameras": ["front_door", "backyard", "garage"],
  "detectors": ["coral"],
  "mqtt": {
    "enabled": true,
    "host": "localhost"
  },
  "model": "path/to/model.tflite",
  "version": "0.16.3"
}
```

## 🏗️ Project Structure

```
frigate-mcp/
├── src/
│   └── frigate_mcp/
│       ├── __init__.py       # Package metadata
│       ├── config.py         # Configuration management
│       └── server.py         # MCP server & tools
├── test_connection.py        # Connection test script
├── pyproject.toml           # Project dependencies
├── .env                     # Environment variables (not in git)
└── README.md                # This file
```

---

Made with ❤️ for the Frigate and MCP communities
