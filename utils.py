import psutil
from pathlib import Path

def _get_ports_file() -> Path:
    ports_file = Path("ports.txt")
    if not ports_file.exists():
        ports_file.write_text("3000\n3001\n3002\n3003\n3004\n3005\n")       
    return ports_file

def _read_ports() -> list[str]:
    try:
        with open(_get_ports_file(), "r") as f:
            return f.readlines()
    except Exception:
        return []

def _write_ports(lines: list[str]) -> bool:
    try:
        with open(_get_ports_file(), "w") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False

def get_target_ports() -> set:
    ports = set()
    for line in _read_ports():
        cleaned = line.strip().split("#")[0].strip() # ignore comments      
        if cleaned and cleaned.isdigit():
            ports.add(int(cleaned))
    return ports

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
    current_ports = get_target_ports()
    if port in current_ports:
        return False
    try:
        with open(_get_ports_file(), "a") as f:
            f.write(f"{port}\n")
        return True
    except Exception:
        return False

def remove_target_port(port: int) -> bool:
    """Removes a port from ports.txt."""
    lines = _read_ports()
    new_lines = []
    port_removed = False
    for line in lines:
        cleaned = line.strip().split("#")[0].strip()
        if cleaned and cleaned.isdigit() and int(cleaned) == port:
            port_removed = True
            continue # Skip adding this line back
        new_lines.append(line)

    return _write_ports(new_lines) if port_removed else False

def edit_target_port(old_port: int, new_port: int) -> bool:
    """Changes an existing port to a new port in ports.txt."""
    if old_port == new_port:
        return True

    current_ports = get_target_ports()
    if new_port in current_ports:
        return False # Target port already exists

    lines = _read_ports()
    new_lines = []
    port_edited = False
    for line in lines:
        cleaned = line.strip().split("#")[0].strip()
        if cleaned and cleaned.isdigit() and int(cleaned) == old_port:      
            # Replace the number but preserve comments/newlines after it    
            idx = line.find(cleaned)
            line = line[:idx] + str(new_port) + line[idx+len(cleaned):]     
            port_edited = True
        new_lines.append(line)

    return _write_ports(new_lines) if port_edited else False
