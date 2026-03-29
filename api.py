from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from app.auth.dependencies import get_current_user
from app.models.user import User

import subprocess
import sys
import json
import threading

app = FastAPI(title="Subscription Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

agent_process = None
lock = threading.Lock()

def start_agent():
    global agent_process
    agent_process = subprocess.Popen(
        [sys.executable, "agent_runner.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

start_agent()

@app.get("/chat-stream")
def chat_stream(
    message: str,
    current_user: User = Depends(get_current_user)
):
    def event_generator():
        with lock:
            try:
                agent_process.stdin.write(
                    json.dumps({"message": message, "user_id": current_user.id}) + "\n"
                )
                agent_process.stdin.flush()
                while True:
                    line = agent_process.stdout.readline()
                    if not line:
                        break
                    data = json.loads(line)
                    if "stream" in data:
                        yield f"data: {data['stream']}\n\n"
                    if "end" in data:
                        break
            except BrokenPipeError:
                start_agent()
                yield "data: [Agent restarted, please try again]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
def health():
    return {"status": "running"}
