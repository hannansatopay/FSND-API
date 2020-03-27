from flask_sqlalchemy import SQLAlchemy

database_name = "trivia_test"
database_url = "hannan:sqlDev@localhost:5432"
database_path = f"postgresql://{database_url}/{database_name}"

db = SQLAlchemy()


def setup_db(app, database_path=database_path):
    """
    setup_db(app)
        binds a flask application and a SQLAlchemy service
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()


class Question(db.Model):
    """
    Question

    """
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String)
    answer = db.Column(db.String)
    category = db.Column(db.Integer,
                         db.ForeignKey("categories.id"),
                         nullable=False)
    category_ = db.relationship("Category", back_populates="questions")
    difficulty = db.Column(db.Integer)

    def __init__(self, question, answer, category, difficulty):
        self.question = question
        self.answer = answer
        self.category = category
        self.difficulty = difficulty

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "difficulty": self.difficulty,
        }


class Category(db.Model):
    """
    Category

    """
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    questions = db.relationship("Question", back_populates="category_")

    def __init__(self, type):
        self.type = type

    def format(self):
        return {
            "id": self.id,
            "type": self.type,
        }

    def __repr__(self):
        return self.type
