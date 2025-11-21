from app import app, db
from models import AuthorPosition
import pandas as pd

with app.app_context():
    df = pd.read_excel("static/uploads/Array Research Author Positions (2).xlsx")

    for _, row in df.iterrows():
        entry = AuthorPosition(
            journal_name=row.get("Journal Name", ""),
            author_name=row.get("Author Name", ""),
            position=row.get("Position", ""),
            price=row.get("Price", "")
        )
        db.session.add(entry)

    db.session.commit()
    print("Migration Complete!")
