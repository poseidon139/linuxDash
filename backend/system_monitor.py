"""System monitoring module for collecting CPU, memory, disk, and network metrics."""

import os

import psutil

from config import config


def _configure_procfs() -> None:
    """Configure procfs path for containerized environments."""
    if config.host_proc:
        psutil.PROCFS_PATH = config.host_proc


_configure_procfs()


def get_system_metrics() -> dict:
    """Collect and return system metrics.
    
    Returns:
        dict: System metrics including CPU, memory, disk, and network statistics.
    """
    # CPU usage percentage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory statistics
    mem = psutil.virtual_memory()
    memory_percent = mem.percent
    memory_used_gb = round(mem.used / (1024 ** 3), 2)
    memory_total_gb = round(mem.total / (1024 ** 3), 2)
    
    # Disk statistics (root partition or custom host root)
    disk = psutil.disk_usage(config.host_root)
    disk_percent = disk.percent
    disk_used_gb = round(disk.used / (1024 ** 3), 2)
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    
    # Network I/O statistics
    net_io = psutil.net_io_counters()
    net_sent_mb = round(net_io.bytes_sent / (1024 ** 2), 2)
    net_recv_mb = round(net_io.bytes_recv / (1024 ** 2), 2)
    
    return {
        "cpu": {
            "percent": cpu_percent
        },
        "memory": {
            "percent": memory_percent,
            "used_gb": memory_used_gb,
            "total_gb": memory_total_gb
        },
        "disk": {
            "percent": disk_percent,
            "used_gb": disk_used_gb,
            "total_gb": disk_total_gb
        },
        "network": {
            "sent_mb": net_sent_mb,
            "recv_mb": net_recv_mb
        }
    }
