from typing import Dict
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, dict] = {}

    async def connect(self, client_id: str, websocket: WebSocket, role: str) -> None:
        self.active_connections[client_id] = {"ws": websocket, "role": role}
        print(f"[WebSocket] Подключен пользователь {client_id} с ролью '{role}'")

    async def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)
        print(f"[WebSocket] Отключен пользователь {client_id}")

    async def send_json(self, client_id: str, message: dict) -> None:
        conn = self.active_connections.get(client_id)
        if conn:
            try:
                await conn["ws"].send_json(message)
                print(f"[WebSocket] Отправлено сообщение пользователю {client_id}: {message}")
            except Exception as e:
                print(f"[WebSocket] Ошибка отправки пользователю {client_id}: {e}")

    async def broadcast(self, message: dict, roles: set = None) -> None:
        json_ready_message = jsonable_encoder(message)
        print(f"[WebSocket] Рассылка события (фильтр ролей: {roles})")
        for client_id, conn_info in list(self.active_connections.items()):
            try:
                if roles is None or conn_info["role"] in roles:
                    await conn_info["ws"].send_json(json_ready_message)
            except Exception as e:
                print(f"Ошибка при отправке сообщения через WebSocket клиенту {client_id}: {e}")
                continue

manager = ConnectionManager()