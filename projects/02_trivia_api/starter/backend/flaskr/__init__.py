import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, DELETE')
        return response

    @app.route("/categories")
    def get_categories():
        try:
            all_categories = Category.query.order_by(Category.id).all()

            categories = {}
            for category in all_categories:
                categories[category.id] = category.type

            if len(all_categories) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'categories': categories
            })

        except AttributeError:
            abort(422)


    @app.route("/questions")
    def get_questions():
        try:
            # Get questions
            questions = Question.query.order_by(Question.id)
            current_questions = paginate_questions(request, questions)

            # Get categories
            all_categories = Category.query.order_by(Category.id).all()

            categories = {}
            for category in all_categories:
                categories[category.id] = category.type

            if len(current_questions) == 0 or len(all_categories) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions.all()),
                'categories': categories,
                'current_category': None
            })
        except AttributeError:
            abort(422)

    @app.route("/questions/<int:Q_id>", methods=['DELETE'])
    def delete_questions(Q_id):
        try:
            question = Question.query.filter(Question.id == Q_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
            })

        except AttributeError:
            abort(422)

    @app.route("/questions", methods=['POST'])
    def create_questions():
        try:
            body = request.get_json()

            new_question = body.get('question')
            new_answer = body.get('answer')
            new_difficulty = body.get('difficulty')
            new_category = body.get('category')

            question = Question(question=new_question,
                                answer=new_answer,
                                difficulty=new_difficulty,
                                category=new_category)
            question.insert()

            return jsonify({
                'success': True,
            })

        except AttributeError:
            abort(422)

    @app.route("/questions/search", methods=['POST'])
    def search_questions():
        try:
            body = request.get_json()
            search_string = body.get('searchTerm', None)

            questions = list(Question.query.filter(Question.question.ilike("%"+search_string+"%")))

            current_questions = [question.format() for question in questions]

            if len(current_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(current_questions),
                'current_category': None
            })

        except AttributeError:
            abort(422)

    @app.route("/categories/<int:cat_id>/questions", methods=['GET'])
    def get_questions_id(cat_id):
        try:
            questions = Question.query\
                        .filter(Question.category == cat_id)\
                        .all()
            current_questions = [question.format() for question in questions]

            if len(current_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(current_questions),
                'current_category': cat_id
            })

        except AttributeError:
            abort(422)

    @app.route("/quizzes", methods=['POST'])
    def quiz_questions():
        try:
            body = request.get_json()

            prev_questions = body.get('previous_questions')
            num_prev_questions = len(prev_questions)
            quiz_category = body.get('quiz_category')

            cat_id = quiz_category['id']
            output = {}

            if (cat_id == 0):
                questions = Question.query\
                            .filter(Question.id.notin_(prev_questions))\
                            .all()

            else:
                questions = Question.query\
                            .filter(Question.category == cat_id)\
                            .filter(Question.id.notin_(prev_questions))\
                            .all()

            if len(questions) > 0:
                new_question = questions[random.randrange
                                         (0, len(questions))].format()
                output['question'] = new_question['question']
                output['answer'] = new_question['answer']
                output['id'] = new_question['id']

                return jsonify({
                    'success': True,
                    'question': output
                })

            if len(questions) == 0:

                return jsonify({
                    'success': True
                })

        except AttributeError:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422  
    return app

# Pagination
def paginate_questions(request, questions):
    page = request.args.get('page', 1, type=int)

    paginated = questions.paginate(page=page, per_page=QUESTIONS_PER_PAGE,
                                   error_out=True,
                                   max_per_page=QUESTIONS_PER_PAGE)

    current_questions = [question.format() for question in paginated.items]

    return current_questions

    