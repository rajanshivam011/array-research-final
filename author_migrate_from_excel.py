from app import app, db, load_author_positions_from_excel
from models import AuthorSheet, AuthorTable, AuthorPosition

with app.app_context():
    sheets = load_author_positions_from_excel()

    # safety: purana data clear (agar kuch hai)
    AuthorPosition.query.delete()
    AuthorTable.query.delete()
    AuthorSheet.query.delete()
    db.session.commit()

    for sheet_data in sheets:
        # sheet_data: { "sheet": name, "info": "...", "tables": [...] }
        sheet = AuthorSheet(
            name=sheet_data.get("sheet", ""),
            info=sheet_data.get("info", "")
        )
        db.session.add(sheet)
        db.session.flush()  # taa ki sheet.id mil jaye

        for t in sheet_data.get("tables", []):
            table = AuthorTable(
                sheet_id=sheet.id,
                title=t.get("title", "")
            )
            db.session.add(table)
            db.session.flush()

            for a in t.get("authors", []):
                pos = AuthorPosition(
                    table_id=table.id,
                    level=a.get("level", ""),
                    amount=a.get("price", ""),
                    status=a.get("status", "")
                )
                db.session.add(pos)

    db.session.commit()
    print("✅ Author data migrated from Excel to DB!")
