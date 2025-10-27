"""Test data migration

Revision ID: 1fc7ee2f3a88
Revises: a2e9959f5e4f
Create Date: 2025-10-26 16:53:40.271366

"""
from typing import Sequence, Union
from alembic import op
import bcrypt


# revision identifiers, used by Alembic.
revision: str = '1fc7ee2f3a88'
down_revision: Union[str, Sequence[str], None] = 'a2e9959f5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Пользователи и роли
    hashed_password1 = bcrypt.hashpw("123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_password2 = bcrypt.hashpw("456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_password3 = bcrypt.hashpw("789".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_password4 = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_password5 = bcrypt.hashpw("321".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    op.execute(f"""
        INSERT INTO users (user_id, username, password_hash, email, phone_number, role, created_at) VALUES
        (1, 'admin', '{hashed_password1}', 'admin@restaurant.com', '+79990000001', 'ADMIN', NOW()),
        (2, 'waiter_ivan', '{hashed_password2}', 'ivan@restaurant.com', '+79990000002', 'WAITER', NOW()),
        (3, 'cook_petr', '{hashed_password3}', 'petr@restaurant.com', '+79990000003', 'COOK', NOW()),
        (4, 'barkeeper_anna', '{hashed_password4}', 'anna@restaurant.com', '+79990000004', 'BARKEEPER', NOW()),
        (5, 'client_alex', '{hashed_password5}', 'alex@client.com', '+79990000005', 'CLIENT', NOW())
    """)

    # 2. Смены сотрудников
    op.execute("""
        INSERT INTO staff_shifts (shift_id, user_id, shift_date, shift_start, shift_end) VALUES
        (1, 2, CURRENT_DATE, '09:00:00', '17:00:00'),
        (2, 3, CURRENT_DATE, '10:00:00', '18:00:00'),
        (3, 4, CURRENT_DATE + INTERVAL '1 day', '12:00:00', '20:00:00')
    """)

    # 3. Ингредиенты
    op.execute("""
        INSERT INTO ingredients (ingredient_id, name, unit, quantity, threshold) VALUES
        (1, 'Говядина', 'кг', 10.0, 2.0),
        (2, 'Картофель', 'кг', 25.0, 5.0),
        (3, 'Морковь', 'кг', 8.0, 2.0),
        (4, 'Лук', 'кг', 6.0, 1.0),
        (5, 'Сливки', 'л', 5.0, 1.0),
        (6, 'Кофе', 'кг', 3.0, 0.5)
    """)

    # 4. Заказы поставок
    op.execute("""
        INSERT INTO supply_orders (supply_order_id, ingredient_id, ordered_quantity, order_date, status, price, delivery_date) VALUES
        (1, 1, 5.0, NOW() - INTERVAL '2 days', 'DELIVERED', 2500.00, NULL),
        (2, 2, 10.0, NOW() - INTERVAL '1 day', 'PENDING', 800.00, NULL),
        (3, 6, 2.0, NOW(), 'PENDING', 1500.00, NOW() + INTERVAL '2 days')
    """)

    # 5. Пункты меню
    op.execute("""
        INSERT INTO menu_items (item_id, name, price, is_available, category, description) VALUES
        (1, 'Борщ украинский', 350.00, true, 'SOUP', 'Наваристый борщ со сметаной и зеленью'),
        (2, 'Стейк Рибай', 890.00, true, 'MAIN', 'Сочный стейк прожарки medium с овощами гриль'),
        (3, 'Цезарь с курицей', 420.00, true, 'MAIN', 'Салат с курицей, сыром пармезан и соусом цезарь'),
        (4, 'Тирамису', 280.00, true, 'DESSERT', 'Классический итальянский десерт'),
        (5, 'Эспрессо', 120.00, true, 'DRINK', 'Крепкий черный кофе'),
        (6, 'Мохито', 320.00, false, 'DRINK', 'Освежающий коктейль с мятой и лаймом')
    """)

    # 6. Связь блюд и ингредиентов
    op.execute("""
        INSERT INTO menu_item_ingredients (item_id, ingredient_id, required_quantity) VALUES
        (1, 2, 0.3), (1, 3, 0.2), (1, 4, 0.1),
        (2, 1, 0.4), (4, 5, 0.1), (5, 6, 0.02)
    """)

    # 7. Изображения блюд
    op.execute("""
        INSERT INTO menu_item_images (image_id, item_id, image_url) VALUES
        (1, 1, '/images/borsh.jpg'),
        (2, 2, '/images/steak.jpg'),
        (3, 4, '/images/tiramisu.jpg'),
        (4, 5, '/images/espresso.jpg')
    """)

    # 8. Заказы
    op.execute("""
        INSERT INTO orders (order_id, user_id, table_number, total_price, status, comment, order_date) VALUES
        (1, 5, 5, 770.00, 'COMPLETED', 'Без лука в борще', NOW() - INTERVAL '3 hours'),
        (2, 5, 3, 1310.00, 'IN_PROGRESS', 'Стейк прожарки medium', NOW() - INTERVAL '30 minutes'),
        (3, 5, 7, 400.00, 'PENDING', NULL, NOW() - INTERVAL '5 minutes')
    """)

    # 9. Элементы заказов
    op.execute("""
        INSERT INTO order_items (order_item_id, order_id, item_id, quantity, price, status) VALUES
        (1, 1, 1, 2, 350.00, 'PENDING'),
        (2, 1, 5, 1, 70.00, 'PENDING'),
        (3, 2, 2, 1, 890.00, 'IN_PROGRESS'),
        (4, 2, 3, 1, 420.00, 'IN_PROGRESS'),
        (5, 3, 4, 1, 280.00, 'PENDING'),
        (6, 3, 5, 1, 120.00, 'PENDING')
    """)

    # 10. Назначения на заказы
    op.execute("""
        INSERT INTO order_assignments (id, order_id, user_id, role) VALUES
        (1, 1, 2, 'WAITER'), (2, 1, 3, 'COOK'),
        (3, 2, 2, 'WAITER'), (4, 2, 3, 'COOK'),
        (5, 3, 2, 'WAITER')
    """)

    # 11. Бронирования столов
    op.execute("""
        INSERT INTO table_bookings (booking_id, table_number, customer_name, phone_number, user_id, status, booking_time, duration_minutes) VALUES
        (1, 2, 'Иван Петров', '+79991112233', 5, 'COMPLETED', NOW() - INTERVAL '1 day', 120),
        (2, 4, 'Мария Сидорова', '+79994445566', NULL, 'CONFIRMED', NOW() + INTERVAL '2 hours', 90),
        (3, 1, 'Алексей Козлов', '+79997778899', 5, 'CANCELLED', NOW() + INTERVAL '1 day', 60)
    """)

    # 12. Отзывы
    op.execute("""
        INSERT INTO reviews (review_id, user_id, order_id, rating, comment, review_date, admin_response) VALUES
        (1, 5, 1, 5, 'Отличный борщ! Обслуживание на высоте.', NOW() - INTERVAL '2 hours', NULL),
        (2, 5, 2, 4, 'Стейк хороший, но ждали долго. Персонал вежливый.', NOW() - INTERVAL '45 minutes', 'Благодарим за отзыв! Улучшим скорость приготовления.')
    """)

    # 13. Резюме
    op.execute("""
        INSERT INTO resumes (resume_id, content, phone_number, status, response) VALUES
        (1, 'Опыт работы официантом 3 года. Ищу работу в вашем ресторане.', '+79990001111', 'PENDING', NULL),
        (2, 'Шеф-повар с 10-летним опытом. Готов рассмотреть предложение.', '+79990002222', 'ACCEPTED', 'Приглашаем на собеседование в пятницу в 15:00')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM resumes WHERE resume_id IN (1, 2)")
    op.execute("DELETE FROM reviews WHERE review_id IN (1, 2)")
    op.execute("DELETE FROM table_bookings WHERE booking_id IN (1, 2, 3)")
    op.execute("DELETE FROM order_assignments WHERE id IN (1, 2, 3, 4, 5)")
    op.execute("DELETE FROM order_items WHERE order_item_id IN (1, 2, 3, 4, 5, 6)")
    op.execute("DELETE FROM orders WHERE order_id IN (1, 2, 3)")
    op.execute("DELETE FROM menu_item_images WHERE image_id IN (1, 2, 3, 4)")
    op.execute("DELETE FROM menu_item_ingredients WHERE (item_id, ingredient_id) IN ((1,2), (1,3), (1,4), (2,1), (4,5), (5,6))")
    op.execute("DELETE FROM menu_items WHERE item_id IN (1, 2, 3, 4, 5, 6)")
    op.execute("DELETE FROM supply_orders WHERE supply_order_id IN (1, 2, 3)")
    op.execute("DELETE FROM ingredients WHERE ingredient_id IN (1, 2, 3, 4, 5, 6)")
    op.execute("DELETE FROM staff_shifts WHERE shift_id IN (1, 2, 3)")
    op.execute("DELETE FROM users WHERE user_id IN (1, 2, 3, 4, 5)")
