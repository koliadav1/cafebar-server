import secrets

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from app.realtime.websocket_manager import manager
from app.realtime.events import handle_event
from jose import JWTError, jwt

from app.database import engine, Base
from app.routers import users, auth, menu, orders, reviews, supplies, shifts, ingredients, booking, resume, recommendations, statistics
from app.scheduler.scheduler import schedule_booking_updater, start_scheduler, scheduler
from app.config import Config

#Планировщик завершения бронирований по итсечении времени
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LIFESPAN] Запуск планировщика")
    start_scheduler()

    print("[LIFESPAN] Планирование задачи обновления бронирований")
    schedule_booking_updater()

    try:
        print("[LIFESPAN] Передача управления")
        yield
    finally:
        print("[LIFESPAN] Остановка планировщика")
        scheduler.shutdown(wait=False)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

security = HTTPBasic()

#Проверка пароля пользователя
def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = secrets.compare_digest(credentials.password, Config.SWAGGER_PASSWORD)
    if not correct_password:
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(verify_password)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Документация")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(credentials: HTTPBasicCredentials = Depends(verify_password)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)

# Подключаем роутеры
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(ingredients.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(supplies.router)
app.include_router(shifts.router)
app.include_router(booking.router)
app.include_router(resume.router)
app.include_router(recommendations.router)
app.include_router(statistics.router)

Base.metadata.create_all(bind=engine)

#Проверка токенов
async def verify_websocket_token(token: str):
    try:
        payload = jwt.decode(token, Config.HASH_SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        if user_id is None or role is None:
            return None
        return {"user_id": user_id, "role": role}
    except JWTError:
        return None

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    try:
        init_msg = await websocket.receive_json()
        token = init_msg.get("token")
        if not token:
            await websocket.close(code=1008) 
            return
        
        user_data = await verify_websocket_token(token)
        if not user_data:
            await websocket.close(code=1008)
            return

        if str(user_data["user_id"]) != client_id:
            await websocket.close(code=1008)
            return
        
        await manager.connect(client_id, websocket, user_data["role"])

        while True:
            data = await websocket.receive_json()
            await handle_event(client_id, data)

    except WebSocketDisconnect:
        await manager.disconnect(client_id)

# health-check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}