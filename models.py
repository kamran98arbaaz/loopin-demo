from flask_sqlalchemy import SQLAlchemy # type: ignore

db = SQLAlchemy()

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
