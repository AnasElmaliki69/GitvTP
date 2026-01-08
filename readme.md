from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# A single "current task" the agent can pull
CURRENT_TASK = {
    "task_id": 1,
    "task_name": "whoami",   # must be in agent whitelist
    "args": []
}

# Store replies in memory (for demo / grading screenshots)
REPLIES = []

@app.get("/task")
def get_task():
    # Agent polls here
    return jsonify(CURRENT_TASK)

@app.post("/reply")
def post_reply():
    data = request.get_json(force=True)
    data["server_received_at"] = datetime.utcnow().isoformat() + "Z"
    REPLIES.append(data)
    return jsonify({"status": "ok", "stored_replies": len(REPLIES)})

@app.get("/replies")
def get_replies():
    return jsonify(REPLIES)

@app.post("/set-task")
def set_task():
    """
    Teacher/demo endpoint: set a new task.
    Example body:
      {"task_id":2,"task_name":"date","args":[]}
    """
    global CURRENT_TASK
    data = request.get_json(force=True)

    # minimal validation
    if "task_id" not in data or "task_name" not in data:
        return jsonify({"error": "task_id and task_name required"}), 400

    CURRENT_TASK = {
        "task_id": int(data["task_id"]),
        "task_name": str(data["task_name"]),
        "args": data.get("args", [])
    }
    return jsonify({"status": "ok", "current_task": CURRENT_TASK})

if __name__ == "__main__":
    # listen on all interfaces so other VMs can reach it if needed
    app.run(host="0.0.0.0", port=8080, debug=True)
