import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.services.review_service import (
    get_all_reviews,
    create_review,
    get_reviews_by_user,
    get_review_by_id,
    update_review,
    delete_review,
    respond_to_review
)
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.models.reviews import Review


class TestReviewService:
    # Тест получения всех отзывов
    @pytest.mark.asyncio
    async def test_get_all_reviews(self, test_db, sample_review):
        result = await get_all_reviews(test_db)
        assert len(result) >= 1
        review_ids = [review.review_id for review in result]
        assert sample_review.review_id in review_ids

    # Тест создания отзыва
    @pytest.mark.asyncio
    async def test_create_review_success(self, test_db, sample_order):
        review_data = ReviewCreate(
            order_id=sample_order.order_id,
            rating=5,
            comment="Отличный сервис"
        )

        result = await create_review(test_db, review_data, sample_order.user_id)
        assert result.user_id == sample_order.user_id
        assert result.order_id == sample_order.order_id
        assert result.rating == 5
        assert result.comment == "Отличный сервис"

    # Тест создания отзыва к чужому заказу
    @pytest.mark.asyncio
    async def test_create_review_wrong_user(self, test_db, sample_order):
        review_data = ReviewCreate(
            order_id=sample_order.order_id,
            rating=5,
            comment="Отличный сервис"
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_review(test_db, review_data, 999)
        assert exc_info.value.status_code == 403

    # Тест получения отзывов пользователя
    @pytest.mark.asyncio
    async def test_get_reviews_by_user(self, test_db, sample_user, sample_review):
        result = await get_reviews_by_user(test_db, sample_user.user_id)
        assert len(result) == 1
        assert all(review.user_id == sample_user.user_id for review in result)

    # Тест получения отзыва по ID
    @pytest.mark.asyncio
    async def test_get_review_by_id(self, test_db, sample_review):
        result = await get_review_by_id(test_db, sample_review.review_id)
        assert result.review_id == sample_review.review_id

    # Тест обновления отзыва
    @pytest.mark.asyncio
    async def test_update_review_success(self, test_db, sample_review):
        update_data = ReviewUpdate(
            order_id=sample_review.order_id,
            rating=5,
            comment="Новый комментарий"
        )

        result = await update_review(test_db, sample_review.review_id, update_data)
        assert result.rating == 5
        assert result.comment == "Новый комментарий"

    # Тест обновления несуществующего отзыва
    @pytest.mark.asyncio
    async def test_update_review_not_found(self, test_db):
        update_data = ReviewUpdate(order_id=1, rating=5, comment="Комментарий")
        result = await update_review(test_db, 999, update_data)
        assert result is None

    # Тест удаления отзыва
    @pytest.mark.asyncio
    async def test_delete_review_success(self, test_db, sample_review):
        result = await delete_review(test_db, sample_review.review_id)
        assert result.review_id == sample_review.review_id
        
        db_result = await test_db.execute(select(Review).filter(Review.review_id == sample_review.review_id))
        db_review = db_result.scalar_one_or_none()
        assert db_review is None

    # Тест ответа на отзыв
    @pytest.mark.asyncio
    async def test_respond_to_review_success(self, test_db, sample_review):
        result = await respond_to_review(test_db, sample_review.review_id, "Спасибо за отзыв!")
        assert result.admin_response == "Спасибо за отзыв!"

    # Тест ответа на несуществующий отзыв
    @pytest.mark.asyncio
    async def test_respond_to_review_not_found(self, test_db):
        with pytest.raises(ValueError) as exc_info:
            await respond_to_review(test_db, 999, "Ответ")
        assert "Отзыв не найден" in str(exc_info.value)