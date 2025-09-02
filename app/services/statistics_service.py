from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.models.orders import Order, OrderStatus
from app.models.order_assignments import OrderAssignment
from app.models.user import UserRole
from app.schemas.statistics import StaffStatsOut, StaffStatsWithRankOut

#Получить статистику по работе персонала
def get_staff_statistics(
    db: Session,
    user_id: int,
    role: UserRole,
    is_admin: bool = False,
    start_date: date | None = None,
    end_date: date | None = None
) -> list[StaffStatsOut] | dict:
    query = db.query(
        OrderAssignment.user_id,
        OrderAssignment.role,
        func.count(OrderAssignment.order_id).label("orders_count")
    ).join(Order, OrderAssignment.order_id == Order.order_id)

    if role == UserRole.WAITER:
        query = query.filter(Order.status == OrderStatus.COMPLETED)
    elif role in [UserRole.COOK, UserRole.BARKEEPER]:
        query = query.filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.READY]))

    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)

    query = query.group_by(OrderAssignment.user_id, OrderAssignment.role)
    stats = query.all()

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
