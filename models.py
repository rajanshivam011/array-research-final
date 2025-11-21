from extensions import db

class AuthorSheet(db.Model):
    __tablename__ = "author_sheet"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    info = db.Column(db.Text)

    tables = db.relationship("AuthorTable", backref="sheet", lazy=True)


class AuthorTable(db.Model):
    __tablename__ = "author_table"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(db.Integer, db.ForeignKey("author_sheet.id"), nullable=False)
    title = db.Column(db.String(255))

    positions = db.relationship("AuthorPosition", backref="table", lazy=True)


class AuthorPosition(db.Model):
    __tablename__ = "author_position"

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("author_table.id"), nullable=False)
    level = db.Column(db.String(100))
    amount = db.Column(db.String(100))
    status = db.Column(db.String(200))
