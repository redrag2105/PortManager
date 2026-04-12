import psutil
from pathlib import Path
import json

DEFAULT_SETTINGS = {
    "ports": [3000, 5173],
    "sounds": {
        "mute": False,
        "volumes": {
            "splash": 0.2,
            "scroll": 0.1,
            "close": 0.4,
            "click": 0.5,
            "error": 0.5,
            "success": 0.5
        }
    }
}

def _get_settings_file() -> Path:
    settings_file = Path("settings.json")
    
    if not settings_file.exists():
        settings = DEFAULT_SETTINGS.copy()
        
        try:
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception:
            pass
            
    return settings_file

def get_settings() -> dict:
    try:
        with open(_get_settings_file(), "r") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged["ports"] = data.get("ports", merged["ports"])
            if "sounds" in data:
                merged["sounds"]["mute"] = data["sounds"].get("mute", merged["sounds"]["mute"])
                if "volumes" in data["sounds"]:
                    for k, v in data["sounds"]["volumes"].items():
                        merged["sounds"]["volumes"][k] = v
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict) -> bool:
    try:
        with open(_get_settings_file(), "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception:
        return False

def get_target_ports() -> set:
    settings = get_settings()
    return set(settings.get("ports", []))

def get_running_processes(target_ports: set) -> list[dict]:
    results = []
    seen = set()
    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.status == 'LISTEN' and conn.laddr and len(conn.laddr) >= 2:
                port = conn.laddr[1]
                if port in target_ports:
                    pid = conn.pid
                    if pid and (port, pid) not in seen:
                        seen.add((port, pid))
                        try:
                            proc = psutil.Process(pid)
                            results.append({
                                "port": port,
                                "pid": pid,
                                "name": proc.name(),
                                "status": "RUNNING",
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            results.append({
                                "port": port,
                                "pid": pid,
                                "name": "Access Denied / Unknown",
                                "status": "RUNNING",
                            })
    except psutil.AccessDenied:
        pass
    
    # Fill in missing ports as inactive
    running_ports = {r["port"] for r in results}
    for p in target_ports:
        if p not in running_ports:
            results.append({
                "port": p,
                "pid": "-",
                "name": "-",
                "status": "INACTIVE"
            })
            
    # Sort by port
    results.sort(key=lambda x: x["port"])
    return results

_process_cache = {}

def get_process_details(pid: int) -> dict | None:
    if not pid or not str(pid).isdigit():
        return None
    pid = int(pid)
    try:
        proc = _process_cache.get(pid)
        # Create a new process object if it doesn't exist or is obsolete
        if not proc or not proc.is_running():
            proc = psutil.Process(pid)
            _process_cache[pid] = proc
            proc.cpu_percent(interval=None) # Prime the cpu counter

        with proc.oneshot():
            return {
                "name": proc.name(),
                "exe": proc.exe(),
                "created": proc.create_time(),
                "status": proc.status(),
                "username": proc.username(),
                "memory": proc.memory_info().rss / (1024 * 1024), # in MB
                "cpu": proc.cpu_percent(interval=None)
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        _process_cache.pop(pid, None)
        return None

def kill_process(pid: int) -> bool:
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False
        
    try:
        proc.terminate()
        proc.wait(timeout=3)
        return True
    except (psutil.AccessDenied, psutil.TimeoutExpired):
        try: # force kill
            proc.kill()
            return True
        except Exception:
            return False

def add_multiple_target_ports(raw_input: str) -> dict:
    """Takes a space-separated string of ports, validates and adds them safely."""
    tokens = raw_input.replace(',', ' ').split()
    current_ports = get_target_ports()
    
    added = []
    failed_exists = []
    failed_invalid = []
    failed_range = []
    
    for token in tokens:
        if not token.isdigit():
            failed_invalid.append(token)
            continue
            
        port = int(token)
        if not (1 <= port <= 65535):
            failed_range.append(str(port))
            continue
            
        if port in current_ports or port in added:
            if str(port) not in failed_exists:
                failed_exists.append(str(port))
            continue
            
        added.append(port)
        
    if added:
        try:
            settings = get_settings()
            ports_list = settings.get("ports", [])
            for p in added:
                if p not in ports_list:
                    ports_list.append(p)
            settings["ports"] = sorted(ports_list)
            save_settings(settings)
        except Exception:
            return {"error": "File write error"}
            
    return {
        "added": [str(a) for a in added],
        "failed_invalid": failed_invalid,
        "failed_range": failed_range,
        "failed_exists": failed_exists
    }

def remove_target_port(port: int) -> bool:
    """Removes a port from settings.json."""
    settings = get_settings()
    ports = settings.get("ports", [])
    if port in ports:
        ports.remove(port)
        settings["ports"] = ports
        return save_settings(settings)
    return False

def edit_target_port(old_port: int, new_port: int) -> bool:
    """Changes an existing port to a new port in settings.json."""
    if old_port == new_port:
        return True

    settings = get_settings()
    ports = settings.get("ports", [])
    
    if new_port in ports:
        return False # Target port already exists

    if old_port in ports:
        idx = ports.index(old_port)
        ports[idx] = new_port
        settings["ports"] = sorted(ports)
        return save_settings(settings)
        
    return False
