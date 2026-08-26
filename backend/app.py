"""
LinuxDash - System Monitoring Dashboard Backend

A real-time system monitoring application that provides metrics,
security event logging, and alerting via WebSocket connections.
"""

import asyncio
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn

from config import config
from system_monitor import get_system_metrics
from security_logger import tail_security_logs
from alert_system import monitor_alerts

# Initialize FastAPI application
app = FastAPI(title="LinuxDash")


class ConnectionManager:
    """Manages WebSocket connections for broadcasting messages."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket from the active list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """Send a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


async def broadcast_metrics() -> None:
    """Periodically fetch and broadcast system metrics to all clients."""
    while True:
        try:
            metrics = get_system_metrics()
            payload = {
                "type": "metrics",
                "data": metrics
            }
            await manager.broadcast(json.dumps(payload))
        except Exception as e:
            print(f"Error broadcasting metrics: {e}")
        await asyncio.sleep(1)


async def handle_security_event(event: dict) -> None:
    """Broadcast security events to all connected clients."""
    payload = {
        "type": "security_event",
        "data": event
    }
    await manager.broadcast(json.dumps(payload))


async def handle_alert(alert: dict) -> None:
    """Broadcast alerts to all connected clients."""
    payload = {
        "type": "alert",
        "data": alert
    }
    await manager.broadcast(json.dumps(payload))


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize background tasks on application startup."""
    asyncio.create_task(broadcast_metrics())
    asyncio.create_task(monitor_alerts(handle_alert))
    asyncio.create_task(tail_security_logs(handle_security_event))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections and maintain client connectivity."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive by waiting for any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Ensure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root() -> RedirectResponse:
    """Redirect root path to the dashboard index page."""
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    uvicorn.run("app:app", host=config.app_host, port=config.app_port, reload=True)
