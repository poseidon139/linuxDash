import os
import asyncio
import re

LOG_FILE = os.getenv("AUTH_LOG_PATH", "/var/log/auth.log")

async def tail_security_logs(callback):
    """
    Tails the security log file and calls the callback with parsed events.
    """
    if not os.path.exists(LOG_FILE):
        print(f"Warning: Log file {LOG_FILE} not found.")
        return

    # Regex patterns for common security events
    failed_ssh_pattern = re.compile(r"Failed password for (?:invalid user )?(.*?) from (.*?) port")
    sudo_pattern = re.compile(r"sudo: +(.*?): .*? COMMAND=(.*)")
    
    try:
        with open(LOG_FILE, "r") as f:
            # Go to the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                
                # Parse the line
                event = parse_log_line(line, failed_ssh_pattern, sudo_pattern)
                if event:
                    await callback(event)
    except PermissionError:
        print(f"Warning: Permission denied to read {LOG_FILE}.")
    except Exception as e:
        print(f"Error tailing log: {e}")

def parse_log_line(line, failed_ssh_pattern, sudo_pattern):
    # Extract timestamp and host (simplistic parsing for standard syslog format)
    # Example format: May  8 12:34:56 hostname sshd[123]: Failed password...
    parts = line.split(maxsplit=4)
    if len(parts) < 5:
        return None
        
    timestamp = " ".join(parts[:3])
    message = parts[4]
    
    # Check for failed SSH login
    ssh_match = failed_ssh_pattern.search(message)
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
    sudo_match = sudo_pattern.search(message)
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
