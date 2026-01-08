import time
import socket
import requests
import subprocess

SERVER = "http://127.0.0.1:8080"  # local server for safe TP
POLL_SECONDS = 3

# Whitelist of allowed tasks (safe)
ALLOWED = {
    "whoami": ["whoami"],
    "date": ["date"],
    "uname": ["uname", "-a"],
    "ls": ["ls", "-la"],
}

def machine_id() -> str:
    return socket.gethostname()

def run_task(task_name: str, args: list[str]) -> str:
    """
    Safe runner: only executes predefined commands from the whitelist.
    Ignores args for safety (or you can validate them strictly).
    """
    if task_name not in ALLOWED:
        return f"REFUSED: task '{task_name}' is not allowed."

    cmd = ALLOWED[task_name]

    try:
        completed = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=5
        )
        out = (completed.stdout or "") + (completed.stderr or "")
        return out.strip() if out.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: task timed out"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    mid = machine_id()
    last_task_id = None

    print(f"[agent] machine_id={mid}")
    print(f"[agent] polling {SERVER}/task every {POLL_SECONDS}s")

    while True:
        try:
            r = requests.get(f"{SERVER}/task", timeout=5)
            r.raise_for_status()
            task = r.json()

            task_id = task.get("task_id")
            task_name = task.get("task_name")
            args = task.get("args", [])

            if task_id == last_task_id:
                time.sleep(POLL_SECONDS)
                continue

            print(f"[agent] new task: id={task_id} name={task_name}")
            result = run_task(task_name, args)

            payload = {
                "machine_id": mid,
                "task_id": task_id,
                "task_name": task_name,
                "result": result
            }

            pr = requests.post(f"{SERVER}/reply", json=payload, timeout=5)
            pr.raise_for_status()
            print(f"[agent] sent reply: {pr.json()}")

            last_task_id = task_id

        except requests.RequestException as e:
            print(f"[agent] network error: {e}")

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
