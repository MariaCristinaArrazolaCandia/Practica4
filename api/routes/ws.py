from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message):
        """
        Envía un mensaje a todos los clientes conectados.
        - Si message es dict, se envía como JSON.
        - Si es str u otra cosa, se convierte a string.
        """
        if isinstance(message, dict):
            payload = json.dumps(message, default=str)
        else:
            payload = str(message)

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                # Si falla, desconectamos esa conexión
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Leemos algo del cliente solo para mantener viva la conexión
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
