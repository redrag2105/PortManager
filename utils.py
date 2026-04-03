import psutil
from pathlib import Path

def get_target_ports() -> set:
    try:
        ports_file = Path("ports.txt")
        if not ports_file.exists():
            ports_file.write_text("3000\n3001\n3002\n3003\n3004\n3005\n")
        
        with open(ports_file, "r") as f:
            lines = f.read().splitlines()
        
        ports = set()
        for line in lines:
            cleaned = line.strip().split("#")[0].strip() # ignore comments
            if cleaned and cleaned.isdigit():
                ports.add(int(cleaned))
        return ports
    except Exception as e:
        return set()

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

def add_target_port(port: int) -> bool:
    """Adds a new port to ports.txt if it doesn't already exist."""
    try:
        ports_file = Path("ports.txt")
        # Ensure file exists
        if not ports_file.exists():
            get_target_ports()
            
        current_ports = get_target_ports()
        if port in current_ports:
            return False
            
        with open(ports_file, "a") as f:
            f.write(f"{port}\n")
        return True
    except Exception:
        return False
