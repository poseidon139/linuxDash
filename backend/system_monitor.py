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
    # CPU usage percentage (per core and total)
    cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_percent_total = sum(cpu_percent_per_core) / len(cpu_percent_per_core) if cpu_percent_per_core else 0
    
    # CPU frequency
    cpu_freq = psutil.cpu_freq()
    cpu_freq_mhz = round(cpu_freq.current, 2) if cpu_freq else 0
    
    # Load averages
    try:
        load_avg = os.getloadavg()
        load_avg_dict = {'1m': round(load_avg[0], 2), '5m': round(load_avg[1], 2), '15m': round(load_avg[2], 2)}
    except (OSError, AttributeError):
        load_avg_dict = {'1m': 0, '5m': 0, '15m': 0}
    
    # Memory statistics
    mem = psutil.virtual_memory()
    memory_used = mem.used
    memory_total = mem.total
    memory_percent = mem.percent
    
    # Swap statistics
    swap = psutil.swap_memory()
    swap_used = swap.used
    swap_total = swap.total
    swap_percent = swap.percent if swap_total > 0 else 0
    
    # Top memory-consuming processes
    top_processes = []
    try:
        processes = sorted(psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']), 
                          key=lambda p: p.info['memory_percent'] or 0, reverse=True)[:5]
        for proc in processes:
            try:
                mem_mb = round(proc.info['memory_info'].rss / (1024 ** 2), 2) if proc.info['memory_info'] else 0
                top_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'percent': round(proc.info['memory_percent'], 2) if proc.info['memory_percent'] else 0,
                    'memory_mb': mem_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    
    # Disk statistics for all partitions (filter out pseudo-filesystems)
    disk_partitions = []
    try:
        partitions = psutil.disk_partitions(all=True)
        for partition in partitions:
            # Filter out pseudo-filesystems and focus on real storage
            if partition.fstype in ('overlay', 'ext4', 'xfs', 'btrfs', 'ntfs', 'vfat', 'fuse.ossfs'):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'used': usage.used,
                        'total': usage.total,
                        'percent': usage.percent,
                        'free': usage.free
                    })
                except (PermissionError, OSError):
                    continue
    except Exception:
        pass
    
    # Fallback to root filesystem if no partitions found
    if not disk_partitions:
        try:
            root_usage = psutil.disk_usage('/')
            disk_partitions.append({
                'device': 'rootfs',
                'mountpoint': '/',
                'fstype': 'overlay',
                'used': root_usage.used,
                'total': root_usage.total,
                'percent': root_usage.percent,
                'free': root_usage.free
            })
        except Exception:
            pass
    
    # Disk I/O statistics
    disk_io = psutil.disk_io_counters()
    disk_read_mb_s = 0
    disk_write_mb_s = 0
    if disk_io:
        # Note: These are cumulative, would need delta calculation for rates
        disk_read_mb_s = round(disk_io.read_bytes / (1024 ** 2), 2)
        disk_write_mb_s = round(disk_io.write_bytes / (1024 ** 2), 2)
    
    # Network I/O statistics
    net_io = psutil.net_io_counters(pernic=True)
    net_sent_total = sum(io.bytes_sent for io in net_io.values())
    net_recv_total = sum(io.bytes_recv for io in net_io.values())
    
    # Network interfaces info
    network_interfaces = []
    try:
        net_if_stats = psutil.net_if_stats()
        for iface_name, stats in net_if_stats.items():
            if stats.isup:
                speed = stats.speed if stats.speed > 0 else 0
                network_interfaces.append({
                    'name': iface_name,
                    'is_up': stats.isup,
                    'speed': speed
                })
    except Exception:
        pass
    
    # Network bandwidth (cumulative for now)
    net_sent_mb = round(net_sent_total / (1024 ** 2), 2)
    net_recv_mb = round(net_recv_total / (1024 ** 2), 2)
    
    return {
        "cpu": {
            "total": round(cpu_percent_total, 2),
            "per_core": [round(p, 2) for p in cpu_percent_per_core],
            "core_count": len(cpu_percent_per_core),
            "frequency_mhz": cpu_freq_mhz,
            "load_avg": load_avg_dict
        },
        "memory": {
            "used": memory_used,
            "total": memory_total,
            "percent": memory_percent,
            "swap_used": swap_used,
            "swap_total": swap_total,
            "swap_percent": swap_percent,
            "top_processes": top_processes
        },
        "disk": {
            "partitions": disk_partitions,
            "io_stats": {
                "read_mb_s": disk_read_mb_s,
                "write_mb_s": disk_write_mb_s
            }
        },
        "network": {
            "sent_total_mb": net_sent_mb,
            "recv_total_mb": net_recv_mb,
            "bandwidth": {
                "sent_mb_s": net_sent_mb,  # Cumulative, not rate
                "recv_mb_s": net_recv_mb   # Cumulative, not rate
            },
            "interfaces": network_interfaces
        }
    }
