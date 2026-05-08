import psutil
import os

# Allow overriding procfs path for Docker containers
host_proc = os.getenv("HOST_PROC")
if host_proc:
    psutil.PROCFS_PATH = host_proc

def get_system_metrics():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory
    mem = psutil.virtual_memory()
    memory_percent = mem.percent
    memory_used_gb = mem.used / (1024 ** 3)
    memory_total_gb = mem.total / (1024 ** 3)
    
    # Disk (Root path; in docker this would be the container root unless host is mounted)
    # To get host root, we'd need to mount it, e.g. /host/root
    # For simplicity, we just check the path defined by HOST_ROOT or "/"
    host_root = os.getenv("HOST_ROOT", "/")
    disk = psutil.disk_usage(host_root)
    disk_percent = disk.percent
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)
    
    # Network
    net_io = psutil.net_io_counters()
    net_sent_mb = net_io.bytes_sent / (1024 ** 2)
    net_recv_mb = net_io.bytes_recv / (1024 ** 2)
    
    return {
        "cpu": {
            "percent": cpu_percent
        },
        "memory": {
            "percent": memory_percent,
            "used_gb": round(memory_used_gb, 2),
            "total_gb": round(memory_total_gb, 2)
        },
        "disk": {
            "percent": disk_percent,
            "used_gb": round(disk_used_gb, 2),
            "total_gb": round(disk_total_gb, 2)
        },
        "network": {
            "sent_mb": round(net_sent_mb, 2),
            "recv_mb": round(net_recv_mb, 2)
        }
    }
