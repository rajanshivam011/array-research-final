from app import app, db
from models import AuthorSheet, AuthorTable, AuthorPosition
from app import load_author_positions_from_excel

def migrate_excel_to_db():
    with app.app_context():

        # Load excel data
        sheets = load_author_positions_from_excel()

        # Clear old data
        AuthorPosition.query.delete()
        AuthorTable.query.delete()
        AuthorSheet.query.delete()
        db.session.commit()

        # Insert new structured data
        for sheet_data in sheets:
            sheet = AuthorSheet(
                name=sheet_data.get("sheet", ""),
                info=sheet_data.get("info", "")
            )
            db.session.add(sheet)
            db.session.flush()

            for table_data in sheet_data.get("tables", []):
                table = AuthorTable(
                    sheet_id=sheet.id,
                    title=table_data.get("title", "")
                )
                db.session.add(table)
                db.session.flush()

                for author in table_data.get("authors", []):
                    pos = AuthorPosition(
                        table_id=table.id,
                        level=author.get("level", ""),
                        amount=author.get("price", ""),
                        status=author.get("status", "")
                    )
                    db.session.add(pos)

        db.session.commit()
        print("Migration Completed from Excel")
