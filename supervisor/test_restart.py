import os
import signal
import subprocess
import tempfile
import time


def await_heartbeat(log, previous_pid=None):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        log.seek(0)
        for line in log:
            if line.startswith("heartbeat "):
                pid = int(line.split()[1])
                if pid != previous_pid:
                    return pid
        time.sleep(0.02)
    raise AssertionError("Timed out waiting for a healthy replacement child")


with tempfile.NamedTemporaryFile(mode="r") as log:
    with open(log.name, "w") as output:
        proc = subprocess.Popen(["build/supervisor", "build/dummy"], stderr=output)
        try:
            first = await_heartbeat(log)
            os.kill(first, signal.SIGKILL)
            second = await_heartbeat(log, first)
            print(f"Restart verified: child {first} replaced by healthy child {second}")
        finally:
            proc.terminate()
            proc.wait(timeout=6)
        assert proc.returncode == 0
