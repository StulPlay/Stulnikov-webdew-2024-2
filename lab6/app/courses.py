from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')

PER_PAGE = 10

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

REVIEW_PARAMS = [
    'text', 'rating', 'course_id', 'user_id'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def review_params():
    return { p: request.form.get(p) or None for p in REVIEW_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html', courses=courses, categories=categories, pagination=pagination, search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html', categories=categories, users=users, course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html', categories=categories, users=users, course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)

    reviews = db.session.query(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc()).limit(5).all()
    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.query(Review).filter_by(course_id=course_id, user_id=current_user.id).first()
    return render_template('courses/show.html', course=course, reviews=reviews, user_review=user_review)

@bp.route('/create/<int:course_id>/review/', methods=['POST'])
@login_required
def review_create(course_id):
    review = Review()
    course_id = review_params().get('course_id')
    origin = request.form.get('origin', 'course')
    existing_review = db.session.query(Review).filter_by(course_id=course_id, user_id=current_user.id).first()

    if existing_review:
        flash('Вы уже оставили отзыв на этот курс.', 'info')
        if origin == "all":
            return redirect(url_for('courses.reviews', course_id=course_id))
        else:
            return redirect(url_for('courses.show', course_id=course_id))

    try:
        review = Review(**review_params())
        db.session.add(review)

        course = db.session.query(Course).filter_by(id=course_id).first()
        course.rating_sum = course.rating_sum + int(review_params().get('rating'))
        course.rating_num = course.rating_num + 1

        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()

        if origin == "all":
            return redirect(url_for('courses.reviews', review=review, course_id=course_id))
        else:
            return render_template('courses/show.html', review=review, course_id=course_id)

    flash(f'Отзыв был успешно добавлен!', 'success')
    if origin == "all":
        return redirect(url_for('courses.reviews', course_id=course_id))
    else:
        return redirect(url_for('courses.show', course_id=course_id))

@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    sort_order = request.args.get('sort_order', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 3

    query = db.session.query(Review).filter_by(course_id=course_id)
    if sort_order == 'positive':
        query = query.order_by(Review.rating.desc())
    elif sort_order == 'negative':
        query = query.order_by(Review.rating)
    else:
        query = query.order_by(Review.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reviews = pagination.items

    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.query(Review).filter_by(course_id=course_id, user_id=current_user.id).first()

    return render_template('courses/reviews.html', course_id=course_id, reviews=reviews, pagination=pagination, sort_order=sort_order, user_review=user_review)
