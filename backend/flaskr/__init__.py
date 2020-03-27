import logging
import random
import flask as fsk
import flask_cors as fc
import models

QUESTIONS_PER_PAGE = 10


def valid_and_cast(data, types, optional=None, cast=True):
    """Performs flat type-checking for input data.

    Args:
      data: (dict) Data to be type-checked
      types: (dict) Type map of each element in `data`
      optional: (set) Optional keys
      cast: (bool) If True, cast the element before type-check

    Returns:
      A shallow copy of `data`, with values casted if applicable.
    """
    optional = optional or set()
    missing = set(types) - set(data) - optional
    if missing:
        fsk.abort(400)

    unknowns = set(data) - set(types)
    if unknowns:
        fsk.abort(400)

    out = {}
    for k, t in types.items():
        if k in data:
            v = data[k]
            if v is not None and cast:
                try:
                    v = t(v)
                except BaseException:
                    pass
            if not isinstance(v, t):
                fsk.abort(400)
            out[k] = v

    return out


def error_json(code, message):
    return fsk.jsonify({"success": False, "error": code, "message": message})


def create_app(test_config=None):
    # create and configure the app
    app = fsk.Flask(__name__)
    models.setup_db(app)

    # Set up CORS.
    fc.CORS(app)

    #   Use the after_request decorator to set Access-Control-Allow
    #   Allow '*' for origins.
    #   Allow methods GET, POST & DELETE
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,DELETE")
        return response

    # Create an endpoint to handle GET requests for all available categories.
    @app.route("/categories", methods=["GET"])
    @fc.cross_origin()
    def get_categories():
        cats = models.Category.query
        return fsk.jsonify({
            "success": True,
            "categories": {c.id: c.type for c in cats},
        })

    #   Create an endpoint to get questions based on category.
    #   The category id should be non-negative.
    #   A zero category id fetches all questions regardless of categories.
    @app.route("/categories/<int:cid>/questions", methods=["GET"])
    @fc.cross_origin()
    def get_questions_by_category(cid):
        # Retrieve arguments
        try:
            page = max(int(fsk.request.args.get("page", 0)), 0)
        except BaseException:
            page = 0

        # Get questions by category
        query = models.Question.query.order_by(models.Question.id)
        if cid != 0:
            cat = models.Category.query.get(cid)
            if cat is None:
                fsk.abort(404)
            query = query.filter(models.Question.category == cid)

        total_questions = query.count()

        # Paginate if applicable
        if page > 0:
            query = query.paginate(
                page=page, per_page=QUESTIONS_PER_PAGE).items

        qs = [q.format() for q in query]
        return fsk.jsonify({
            "success": True,
            "questions": qs,
            "total_questions": total_questions,
        })

    #   Create a POST endpoint to get questions based on a search term.
    #   Questions containing the `search` term (case-insensitive) are returned.
    #   If `search` is not given, all questions are returned.
    #   The `page` parameter can optionally be provided for paginated return.
    @app.route("/questions", methods=["GET"])
    @fc.cross_origin()
    def search_questions():
        # Retrieve arguments
        search_term = fsk.request.args.get("search")
        try:
            page = max(int(fsk.request.args.get("page", 0)), 0)
        except BaseException:
            page = 0

        # Retrieve questions
        query = models.Question.query.order_by(models.Question.id)
        if search_term:
            query = query.filter(
                models.Question.question.ilike(f"%{search_term}%"))
        count = query.count()

        # Paginate if applicable
        if page > 0:
            query = query.paginate(
                page=page, per_page=QUESTIONS_PER_PAGE).items

        return fsk.jsonify({
            "success": True,
            "questions": [q.format() for q in query],
            "total_questions": count,
        })

    #   Create an endpoint to POST a new question, which will require the
    #   question and answer text, category ID, and difficulty score (+ve int).
    @app.route("/questions", methods=["POST"])
    @fc.cross_origin()
    def create_question():
        data = fsk.request.get_json()

        # Type-check
        types = {
            "question": str,
            "answer": str,
            "category": int,
            "difficulty": int,
        }

        data = valid_and_cast(data, types)

        # Sanity-check
        cid = data["category"]
        if models.Category.query.get(cid) is None or data["difficulty"] < 1:
            fsk.abort(422)

        # Create question
        qtn = models.Question(**data)
        db = models.db
        try:
            qtn.insert()
            q_data = qtn.format()
            logging.info(f"Created question: {q_data}")
            return fsk.jsonify({"success": True, "id": q_data["id"]})
        except BaseException:
            db.session.rollback()
            logging.exception(
                f"Failed to add new question with content: {data}")
            fsk.abort(500)
        finally:
            db.session.close()

    # Create an endpoint to get question by ID.
    @app.route("/questions/<int:qid>", methods=["GET"])
    @fc.cross_origin()
    def get_question(qid):
        q = models.Question.query.get(qid)
        if q is None:
            fsk.abort(404)
        return fsk.jsonify({"success": True, "question": q.format()})

    # Create an endpoint to delete question by ID.
    @app.route("/questions/<int:qid>", methods=["DELETE"])
    @fc.cross_origin()
    def delete_question(qid):
        # Check question existence
        question = models.Question.query.get(qid)
        if question is None:
            fsk.abort(404)

        # Delete question
        db = models.db
        q_data = question.format()
        try:
            question.delete()
            logging.info(f"Deleted question: {q_data}.")
        except BaseException:
            db.session.rollback()
            logging.exception(f"Failed to delete question: {q_data}")
            fsk.abort(500)
        finally:
            db.session.close()

        return fsk.jsonify({"success": True, "id": q_data["id"]})

    #   Create a POST endpoint to get questions to play the quiz.
    #   This endpoint takes category and previous question parameters
    #   and return a random questions within the given category,
    #   if provided, and that is not one of the previous questions.
    @app.route("/quizzes", methods=["POST"])
    @fc.cross_origin()
    def get_quiz_question():
        data = fsk.request.get_json()

        # Type-check
        data = valid_and_cast(data, {"previous_questions": list,
                                     "quiz_category": int})

        # Sanity-check
        pqids = data["previous_questions"]
        cid = data["quiz_category"]
        try:
            pqids = [int(qid) for qid in pqids]
        except BaseException:
            fsk.abort(422)

        # Get questions IDs with previous ones excluded
        query = (models.Question
                       .query.with_entities(models.Question.id)
                       .filter(~models.Question.id.in_(pqids)))
        if cid != 0:
            query = query.filter(models.Question.category == cid)
        qids = [q.id for q in query]

        q = None
        if qids:
            # Choose question randomly
            qid = qids[random.randint(0, len(qids) - 1)]
            q = models.Question.query.get(qid).format()  # Get chosen question
        return fsk.jsonify({"success": True, "question": q})

    # Create error handler for status 400
    @app.errorhandler(400)
    def bad_request_error(error):
        return error_json(400, "bad request"), 400

    # Create error handler for status 404
    @app.errorhandler(404)
    def not_found_error(error):
        return error_json(404, "resource not found"), 404

    # Create error handler for status 422
    @app.errorhandler(422)
    def unprocessable_error(error):
        return error_json(422, "unprocessable"), 422

    # Create error handler for status 500
    @app.errorhandler(500)
    def server_error(error):
        return error_json(500, "server error"), 500

    return app
