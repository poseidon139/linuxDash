"""Security log monitoring module for parsing and tailing authentication logs."""

import asyncio
import os
import re
from typing import Callable, Optional

from config import config


# Regex patterns for common security events
FAILED_SSH_PATTERN = re.compile(r"Failed password for (?:invalid user )?(.*?) from (.*?) port")
SUDO_PATTERN = re.compile(r"sudo: +(.*?): .*? COMMAND=(.*)")


def parse_log_line(line: str) -> Optional[dict]:
    """Parse a log line to extract security event information.
    
    Args:
        line: A single line from the security log file.
        
    Returns:
        dict containing event details if a security event is found, None otherwise.
    """
    # Extract timestamp and host (simplistic parsing for standard syslog format)
    # Example format: May  8 12:34:56 hostname sshd[123]: Failed password...
    parts = line.split(maxsplit=4)
    if len(parts) < 5:
        return None
    
    timestamp = " ".join(parts[:3])
    message = parts[4]
    
    # Check for failed SSH login
    ssh_match = FAILED_SSH_PATTERN.search(message)
    if ssh_match:
        user = ssh_match.group(1)
        ip = ssh_match.group(2)
        return {
            "type": "failed_login",
            "timestamp": timestamp,
            "user": user,
            "ip": ip,
            "message": f"Failed SSH login for user {user} from {ip}"
        }
    
    # Check for sudo usage
    sudo_match = SUDO_PATTERN.search(message)
    if sudo_match:
        user = sudo_match.group(1)
        command = sudo_match.group(2)
        return {
            "type": "sudo_usage",
            "timestamp": timestamp,
            "user": user,
            "command": command,
            "message": f"User {user} executed sudo command: {command}"
        }
    
    return None


async def tail_security_logs(callback: Callable[[dict], None]) -> None:
    """Tail the security log file and call the callback with parsed events.
    
    Args:
        callback: Async function to call with each parsed security event.
    """
    if not os.path.exists(config.auth_log_path):
        print(f"Warning: Log file {config.auth_log_path} not found.")
        return
    
    try:
        with open(config.auth_log_path, "r") as f:
            # Go to the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                
                # Parse the line for security events
                event = parse_log_line(line)
                if event:
                    await callback(event)
    except PermissionError:
        print(f"Warning: Permission denied to read {config.auth_log_path}.")
    except Exception as e:
        print(f"Error tailing log: {e}")
