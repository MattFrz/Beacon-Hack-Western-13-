import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def wait_for(log, prefix, occurrence=1):
    deadline = time.monotonic() + 7
    while time.monotonic() < deadline:
        log.seek(0)
        matches = [line.strip() for line in log if line.startswith(prefix)]
        if len(matches) >= occurrence:
            return matches[occurrence - 1]
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for {prefix} #{occurrence}")


@contextmanager
def supervise(*worker):
    world = "/beacon-supervisor-test-" + uuid.uuid4().hex
    env = dict(os.environ, BEACON_SUPERVISOR_WORLD=world)
    with tempfile.NamedTemporaryFile(mode="r") as log, open(log.name, "w") as out:
        proc = subprocess.Popen(["build/supervisor", *worker], env=env,
                                stderr=out, stdout=subprocess.DEVNULL)
        try:
            yield log
        finally:
            proc.terminate()
            proc.wait(timeout=6)
            Path("/dev/shm", world[1:]).unlink(missing_ok=True)
        assert proc.returncode == 0


with supervise("build/dummy") as log:
    first = int(wait_for(log, "heartbeat").split()[1])
    os.kill(first, signal.SIGKILL)
    assert wait_for(log, "worker fault").endswith("100 ms")
    second = int(wait_for(log, "heartbeat", 2).split()[1])
    assert second != first
    os.kill(second, signal.SIGSTOP)  # Process still exists, heartbeat stops.
    assert wait_for(log, "worker fault", 2).endswith("500 ms")
    third = int(wait_for(log, "heartbeat", 3).split()[1])
    time.sleep(10.3)
    os.kill(third, signal.SIGKILL)
    assert wait_for(log, "worker fault", 3).endswith("100 ms")
    wait_for(log, "heartbeat", 4)
    print("PASS: child death, stale shared heartbeat, and reset after ten healthy seconds")

with supervise(sys.executable, "-u", "-c", "import time\nwhile True: print('H'); time.sleep(.01)") as log:
    wait_for(log, "worker fault")
    log.seek(0)
    assert not any(line.startswith("heartbeat") for line in log)
    print("PASS: stdout cannot clear the heartbeat fault")
