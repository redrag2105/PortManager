import os
import shutil
import platform
import subprocess
import urllib.request
import re
import asyncio

# Dictionary to track active processes for each forwarded port
active_tunnels: dict[int, asyncio.subprocess.Process] = {}

def get_devtunnel_path() -> str:
    """Helper function to get the local or system path of the devtunnel executable."""
    system_path = shutil.which('devtunnel')
    if system_path:
        return system_path
        
    # Check current directory for downloaded executable
    exe_name = 'devtunnel.exe' if platform.system() == 'Windows' else 'devtunnel'
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)

def check_devtunnel_cli() -> bool:
    """1. Checks if the devtunnel CLI is installed and accessible."""
    path = get_devtunnel_path()
    if os.path.exists(path) and os.access(path, os.X_OK):
        return True

    try:
        # Fallback test: execute devtunnel --version
        result = subprocess.run([path or 'devtunnel', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, PermissionError):
        return False

def download_devtunnel_cli(progress_callback=None) -> bool:
    """2. Download the CLI based on the host OS."""
    sys_os = platform.system()
    arch = platform.machine().lower()
    
    if sys_os == "Windows":
        url = "https://aka.ms/TunnelsCliDownload/win-x64"
    elif sys_os == "Darwin":
        if arch in ("arm64", "aarch64"):
            url = "https://aka.ms/TunnelsCliDownload/osx-arm64-mac"
        else:
            url = "https://aka.ms/TunnelsCliDownload/osx-x64-mac"
    else:  # Linux and others
        url = "https://aka.ms/TunnelsCliDownload/linux-x64"

    exe_name = 'devtunnel.exe' if sys_os == 'Windows' else 'devtunnel'
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)

    try:
        def reporthook(block_num, block_size, total_size):
            if total_size > 0 and progress_callback:
                percent = min(100, int(block_num * block_size * 100 / total_size))
                progress_callback(percent)

        urllib.request.urlretrieve(url, local_path, reporthook=reporthook)
        
        # Make executable on macOS/Linux
        if sys_os != "Windows":
            os.chmod(local_path, 0o755)
            
        return True
    except Exception as e:
        print(f"Failed to download devtunnel: {e}")
        return False

def check_login_status() -> str:
    """3. Check Login: Run devtunnel user show to determine authentication.
    Returns 'logged_in', 'logged_out', or 'expired'.
    """
    path = get_devtunnel_path()
    try:
        result = subprocess.run([path, 'user', 'show'], capture_output=True, text=True)
        # Check output or return code to verify authentication
        if 'Login token expired' in result.stdout or 'Login token expired' in result.stderr:
            return 'expired'
        if result.returncode != 0 or 'Not logged in' in result.stdout:
            return 'logged_out'
        return 'logged_in'
    except FileNotFoundError:
        return 'logged_out'

def trigger_login() -> bool:
    """3. Trigger Login: trigger the GitHub device login flow."""
    path = get_devtunnel_path()
    try:
        # Popen without blocking to allow the browser flow
        subprocess.Popen([path, 'user', 'login', '-g'])
        return True
    except Exception as e:
        print(f"Failed to trigger login: {e}")
        return False
def _extract_urls(line: str) -> list[str]:
    return re.findall(r'(https://[a-zA-Z0-9-\.]+\.devtunnels\.ms[^\s\x1b,]*)', line)
async def start_port_forward(port: int) -> tuple[str, str] | str | None:
    """
    4. Start Tunnel & Parse URL.
    Run devtunnel host -p {port} asynchronously and extract the public URL.   
    """
    path = get_devtunnel_path()
    tunnel_name = f"tui-tunnel-{port}"

    try:
        # Step 1: Create the tunnel
        proc_create = await asyncio.create_subprocess_exec(
            path, 'create', tunnel_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc_create.wait()

        # Step 2: Assign the port
        proc_port = await asyncio.create_subprocess_exec(
            path, 'port', 'create', tunnel_name, '-p', str(port),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc_port.wait()

        # Step 3: Host the tunnel
        process = await asyncio.create_subprocess_exec(
            path, 'host', tunnel_name, '--allow-anonymous',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        active_tunnels[port] = process

        # Continuously read and parse the generated tunnel URL from stdout    
        if process.stdout:
            public_url = None
            inspect_url = None

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace')
                
                if line.strip():
                    # Clean up ansi escape codes that might break our regex       
                    clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)       

                    # Parse URLs based on line content
                    if "Connect via browser:" in clean_line:
                        matches = _extract_urls(clean_line)
                        if matches:
                            # Pick the 'dashed' URL format (typically the second one, or the one lacking port logic at the end)
                            for match in matches:
                                if f"-{port}." in match or (not match.endswith(f":{port}") and not match.endswith(f":{port}/")):
                                    public_url = match
                                    break
                            if not public_url:
                                public_url = matches[-1]

                    elif "Inspect network activity:" in clean_line:
                        matches = _extract_urls(clean_line)
                        if matches:
                            inspect_url = matches[0]

                    if public_url and inspect_url:
                        return (public_url, inspect_url)

        return None
    except Exception as e:
        print(f"Error starting port forward for port {port}: {e}")
        return None

async def stop_port_forward(port: int) -> bool:
    """
    5. Stop Tunnel.
    Terminate the active process for the specified port.
    """
    process = active_tunnels.get(port)
    if process:
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
        except Exception:
            try:
                process.kill() # Force kill if terminate fails
            except Exception:
                pass
        
        del active_tunnels[port]
        return True
        
    return False
