import pytest
from unittest.mock import Mock, patch

from app.models.reviews import Review


class TestReviewsRouter:
    # Тест получения всех отзывов админом
    @pytest.mark.asyncio
    async def test_get_all_reviews_as_admin(self, admin_client, test_db):
        review1 = Review(user_id=1, order_id=1, rating=5)
        review2 = Review(user_id=2, order_id=2, rating=4)
        test_db.add_all([review1, review2])
        await test_db.commit()

        response = await admin_client.get("/reviews/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    # Тест получения отзывов клиентом (только своих)
    @pytest.mark.asyncio
    async def test_get_all_reviews_as_client(self, authenticated_client, test_db):
        review1 = Review(user_id=1, order_id=1, rating=5)
        review2 = Review(user_id=2, order_id=2, rating=4)
        test_db.add_all([review1, review2])
        await test_db.commit()

        response = await authenticated_client.get("/reviews/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == 1

    # Тест получения отзывов с неавторизованной ролью
    @pytest.mark.asyncio
    async def test_get_all_reviews_unauthorized(self, authenticated_client):
        authenticated_client.user.role = "Cook"
        response = await authenticated_client.get("/reviews/")
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест создания отзыва клиентом
    @pytest.mark.asyncio
    async def test_create_review_as_client(self, authenticated_client, sample_review_data, sample_review):
        with patch('app.services.review_service.create_review', return_value=sample_review):
            response = await authenticated_client.post("/reviews/", json=sample_review_data)
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == sample_review.user_id
            assert data["review_id"] == sample_review.review_id

    # Тест создания отзыва не-клиентом
    @pytest.mark.asyncio
    async def test_create_review_as_non_client(self, admin_client, sample_review_data):
        response = await admin_client.post("/reviews/", json=sample_review_data)
        assert response.status_code == 403
        assert "Только клиенты могут оставлять отзывы" in response.json()["detail"]

    # Тест получения отзывов пользователя админом
    @pytest.mark.asyncio
    async def test_get_reviews_by_user_as_admin(self, admin_client, test_db):
        review = Review(user_id=1, order_id=1, rating=5)
        test_db.add(review)
        await test_db.commit()

        response = await admin_client.get("/reviews/user/1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == 1

    # Тест получения отзывов пользователя не-админом
    @pytest.mark.asyncio
    async def test_get_reviews_by_user_as_non_admin(self, authenticated_client):
        response = await authenticated_client.get("/reviews/user/1")
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест получения отзыва по ID
    @pytest.mark.asyncio
    async def test_get_review_by_id(self, client, test_db):
        review = Review(user_id=1, order_id=1, rating=5, comment="Тестовый отзыв")
        test_db.add(review)
        await test_db.commit()

        response = await client.get(f"/reviews/{review.review_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["review_id"] == review.review_id
        assert data["comment"] == "Тестовый отзыв"

    # Тест получения несуществующего отзыва
    @pytest.mark.asyncio
    async def test_get_review_by_id_not_found(self, client):
        response = await client.get("/reviews/999")
        assert response.status_code == 404
        assert "Отзыв не найден" in response.json()["detail"]

    # Тест обновления отзыва владельцем
    @pytest.mark.asyncio
    async def test_update_review_as_owner(self, authenticated_client, sample_review):
        with patch('app.services.review_service.update_review') as mock_update:
            sample_review.rating = 5
            sample_review.comment = "Обновленный комментарий"
            mock_update.return_value = sample_review
            
            update_data = {
                "order_id": sample_review.order_id,
                "rating": 5,
                "comment": "Обновленный комментарий"
            }

            response = await authenticated_client.put(f"/reviews/{sample_review.review_id}", json=update_data) 
            assert response.status_code == 200
            data = response.json()
            assert data["rating"] == 5
            assert data["comment"] == "Обновленный комментарий"

    # Тест обновления чужого отзыва
    @pytest.mark.asyncio
    async def test_update_review_as_non_owner(self, authenticated_client):
        mock_review = Mock(spec=Review)
        mock_review.review_id = 1
        mock_review.user_id = 2

        with patch('app.services.review_service.get_review_by_id', return_value=mock_review):
            update_data = {
                "order_id": 1,
                "rating": 5,
                "comment": "Обновленный комментарий"
            }

            response = await authenticated_client.put("/reviews/1", json=update_data)

            assert response.status_code == 403
            assert "только свои отзывы" in response.json()["detail"]

    # Тест удаления отзыва админом
    @pytest.mark.asyncio
    async def test_delete_review_as_admin(self, admin_client, sample_review):
        with patch('app.services.review_service.delete_review') as mock_delete:
            mock_delete.return_value = sample_review
            response = await admin_client.delete(f"/reviews/{sample_review.review_id}")
            assert response.status_code == 200

    # Тест удаления отзыва владельцем
    @pytest.mark.asyncio
    async def test_delete_review_as_owner(self, authenticated_client, sample_review):
        with patch('app.services.review_service.delete_review', return_value=sample_review):
            response = await authenticated_client.delete(f"/reviews/{sample_review.review_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["review_id"] == sample_review.review_id

    # Тест ответа на отзыв админом
    @pytest.mark.asyncio
    async def test_respond_to_review_as_admin(self, admin_client, sample_review):
        with patch('app.services.review_service.respond_to_review') as mock_respond:
            sample_review.admin_response = "Спасибо за отзыв!"
            mock_respond.return_value = sample_review
            
            response_data = {"admin_response": "Спасибо за отзыв!"}
            response = await admin_client.post(f"/reviews/{sample_review.review_id}/response", json=response_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["admin_response"] == "Спасибо за отзыв!"

    # Тест ответа на отзыв не-админом
    @pytest.mark.asyncio
    async def test_respond_to_review_as_non_admin(self, authenticated_client):
        response_data = {
            "admin_response": "Спасибо за отзыв!"
        }

        response = await authenticated_client.post("/reviews/1/response", json=response_data)

        assert response.status_code == 403
        assert "Только админы могут отвечать на отзывы" in response.json()["detail"]