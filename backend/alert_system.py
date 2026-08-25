"""Alert monitoring system for detecting threshold violations in system metrics."""

import asyncio
from datetime import datetime
from typing import Callable, List, Dict, Any

from config import config
from system_monitor import get_system_metrics


def _create_alert(metric_name: str, value: float, threshold: float, level: str = "critical") -> Dict[str, Any]:
    """Create an alert dictionary with standardized format.
    
    Args:
        metric_name: Name of the metric that triggered the alert.
        value: Current value of the metric.
        threshold: Threshold that was exceeded.
        level: Alert severity level (default: "critical").
        
    Returns:
        dict: Formatted alert object.
    """
    timestamp = datetime.now().strftime("%b %d %H:%M:%S")
    return {
        "id": f"{metric_name}-{datetime.now().timestamp()}",
        "level": level,
        "timestamp": timestamp,
        "message": f"High {metric_name.title()} usage detected: {value}%"
    }


def check_thresholds(metrics: dict) -> List[Dict[str, Any]]:
    """Check system metrics against defined thresholds and generate alerts.
    
    Args:
        metrics: Dictionary containing current system metrics.
        
    Returns:
        list: List of alert dictionaries for exceeded thresholds.
    """
    alerts = []
    
    if metrics["cpu"]["percent"] > config.cpu_threshold:
        alerts.append(_create_alert("cpu", metrics["cpu"]["percent"], config.cpu_threshold))
    
    if metrics["memory"]["percent"] > config.memory_threshold:
        alerts.append(_create_alert("memory", metrics["memory"]["percent"], config.memory_threshold))
    
    if metrics["disk"]["percent"] > config.disk_threshold:
        alerts.append(_create_alert("disk", metrics["disk"]["percent"], config.disk_threshold, level="warning"))
    
    return alerts


async def monitor_alerts(callback: Callable[[dict], None]) -> None:
    """Periodically check system metrics and notify via callback when thresholds are exceeded.
    
    Args:
        callback: Async function to call with each generated alert.
    """
    while True:
        try:
            metrics = get_system_metrics()
            alerts = check_thresholds(metrics)
            
            for alert in alerts:
                await callback(alert)
                
        except Exception as e:
            print(f"Error checking alerts: {e}")
        
        # Check every 5 seconds
        await asyncio.sleep(5)
