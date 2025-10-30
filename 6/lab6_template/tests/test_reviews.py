import pytest
from flask import url_for
from app.models import db, User, Course, Category, Review
from app.repositories import ReviewRepository


class TestReviews:
    """Тесты для функциональности отзывов"""

    def test_create_review_model(self, app):
        """Тест создания модели отзыва"""
        with app.app_context():
            # Создаем тестовые данные
            user = User(first_name='Тест', last_name='Пользователь', login='testuser')
            user.set_password('password')
            
            category = Category(name='Тестовая категория')
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image'
            )
            
            review = Review(
                rating=5,
                text='Отличный курс!',
                course_id=1,
                user_id=1
            )
            
            # Проверяем, что модель создается корректно
            assert review.rating == 5
            assert review.text == 'Отличный курс!'
            assert review.course_id == 1
            assert review.user_id == 1

    def test_review_repository_add_review(self, app):
        """Тест добавления отзыва через репозиторий"""
        with app.app_context():
            # Создаем тестовые данные
            user = User(first_name='Тест', last_name='Пользователь', login='testuser')
            user.set_password('password')
            db.session.add(user)
            
            category = Category(name='Тестовая категория')
            db.session.add(category)
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image'
            )
            db.session.add(course)
            db.session.commit()
            
            # Создаем репозиторий и добавляем отзыв
            review_repo = ReviewRepository(db)
            review = review_repo.add_review(1, 1, 5, 'Отличный курс!')
            
            # Проверяем, что отзыв создан
            assert review.id is not None
            assert review.rating == 5
            assert review.text == 'Отличный курс!'
            assert review.course_id == 1
            assert review.user_id == 1

    def test_review_repository_get_reviews_by_course(self, app):
        """Тест получения отзывов по курсу"""
        with app.app_context():
            # Создаем тестовые данные
            user1 = User(first_name='Пользователь', last_name='1', login='user1')
            user1.set_password('password')
            user2 = User(first_name='Пользователь', last_name='2', login='user2')
            user2.set_password('password')
            db.session.add_all([user1, user2])
            
            category = Category(name='Тестовая категория')
            db.session.add(category)
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image'
            )
            db.session.add(course)
            db.session.commit()
            
            # Добавляем отзывы
            review_repo = ReviewRepository(db)
            review_repo.add_review(1, 1, 5, 'Отличный курс!')
            review_repo.add_review(2, 1, 4, 'Хороший курс!')
            
            # Получаем отзывы
            pagination = review_repo.get_reviews_by_course(1, sort_by='newest', page=1, per_page=10)
            reviews = pagination.items
            
            # Проверяем результат
            assert len(reviews) == 2
            assert reviews[0].rating == 4  # Сортировка по новизне (последний добавленный)
            assert reviews[1].rating == 5

    def test_review_repository_get_user_review_for_course(self, app):
        """Тест получения отзыва пользователя для курса"""
        with app.app_context():
            # Создаем тестовые данные
            user = User(first_name='Тест', last_name='Пользователь', login='testuser')
            user.set_password('password')
            db.session.add(user)
            
            category = Category(name='Тестовая категория')
            db.session.add(category)
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image'
            )
            db.session.add(course)
            db.session.commit()
            
            # Добавляем отзыв
            review_repo = ReviewRepository(db)
            review_repo.add_review(1, 1, 5, 'Отличный курс!')
            
            # Получаем отзыв пользователя
            user_review = review_repo.get_user_review_for_course(1, 1)
            
            # Проверяем результат
            assert user_review is not None
            assert user_review.rating == 5
            assert user_review.text == 'Отличный курс!'

    def test_review_repository_update_course_rating(self, app):
        """Тест пересчета рейтинга курса"""
        with app.app_context():
            # Создаем тестовые данные
            user1 = User(first_name='Пользователь', last_name='1', login='user1')
            user1.set_password('password')
            user2 = User(first_name='Пользователь', last_name='2', login='user2')
            user2.set_password('password')
            db.session.add_all([user1, user2])
            
            category = Category(name='Тестовая категория')
            db.session.add(category)
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image',
                rating_sum=0,
                rating_num=0
            )
            db.session.add(course)
            db.session.commit()
            
            # Добавляем отзывы
            review_repo = ReviewRepository(db)
            review_repo.add_review(1, 1, 5, 'Отличный курс!')
            review_repo.add_review(2, 1, 3, 'Нормальный курс!')
            
            # Пересчитываем рейтинг
            review_repo.update_course_rating(1)
            
            # Проверяем результат
            updated_course = db.session.get(Course, 1)
            assert updated_course.rating_sum == 8  # 5 + 3
            assert updated_course.rating_num == 2
            assert updated_course.rating == 4.0  # 8 / 2

    def test_review_sorting(self, app):
        """Тест сортировки отзывов"""
        with app.app_context():
            # Создаем тестовые данные
            user1 = User(first_name='Пользователь', last_name='1', login='user1')
            user1.set_password('password')
            user2 = User(first_name='Пользователь', last_name='2', login='user2')
            user2.set_password('password')
            user3 = User(first_name='Пользователь', last_name='3', login='user3')
            user3.set_password('password')
            db.session.add_all([user1, user2, user3])
            
            category = Category(name='Тестовая категория')
            db.session.add(category)
            
            course = Course(
                name='Тестовый курс',
                short_desc='Короткое описание',
                full_desc='Полное описание',
                category_id=1,
                author_id=1,
                background_image_id='test_image'
            )
            db.session.add(course)
            db.session.commit()
            
            # Добавляем отзывы с разными рейтингами
            review_repo = ReviewRepository(db)
            review_repo.add_review(1, 1, 5, 'Отличный курс!')
            review_repo.add_review(2, 1, 2, 'Плохой курс!')
            review_repo.add_review(3, 1, 4, 'Хороший курс!')
            
            # Тест сортировки по новизне
            pagination_newest = review_repo.get_reviews_by_course(1, sort_by='newest', page=1, per_page=10)
            newest_reviews = pagination_newest.items
            assert newest_reviews[0].rating == 4  # Последний добавленный
            assert newest_reviews[1].rating == 2
            assert newest_reviews[2].rating == 5
            
            # Тест сортировки по положительным
            pagination_positive = review_repo.get_reviews_by_course(1, sort_by='positive', page=1, per_page=10)
            positive_reviews = pagination_positive.items
            assert positive_reviews[0].rating == 5  # Самый высокий рейтинг
            assert positive_reviews[1].rating == 4
            assert positive_reviews[2].rating == 2
            
            # Тест сортировки по отрицательным
            pagination_negative = review_repo.get_reviews_by_course(1, sort_by='negative', page=1, per_page=10)
            negative_reviews = pagination_negative.items
            assert negative_reviews[0].rating == 2  # Самый низкий рейтинг
            assert negative_reviews[1].rating == 4
            assert negative_reviews[2].rating == 5

