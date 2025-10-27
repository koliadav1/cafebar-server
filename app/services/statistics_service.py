from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import date

from app.models.orders import Order, OrderStatus
from app.models.order_assignments import OrderAssignment
from app.models.user import UserRole
from app.schemas.statistics import StaffStatsOut, StaffStatsWithRankOut

# Получить статистику по работе персонала
async def get_staff_statistics(
    db: AsyncSession,
    user_id: int,
    role: UserRole,
    is_admin: bool = False,
    start_date: date | None = None,
    end_date: date | None = None
) -> list[StaffStatsOut] | dict:
    stmt = select(
        OrderAssignment.user_id,
        OrderAssignment.role,
        func.count(OrderAssignment.order_id).label("orders_count")
    ).join(Order, OrderAssignment.order_id == Order.order_id)

    if role == UserRole.WAITER:
        stmt = stmt.where(Order.status == OrderStatus.COMPLETED)
    elif role in [UserRole.COOK, UserRole.BARKEEPER]:
        stmt = stmt.where(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.READY]))

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(OrderAssignment.user_id, OrderAssignment.role)

    result = await db.execute(stmt)
    stats = result.all()

    if is_admin:
        return [StaffStatsWithRankOut(
            user_id=s.user_id,
            role=s.role,
            orders_count=s.orders_count,
            rating=None,
            total_employees=None
        ) for s in stats]

    same_role_stats = [s for s in stats if s.role == role]
    same_role_stats.sort(key=lambda x: x.orders_count, reverse=True)

    rating = None
    current_stats = None
    for idx, s in enumerate(same_role_stats, start=1):
        if s.user_id == user_id:
            rating = idx
            current_stats = s
            break

    if current_stats is None:
        return [StaffStatsWithRankOut(
            user_id=user_id,
            role=role,
            orders_count=0,
            rating=None,
            total_employees=len(same_role_stats)
        )]

    return [StaffStatsWithRankOut(
        user_id=current_stats.user_id,
        role=current_stats.role,
        orders_count=current_stats.orders_count,
        rating=rating,
        total_employees=len(same_role_stats)
    )]