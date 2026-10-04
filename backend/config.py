"""Configuration module for LinuxDash application.

Centralizes all configuration settings and environment variable handling.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables.
    
    Attributes:
        host_proc: Path to procfs for containerized environments.
        host_root: Root filesystem path for disk metrics.
        auth_log_path: Path to authentication log file.
        cpu_threshold: CPU usage percentage threshold for alerts.
        memory_threshold: Memory usage percentage threshold for alerts.
        disk_threshold: Disk usage percentage threshold for alerts.
        app_host: Host address for the application server.
        app_port: Port number for the application server.
    """
    host_proc: Optional[str] = None
    host_root: str = "/"
    auth_log_path: str = "/var/log/auth.log"
    cpu_threshold: float = 90.0
    memory_threshold: float = 90.0
    disk_threshold: float = 90.0
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables.
        
        Returns:
            Config: Configuration instance with values from environment.
        """
        return cls(
            host_proc=os.getenv("HOST_PROC"),
            host_root=os.getenv("HOST_ROOT", "/"),
            auth_log_path=os.getenv("AUTH_LOG_PATH", "/var/log/auth.log"),
            cpu_threshold=float(os.getenv("CPU_THRESHOLD", "90.0")),
            memory_threshold=float(os.getenv("MEMORY_THRESHOLD", "90.0")),
            disk_threshold=float(os.getenv("DISK_THRESHOLD", "90.0")),
            app_host=os.getenv("APP_HOST", "0.0.0.0"),
            app_port=int(os.getenv("APP_PORT", "8000")),
        )


# Global configuration instance
config = Config.from_environment()
