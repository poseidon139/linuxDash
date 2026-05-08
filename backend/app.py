import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
import os

from system_monitor import get_system_metrics
from security_logger import tail_security_logs
from alert_system import monitor_alerts

app = FastAPI(title="LinuxDash")

# Store connected websocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Background tasks
async def broadcast_metrics():
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

async def handle_security_event(event):
    payload = {
        "type": "security_event",
        "data": event
    }
    await manager.broadcast(json.dumps(payload))

async def handle_alert(alert):
    payload = {
        "type": "alert",
        "data": alert
    }
    await manager.broadcast(json.dumps(payload))

@app.on_event("startup")
async def startup_event():
    # Start background tasks
    asyncio.create_task(broadcast_metrics())
    asyncio.create_task(monitor_alerts(handle_alert))
    asyncio.create_task(tail_security_logs(handle_security_event))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, just keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Mount static files for frontend
# Ensure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
