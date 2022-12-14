from http import client
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import json



app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket, id:int):
        msg = json.dumps({'id':'', 'message':message })
        await websocket.send_json(json.loads(msg))

    async def broadcast(self, message: str, id:str):
        for connection in self.active_connections:
            msg = json.dumps({'id':id, 'message':message})
            await connection.send_json(json.loads(msg))

manager = ConnectionManager()


@app.get('/')
def chat(request: Request):
    return templates.TemplateResponse("index.html",  {"request": request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket, client_id)
            await manager.broadcast(f"Client  says: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client left the chat", client_id)
