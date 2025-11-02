from app.realtime.websocket_manager import manager

async def handle_event(sender_id: str, data: dict):
    event_type = data.get("type")
    action = data.get("action")
    payload = data.get("payload", {})

    if not event_type or not action:
        return

    # Обработка позиций меню
    if event_type == "menu":
        if action in {"create", "update", "delete"}:
            await manager.broadcast({
                "type": f"menu_{action}",
                "payload": payload
            }, roles={"Client"})

    # Обработка заказов
    elif event_type == "order":
        user_id = payload.get("user_id")

        if user_id:
            await manager.send_json(str(user_id), {
                "type": f"order_{action}",
                "payload": payload
            })

        await manager.broadcast({
            "type": f"order_{action}",
            "payload": payload
        }, roles={"Barkeeper", "Waiter", "Cook"})

    # Обработка смен
    elif event_type == "shift":
        if action in {"create", "update", "delete"}:
            await manager.broadcast({
                "type": f"shift_{action}",
                "payload": payload
            }, roles={"Barkeeper", "Waiter", "Cook"})

    # Обработка бронирований
    elif event_type == "reservation":
        if action in {"create", "update", "delete"}:
            await manager.broadcast({
                "type": f"reservation_{action}",
                "payload": payload
            }, roles={"Client", "Admin"})
            
    # Обработка отдельных позиций заказа
    elif event_type == "order_item":
        if action == "update":
            await manager.broadcast({
                "type": "order_item_update",
                "payload": payload
            }, roles={"Barkeeper", "Cook", "Waiter"})