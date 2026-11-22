"""Beacon stack test: the QNX beat, on a laptop.

Run from supervisor/: `python3 test_beacon.py`, or `make test-beacon`.

What it checks, against `supervisor --beacon` and the real guided/ingest
binaries (spec §5.1):

  1. guided starts and keeps its heartbeat, so the fault path stays quiet;
  2. killing guided is reported as a fault and respawned, and ingest is left
     alone (the relay may die, the cue process is the one that must not);
  3. SIGSTOP on guided (process alive, loop dead) is caught by the heartbeat
     and produces the same fault path;
  4. SIGTERM to the supervisor shuts the stack down and exits 0.

This is not a QNX test. It proves the restart logic and the fault reporting;
the scheduler attributes are only real on the device (spawn attrs are refused
by an unprivileged Linux kernel, and the supervisor says so in its log).
"""
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = Path(__file__).resolve().parent / "build"


def lines(log, prefix):
    log.seek(0)
    return [line.rstrip() for line in log if line.startswith(prefix)]


def pids(log, prefix):
    found = []
    for line in lines(log, prefix):
        parts = line.split()
        if len(parts) >= 3 and parts[2].isdigit():
            found.append((parts[1], int(parts[2])))
    return found


def wait_for(log, prefix, count=1, timeout=12):
    """Waits for the count-th line with this prefix."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = lines(log, prefix)
        if len(found) >= count:
            return found[count - 1]
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {prefix!r} #{count}")


def wait_for_pid(log, prefix, count=1, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = pids(log, prefix)
        if len(found) >= count:
            return found[count - 1]
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for a pid in {prefix!r} #{count}")


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main():
    world = "/beacon-stack-test-" + uuid.uuid4().hex

    # Its own UDP port: a leftover ingest from a demo must not fail the test.
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    udp_port = probe.getsockname()[1]
    probe.close()
    env = dict(
        os.environ,
        BEACON_SUPERVISOR_WORLD=world,
        BEACON_WORLD=world,
        BEACON_FRAMES=world + "-frames",
        BEACON_DEPTH=world + "-depth",
        BEACON_GUIDED=str(ROOT / "guided" / "build" / "guided"),
        BEACON_INGEST=str(ROOT / "ingest" / "build" / "ingest"),
    )
    for name, path in (("guided", env["BEACON_GUIDED"]), ("ingest", env["BEACON_INGEST"])):
        if not Path(path).is_file():
            sys.exit(f"missing {name} binary at {path}; run make -C {name} first")

    with open("/tmp/beacon-stack-test.log", "w+") as log:
        sup = subprocess.Popen(
            [str(BUILD / "supervisor"), "--beacon",
             "--guided-args", "--duration 120",
             "--ingest-args", f"--udp {udp_port}"],
            cwd=ROOT, env=env, stdout=log, stderr=log,
        )
        try:
            # 1. both children start, no fault line, guided heartbeats.
            _, guided = wait_for_pid(log, "started guided")
            _, ingest = wait_for_pid(log, "started ingest")
            time.sleep(3.0)
            assert not pids(log, "guided fault"), "faulted while healthy:\n" + Path(log.name).read_text()
            print("PASS: stack up, guided heartbeat clean for 3 s")

            # 2. killed guided is a fault; ingest is untouched.
            os.kill(guided, signal.SIGKILL)
            wait_for(log, "guided fault")
            _, guided2 = wait_for_pid(log, "restarted guided", 1)
            assert guided2 != guided
            assert alive(ingest), "ingest was restarted for a guided fault"
            assert alive(guided2)
            print("PASS: guided kill => fault => respawn, ingest untouched")

            # 3. alive but not looping (SIGSTOP) is also a fault.
            os.kill(guided2, signal.SIGSTOP)
            wait_for(log, "guided fault: heartbeat stale")
            _, guided3 = wait_for_pid(log, "restarted guided", 2)
            assert guided3 not in (guided, guided2)
            assert alive(ingest)
            print("PASS: stale heartbeat (SIGSTOP) caught without killing ingest")

            # 4. shutdown is clean.
            sup.send_signal(signal.SIGTERM)
            assert sup.wait(timeout=8) == 0, "supervisor exit code"
            for pid in (guided3, ingest):
                deadline = time.monotonic() + 3
                while alive(pid) and time.monotonic() < deadline:
                    time.sleep(0.05)
                assert not alive(pid), f"child {pid} outlived the supervisor"
            print("PASS: SIGTERM shuts the stack down and exits 0")

            text = Path(log.name).read_text()
            if "spawn with sched attrs failed" in text:
                print("NOTE: this kernel refused SCHED_FIFO/runmask (expected off-QNX)")
            print("ALL PASS")
        finally:
            if sup.poll() is None:
                sup.kill()
                sup.wait(timeout=5)
            for suffix in ("", "-frames", "-depth"):
                Path("/dev/shm", (world + suffix)[1:]).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
