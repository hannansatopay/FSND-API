from urllib import parse as url_parse
import hashlib
import unittest

from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category


ERROR_400 = {"success": False, "error": 400, "message": "bad request"}
ERROR_404 = {"success": False, "error": 404, "message": "resource not found"}
ERROR_422 = {"success": False, "error": 422, "message": "unprocessable"}
ERROR_500 = {"success": False, "error": 500, "message": "server error"}


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_url = "hannan:sqlDev@localhost:5432"
        self.database_path = f"postgresql://{self.database_url}/{self.database_name}"
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def validate_response(self, res, code, types, allow_none=False):
        self.assertEqual(res.status_code, code)
        self.assertTrue(res.is_json)
        data = res.json
        self.assertTrue(isinstance(data, dict))
        self.assertSetEqual(set(data), set(types))
        for k in types:
            v = data[k]
            if allow_none and v is None:
                continue
            self.assertTrue(isinstance(v, types[k]))

        return data

    def compare(self, res, code, expected):
        self.assertEqual(res.status_code, code)
        self.assertTrue(res.is_json)
        data = res.json
        self.assertDictEqual(data, expected)

    # Endpoint: /categories
    #  Methods: GET
    def testGetCategories(self):
        expected = {
            "success": True,
            "categories": {str(c.id): c.type for c in Category.query},
        }
        res = self.client().get("/categories")
        self.compare(res, 200, expected)

    # Endpoint: /categories/<int:cid>/questions
    #  Methods: GET
    def testGetQuestionsByCategory(self):
        cid = 1
        query = (Question.query
                 .order_by(Question.id)
                 .filter(Question.category == cid))
        count = query.count()
        expected = {
            "success": True,
            "total_questions": count,
            "questions": [q.format() for q in query],
        }
        res = self.client().get(f"/categories/{cid}/questions")
        self.compare(res, 200, expected)

    # Endpoint: /categories/<int:cid>/questions?page=<int>
    #  Methods: GET
    def testGetQuestionsByCategoryPaged(self):
        cid = 1
        page = 1
        query = (Question.query
                 .order_by(Question.id)
                 .filter(Question.category == cid))
        q_paged = query.paginate(page=page, per_page=QUESTIONS_PER_PAGE).items
        qs = [q.format() for q in q_paged]
        count = query.count()
        expected = {
            "success": True,
            "total_questions": count,
            "questions": qs,
        }
        res = self.client().get(f"/categories/{cid}/questions?page={page}")
        self.compare(res, 200, expected)

    # Endpoint: /categories/0/questions
    #  Methods: GET
    def testGetQuestionsByCategoryAll(self):
        cid = 0
        query = Question.query.order_by(Question.id)
        qs = [q.format() for q in query]
        expected = {
            "success": True,
            "total_questions": query.count(),
            "questions": qs,
        }
        res = self.client().get(f"/categories/{cid}/questions")
        self.compare(res, 200, expected)

    # Endpoint: /categories/0/questions?page=<int>
    #  Methods: GET
    def testGetQuestionsByCategoryAllPaged(self):
        cid = 0
        page = 2
        query = Question.query.order_by(Question.id)
        q_paged = query.paginate(page=2, per_page=QUESTIONS_PER_PAGE).items
        qs = [q.format() for q in q_paged]
        count = query.count()
        expected = {
            "success": True,
            "total_questions": count,
            "questions": qs,
        }
        res = self.client().get(f"/categories/{cid}/questions?page={page}")
        self.compare(res, 200, expected)

    # Endpoint: /categories/<int:cid>/questions
    #  Methods: GET
    def testGetQuestionsByCategoryError404(self):
        cid = -1
        res = self.client().get(f"/categories/{cid}/questions")
        self.compare(res, 404, ERROR_404)

    # Endpoint: /questions
    #  Methods: GET
    def testGetQuestions(self):
        query = Question.query.order_by(Question.id)
        count = query.count()
        expected = {
            "success": True,
            "total_questions": count,
            "questions": [q.format() for q in query],
        }
        res = self.client().get("/questions")
        self.compare(res, 200, expected)

    # Endpoint: /questions?search=<str>
    #  Methods: GET
    def testSearchQuestions(self):
        search_term = "title"
        url_query = url_parse.urlencode({"search": search_term})
        query = (Question.query
                         .order_by(Question.id)
                         .filter(Question.question.ilike(f"%{search_term}%")))
        count = query.count()
        expected = {
            "success": True,
            "total_questions": count,
            "questions": [q.format() for q in query],
        }
        res = self.client().get(f"/questions?{url_query}")
        self.compare(res, 200, expected)

    # Endpoint: /questions?search=<str>
    #  Methods: GET
    def testSearchQuestionsEmptyResult(self):
        m = hashlib.sha256(b"This does not exist. (Probably)")
        search_term = m.hexdigest()
        url_query = url_parse.urlencode({"search": search_term})
        expected = {
            "success": True,
            "total_questions": 0,
            "questions": [],
        }

        res = self.client().get(f"/questions?{url_query}")
        self.compare(res, 200, expected)

    # Endpoint: /questions?search=<str>&page=<int>
    #  Methods: GET
    def testSearchQuestionsPaged(self):
        search_term = "w"
        page = 1
        url_query = url_parse.urlencode({"search": search_term, "page": page})
        query = (Question.query
                         .order_by(Question.id)
                         .filter(Question.question.ilike(f"%{search_term}%")))
        count = query.count()
        query = query.paginate(page=page, per_page=QUESTIONS_PER_PAGE).items
        qs = [q.format() for i, q in enumerate(query)
              if i < min(count, QUESTIONS_PER_PAGE)]
        expected = {
            "success": True,
            "total_questions": count,
            "questions": qs,
        }
        res = self.client().get(f"/questions?{url_query}")
        self.compare(res, 200, expected)

    # Endpoint: /questions/<int:qid>
    #  Methods: GET
    def testGetQuestionByID(self):
        q = Question.query.order_by(Question.id).first()
        if q is None:
            return

        expected = {
            "success": True,
            "question": q.format(),
        }

        res = self.client().get(f"/questions/{q.id}")
        self.compare(res, 200, expected)

    # Endpoint: /questions/<int:qid>
    #  Methods: GET
    def testGetQuestionByIDError404(self):
        qid = -1
        res = self.client().get(f"/questions/{qid}")
        self.compare(res, 404, ERROR_404)

    # Endpoint: /questions
    #  Methods: POST, DELETE
    def testCreateAndDeleteQuestion(self):
        # Test Create
        inputs = {
            "question": "Test Question",
            "answer": "Test Answer",
            "category": 1,
            "difficulty": 1,
        }

        r1 = self.client().post("/questions", json=inputs)
        data = self.validate_response(r1, 200, {"success": bool, "id": int})
        self.assertEqual(data["success"], True)
        qid = inputs["id"] = data["id"]

        q = Question.query.get(qid)
        try:
            self.assertDictEqual(inputs, q.format())

            # Test Delete
            expected = {"success": True, "id": qid}
            r2 = self.client().delete(f"/questions/{qid}")
            self.compare(r2, 200, expected)
            self.assertIsNone(Question.query.get(qid))
        except AssertionError:
            if q:
                q.delete()
            raise

    # Endpoint: /questions
    #  Methods: POST
    def testCreateQuestionError400(self):
        res = self.client().post("/questions", json={})
        self.compare(res, 400, ERROR_400)

    # Endpoint: /questions
    #  Methods: POST
    def testCreateQuestionError422(self):
        inputs = {
            "question": "Failed Question",
            "answer": "Failed Answer",
            "category": 999,
            "difficulty": 1,
        }

        res = self.client().post("/questions", json=inputs)
        self.compare(res, 422, ERROR_422)

    # Endpoint: /questions
    #  Methods: DELETE
    def testDeleteQuestionError404(self):
        qid = -1
        res = self.client().delete(f"/questions/{qid}")
        self.compare(res, 404, ERROR_404)

    # Endpoint: /quizzes
    #  Methods: POST
    def testGetFirstQuizQuestion(self):
        cid = 1
        inputs = {
            "previous_questions": [],
            "quiz_category": cid,
        }
        res = self.client().post("/quizzes", json=inputs)
        data = self.validate_response(
            res, 200, {"success": bool, "question": dict})
        self.assertEqual(data["success"], True)
        rq = data["question"]
        self.assertEqual(rq["category"], cid)
        q = Question.query.get(rq["id"])
        self.assertDictEqual(rq, q.format())

    # Endpoint: /quizzes
    #  Methods: POST
    def testGetSecondQuizQuestion(self):
        cid = 1
        q = (Question.query
                     .filter(Question.category == cid)
                     .order_by(Question.id)
                     .first())
        inputs = {"previous_questions": [q.id], "quiz_category": cid}
        res = self.client().post("/quizzes", json=inputs)
        data = self.validate_response(
            res, 200, {"success": bool, "question": dict}, allow_none=True)
        self.assertEqual(data["success"], True)
        rq = data["question"]
        if rq is None:
            return
        self.assertEqual(rq["category"], q.category)
        self.assertNotEqual(rq["id"], q.id)

    # Endpoint: /quizzes
    #  Methods: POST
    def testGetSecondQuizQuestionNonCategorized(self):
        cid = 0
        q = Question.query.order_by(Question.id).first()
        inputs = {"previous_questions": [q.id], "quiz_category": cid}
        res = self.client().post("/quizzes", json=inputs)
        data = self.validate_response(
            res, 200, {"success": bool, "question": dict}, allow_none=True)
        self.assertEqual(data["success"], True)
        rq = data["question"]
        if rq is None:
            return
        self.assertNotEqual(rq["id"], q.id)

    # Endpoint: /quizzes
    #  Methods: POST
    def testGetQuizQuestionError400(self):
        inputs = {"previous_questions": [], "quiz_category": "string"}
        res = self.client().post("/quizzes", json=inputs)
        self.compare(res, 400, ERROR_400)

    # Endpoint: /quizzes
    #  Methods: POST
    def testGetQuizQuestionError422(self):
        inputs = {"previous_questions": ["non-integer"], "quiz_category": 0}
        res = self.client().post("/quizzes", json=inputs)
        self.compare(res, 422, ERROR_422)

    def tearDown(self):
        """Executed after each test"""
        pass


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
