from app.models import Review
from sqlalchemy import desc, asc

class ReviewRepository:
    def __init__(self, db):
        self.db = db

    def get_reviews_by_course(self, course_id, sort_by='newest', page=1, per_page=5):
        """Получить отзывы по курсу с пагинацией и сортировкой"""
        query = self.db.select(Review).filter_by(course_id=course_id)
        
        # Применяем сортировку
        if sort_by == 'newest':
            query = query.order_by(desc(Review.created_at))
        elif sort_by == 'positive':
            query = query.order_by(desc(Review.rating), desc(Review.created_at))
        elif sort_by == 'negative':
            query = query.order_by(asc(Review.rating), desc(Review.created_at))
        
        return self.db.paginate(query, page=page, per_page=per_page)

    def get_recent_reviews_by_course(self, course_id, limit=5):
        """Получить последние отзывы по курсу"""
        query = self.db.select(Review).filter_by(course_id=course_id).order_by(desc(Review.created_at)).limit(limit)
        return self.db.session.execute(query).scalars()

    def get_user_review_for_course(self, user_id, course_id):
        """Получить отзыв пользователя для конкретного курса"""
        return self.db.session.execute(
            self.db.select(Review).filter_by(user_id=user_id, course_id=course_id)
        ).scalar()

    def add_review(self, user_id, course_id, rating, text):
        """Добавить новый отзыв"""
        review = Review(
            user_id=user_id,
            course_id=course_id,
            rating=rating,
            text=text
        )
        self.db.session.add(review)
        self.db.session.commit()
        return review

    def update_course_rating(self, course_id):
        """Пересчитать рейтинг курса на основе отзывов"""
        from app.models import Course
        
        # Получаем все отзывы для курса
        reviews = self.db.session.execute(
            self.db.select(Review).filter_by(course_id=course_id)
        ).scalars()
        
        rating_sum = sum(review.rating for review in reviews)
        rating_num = sum(1 for review in reviews)
        
        # Обновляем курс
        course = self.db.session.get(Course, course_id)
        if course:
            course.rating_sum = rating_sum
            course.rating_num = rating_num
            self.db.session.commit()

