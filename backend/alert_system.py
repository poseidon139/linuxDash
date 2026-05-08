import asyncio
from datetime import datetime
from system_monitor import get_system_metrics

# Alert thresholds
CPU_THRESHOLD = 90.0
MEMORY_THRESHOLD = 90.0
DISK_THRESHOLD = 90.0

async def monitor_alerts(callback):
    """
    Periodically checks system metrics and generates alerts if thresholds are exceeded.
    """
    while True:
        try:
            metrics = get_system_metrics()
            alerts = []
            timestamp = datetime.now().strftime("%b %d %H:%M:%S")

            if metrics["cpu"]["percent"] > CPU_THRESHOLD:
                alerts.append({
                    "id": f"cpu-{datetime.now().timestamp()}",
                    "level": "critical",
                    "timestamp": timestamp,
                    "message": f"High CPU usage detected: {metrics['cpu']['percent']}%"
                })
                
            if metrics["memory"]["percent"] > MEMORY_THRESHOLD:
                alerts.append({
                    "id": f"mem-{datetime.now().timestamp()}",
                    "level": "critical",
                    "timestamp": timestamp,
                    "message": f"High Memory usage detected: {metrics['memory']['percent']}%"
                })

            if metrics["disk"]["percent"] > DISK_THRESHOLD:
                alerts.append({
                    "id": f"disk-{datetime.now().timestamp()}",
                    "level": "warning",
                    "timestamp": timestamp,
                    "message": f"High Disk usage detected: {metrics['disk']['percent']}%"
                })

            for alert in alerts:
                await callback(alert)
                
        except Exception as e:
            print(f"Error checking alerts: {e}")

        # Check every 5 seconds
        await asyncio.sleep(5)
