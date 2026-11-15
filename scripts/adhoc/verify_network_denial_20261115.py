"""Require OS network refusal before offline native tests, #1996, 2026-11-15.

Input: current OS sandbox. Output: errno evidence on stdout. Uses loopback only;
no address, email, source payload or request is sent to any external service.
"""

import errno
import json
import socket


def main():
    try:
        with socket.create_connection(("127.0.0.1", 9), timeout=1):
            raise RuntimeError("OS sandbox unexpectedly allowed a network connection")
    except OSError as exc:
        if exc.errno not in (errno.EPERM, errno.EACCES):
            raise RuntimeError(f"Expected OS permission refusal, observed errno {exc.errno}") from exc
        print(json.dumps({"os_network_denied": True, "errno": exc.errno, "message": str(exc)}))


if __name__ == "__main__":
    main()
