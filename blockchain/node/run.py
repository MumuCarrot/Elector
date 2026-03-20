import uvicorn
import socket
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from node.core.settings import settings

HOST = settings.app.APP_HOST
PORT = settings.app.APP_PORT
BASE_DIR = Path(__file__).resolve().parent
APP = "node"


def is_port_free(port, host="127.0.0.1"):
    """Checks whether ``host:port`` accepts a new TCP connection (port not in use).

    Args:
        port: TCP port number.
        host: Host to probe; defaults to loopback.

    Returns:
        bool: True if the port appears free for bind/listen on ``0.0.0.0``.

    """
    check_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    check_socket.settimeout(0.1)
    try:
        result = check_socket.connect_ex((host, port))
        if result == 0:
            check_socket.close()
            return False
    except Exception:
        pass
    finally:
        check_socket.close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", port))
            s.listen(1)
            return True
        except (OSError, socket.error):
            return False


def find_port(start=PORT, end=PORT + 100, host="127.0.0.1"):
    """Returns the first free port in ``[start, end)``.

    Args:
        start: First port to try (inclusive).
        end: One past the last port to try (exclusive).
        host: Host used for ``is_port_free`` probes.

    Returns:
        int: A free port number.

    Raises:
        RuntimeError: If no free port exists in the range.

    """
    for port in range(start, end):
        if is_port_free(port, host):
            return port
    raise RuntimeError(f"No free port found in range {start}-{end}")


if __name__ == "__main__":
    import os
    import time

    time.sleep(0.1)

    actual_port = find_port(start=PORT, host="127.0.0.1")

    if not is_port_free(actual_port, "127.0.0.1"):
        actual_port = find_port(start=actual_port + 1, host="127.0.0.1")

    os.environ["NODE_ACTUAL_HOST"] = HOST
    os.environ["NODE_ACTUAL_PORT"] = str(actual_port)

    hello = f'''
            ===========================
            This app is running node application.

            Node is running on {HOST}:{actual_port}.

            To stop the node, simply terminate the application.
            ===========================
            '''
    print(hello, end="\n\n")

    uvicorn.run(
        "node.main:app",
        host=HOST,
        port=actual_port,
        reload=True,
        reload_dirs=[str(BASE_DIR)],
    )
