import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
client = gspread.authorize(creds)

# ---- Replace with YOUR sheet ID ----
SHEET_ID = "1RchuSMJIgulr2u6ThjttZ79MMKuDtZKmO7ounsO1j0I"
sheet = client.open_by_key(SHEET_ID).sheet1

def add_booking(name, email, service, date):
    sheet.append_row([name, email, service, date])
