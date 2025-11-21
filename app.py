from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
from werkzeug.security import generate_password_hash
from google.oauth2.service_account import Credentials
import google.auth.transport.requests
import gspread
import requests
import json
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from models import AuthorPosition


# --------------------------------------------------------
# INITIAL SETUP
# --------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Flask Config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret')

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from extensions import db
db.init_app(app)


# Mail Config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
mail = Mail(app)

# --------------------------------------------------------
# GOOGLE SHEETS CONFIG
# --------------------------------------------------------
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
SHEET_ID = os.getenv('SHEET_ID')
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet():
    """Connect to Google Sheet securely."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

# --------------------------------------------------------
# MODELS
# --------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    picture = db.Column(db.String(300))  # profile image link (optional)

    def __repr__(self):
        return f'<User {self.email}>'

# --------------------------------------------------------
# DATA CONTENT
# --------------------------------------------------------
SERVICES = [
    {'id': 1, 'title': 'PhD Thesis Writing', 'description': 'Complete thesis writing support from proposal to final submission', 'icon': '📚', 'image': 'thesis.png', 'price': 'Negotiable'},
    {'id': 2, 'title': 'Research Paper Publication', 'description': 'Expert assistance in publishing papers in reputed journals', 'icon': '📝', 'image': 'publication.png', 'price': 'Negotiable'},
    {'id': 3, 'title': 'Literature Review', 'description': 'Comprehensive literature review and analysis', 'icon': '🔍', 'image': 'literature.png', 'price': 'Negotiable'},
    {'id': 4, 'title': 'Plagiarism Check & Removal', 'description': 'Advanced plagiarism detection and content revision', 'icon': '✓', 'image': 'plagarism.png', 'price': 'Negotiable'},
    {'id': 5, 'title': 'Data Analysis', 'description': 'Statistical analysis using SPSS, R, Python, and more', 'icon': '📊', 'image': 'data.png', 'price': 'Negotiable'},
    {'id': 6, 'title': 'Research Proposal', 'description': 'Well-structured research proposals for your projects', 'icon': '📋', 'image': 'proposal.png', 'price': 'Negotiable'},
    {'id': 7, 'title': 'Manuscript Editing', 'description': 'Professional editing and proofreading services', 'icon': '✏️', 'image': 'editing.png', 'price': 'Negotiable'},
    {'id': 8, 'title': 'Synopsis Writing', 'description': 'Detailed synopsis preparation for research work', 'icon': '📄', 'image': 'synopsis.png', 'price': 'Negotiable'}
]

FULL_SERVICES = [
    {'id': 1, 'title': 'PhD Thesis Writing', 'description': 'Complete thesis writing support from proposal to final submission', 'image': 'phd.jpg', 'price': 'Negotiable'},
    {'id': 2, 'title': 'Research Paper Publication', 'description': 'Expert assistance in publishing papers in reputed journals', 'image': 'publication.jpg', 'price': 'Negotiable'},
    {'id': 3, 'title': 'Literature Review', 'description': 'Comprehensive literature review and analysis', 'image': 'literature.png', 'price': 'Negotiable'},
    {'id': 4, 'title': 'Plagiarism Check & Removal', 'description': 'Advanced plagiarism detection and content revision', 'image': 'plagiarism.jpg', 'price': 'Negotiable'},
    {'id': 5, 'title': 'Data Analysis', 'description': 'Statistical analysis using SPSS, R, Python, and more', 'image': 'data.jpg', 'price': 'Negotiable'},
    {'id': 6, 'title': 'Research Proposal', 'description': 'Well-structured research proposals for your projects', 'image': 'proposal.jpg', 'price': 'Negotiable'},
    {'id': 7, 'title': 'Manuscript Editing', 'description': 'Professional editing and proofreading services', 'image': 'editing.jpg', 'price': 'Negotiable'},
    {'id': 8, 'title': 'Synopsis Writing', 'description': 'Detailed synopsis preparation for research work', 'image': 'synopsis.jpg', 'price': 'Negotiable'}
]


# =========================
# JOURNAL SECTION DATA
# =========================



BLOG_POSTS = [
    {'id': 1, 'title': 'Common Pitfalls in Academic Publishing and How to Avoid Them', 'excerpt': 'Learn about the most common mistakes researchers make when publishing their work and how to avoid them.', 'image': 'blog1.jpg', 'date': '2024-10-15', 'author': 'Array Research Team'},
    {'id': 2, 'title': 'Why Choosing the Right Academic Support Can Transform Your Career?', 'excerpt': 'Discover how professional academic support can accelerate your research career and open new opportunities.', 'image': 'blog2.jpg', 'date': '2024-10-10', 'author': 'Dr. Sharma'},
    {'id': 3, 'title': 'From Manuscript to Publication: Navigating the Journey', 'excerpt': 'A comprehensive guide to taking your research from manuscript stage to successful publication.', 'image': 'blog3.jpg', 'date': '2024-10-05', 'author': 'Array Research Team'}
]

TESTIMONIALS = [
    {'name': 'Sophia Johnson', 'text': 'Array Research Academy provided exceptional guidance, and their editing services significantly improved my research paper.', 'rating': 5},
    {'name': 'Raj Patel', 'text': 'I highly recommend Array Research Academy for their professional writing services. They exceeded my expectations.', 'rating': 5},
    {'name': 'Aisha Khan', 'text': 'The team at Array Research Academy is outstanding. Their support was crucial in my research journey.', 'rating': 5}
]

# --------------------------------------------------------
# CONTEXT PROCESSOR
# --------------------------------------------------------
#from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# --------------------------------------------------------
# MAIN ROUTES
# --------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html', services=SERVICES[:4], testimonials=TESTIMONIALS, blog_posts=BLOG_POSTS[:3])

@app.route('/about')
def about():
    return render_template('about.html')



import pandas as pd
import os

# ======= JOURNAL DATA LOADING FROM EXCEL =======
import re
import pandas as pd
import os
from urllib.parse import quote

def extract_hyperlink(cell):
    """
    If cell contains Excel hyperlink formula, extract actual URL.
    """
    if isinstance(cell, str):
        # Case: proper http link
        if "http" in cell:
            parts = cell.split()
            for p in parts:
                if p.startswith("http"):
                    return p.strip()
    return None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


import re

import re
import pandas as pd
import os

# regex helpers
def load_journals_from_excel():
    import pandas as pd
    import os
    import re

    excel_path = os.path.join(BASE_DIR, "static", "uploads", "journals.xlsx")
    if not os.path.exists(excel_path):
        return {}

    excel_data = pd.read_excel(excel_path, sheet_name=None, header=None, engine='openpyxl')

    sheets_output = {}

    for sheet, df in excel_data.items():
        df = df.fillna("")
        journals = []
        block = []

        for _, row in df.iterrows():
            line = " ".join([str(x).strip() for x in row if str(x).strip()])

            if not line:      # empty row → journal complete
                if block:
                    journals.append(parse_journal_block(block))
                    block = []
                continue

            block.append(line)

        if block:   # last block
            journals.append(parse_journal_block(block))

        sheets_output[sheet] = journals

    return sheets_output


def parse_journal_block(block):
    """
    block example:
        [ "https://link.com",
          "Journal Name ...",
          "ISSN...",
          "Publication time...",
          "Price: 3.5k"
        ]
    """

    link = block[0] if block and block[0].startswith("http") else "#"

    # last price-like line
    price = "N/A"
    for line in reversed(block):
        if "price" in line.lower() or re.search(r"\d+\s*[kKlL]", line):
            price = line
            break

    details = block[1:] if len(block) > 1 else []

    return {
        "link": link,
        "details": details,
        "price": price
    }
JOURNALS_BY_SHEET = load_journals_from_excel()


# Author

# put near other imports
import re
import pandas as pd
import os

def parse_author_cell(cell):
    if not isinstance(cell, str):
        return {"price": "", "status": ""}
    parts = cell.strip().split()
    if len(parts) == 0:
        return {"price": "", "status": ""}
    return {"price": parts[0], "status": " ".join(parts[1:])}


def load_author_positions_from_excel(filepath=None):

    if filepath is None:
        filepath = os.path.join("static", "uploads", "Array Research Author Positions (2).xlsx")

    if not os.path.exists(filepath):
        print("Author Excel not found:", filepath)
        return []

    try:
        excel_data = pd.read_excel(filepath, sheet_name=None, header=None)
    except Exception as e:
        print("Error reading author excel:", e)
        return []

    all_sheets = []
    author_label_re = re.compile(r'^\s*Author\b', re.IGNORECASE)

    for sheet_name, df in excel_data.items():
        df = df.fillna("")
        nrows, ncols = df.shape

        sheet_info = []
        tables = []
        current_table = None
        in_table = False

        for r in range(nrows):
            row = [str(x).strip() for x in df.iloc[r].tolist()]
            lower_row = [c.lower() for c in row]

            # TRUE header row
            is_header = (
                any("position" in c for c in lower_row)
                and any(("amount" in c or "price" in c) for c in lower_row)
                and any("status" in c for c in lower_row)
            )

            # AVOID repeating "author position available"
            is_fake_title = any(
                "author position" in c.lower() for c in row if c
            )

            # Author line?
            has_author_label = any(author_label_re.match(c) for c in row if c)

            # ----------------------
            # SHEET INFO (before tables)
            # ----------------------
            if not in_table and not is_header and not has_author_label:
                # Skip fake titles from sheet info too
                if not is_fake_title:
                    text = " ".join([c for c in row if c])
                    if len(text.strip()) > 3:
                        sheet_info.append(text.strip())
                continue

            # ----------------------
            # TABLE START
            # ----------------------
            if is_header:

                # Push previous table
                if current_table:
                    tables.append(current_table)

                # FIND REAL HEADING ABOVE HEADER
                heading = ""
                for up in range(r - 1, -1, -1):
                    prev = [str(x).strip() for x in df.iloc[up].tolist()]
                    line = " ".join([c for c in prev if c])

                    if len(line) > 3 and not ("author position" in line.lower()):
                        heading = line
                        break

                current_table = {"title": heading, "authors": []}
                in_table = True

                # find column indexes
                author_col = next((i for i, c in enumerate(lower_row) if "position" in c or "author" in c), 0)
                amount_col = next((i for i, c in enumerate(lower_row) if "amount" in c or "price" in c), 1)
                status_col = next((i for i, c in enumerate(lower_row) if "status" in c), 2)

                current_table["_cols"] = {
                    "author": author_col,
                    "amount": amount_col,
                    "status": status_col
                }
                continue

            # ----------------------
            # DATA ROWS
            # ----------------------
            if in_table:
                # blank row ends table
                if all(not c for c in row):
                    if current_table and current_table["authors"]:
                        tables.append(current_table)
                    current_table = None
                    in_table = False
                    continue

                cols = current_table["_cols"]
                ai, bi, ci = cols["author"], cols["amount"], cols["status"]

                author_cell = row[ai]
                amount_cell = row[bi] if bi < len(row) else ""
                status_cell = row[ci] if ci < len(row) else ""

                # fix missing author
                if not author_cell:
                    for c in row:
                        if c.lower().startswith("author"):
                            author_cell = c
                            break

                if not author_cell or not re.search(r"Author", author_cell, re.I):
                    continue

                # clean author label
                level = re.sub(r'[:\-]', '', author_cell).strip()
                if not re.search(r'Author', level, re.I):
                    m = re.search(r'(\d+)', level)
                    if m:
                        level = f"Author {m.group(1)}"

                parsed = parse_author_cell(
                    status_cell if not amount_cell else f"{amount_cell} {status_cell}"
                )

                price = amount_cell or parsed["price"]
                status = status_cell or parsed["status"]

                current_table["authors"].append({
                    "level": level,
                    "price": price.strip(),
                    "status": status.strip()
                })

        if current_table and current_table["authors"]:
            tables.append(current_table)

        all_sheets.append({
            "sheet": sheet_name,
            "info": "\n".join(sheet_info),
            "tables": [{k: v for k, v in t.items() if k != "_cols"} for t in tables]
        })

    return all_sheets



@app.route('/authors')
def authors_cards():
    sheets = AuthorSheet.query.all()
    return render_template('author_cards.html', sheets=sheets)




@app.route('/service')
def services():
    return render_template('service.html', services=SERVICES)


@app.route('/journals')
def journals():
    # ensure fresh load on each request in dev if you want:
    # global JOURNALS_BY_SHEET
    # JOURNALS_BY_SHEET = load_journals_from_excel()
    return render_template('journals.html', journals_by_sheet=JOURNALS_BY_SHEET)




#@app.route('/journals')
#def journals():
 #   return render_template('service.html', services=FULL_SERVICES, journals=JOURNALS)

posts = [
    # 1
    {
        "id": "academic-publishing-pitfalls",
        "title": "Common Pitfalls in Academic Publishing and How to Avoid Them",
        "author": "arrayresearch3",
        "date": "Jan 4, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/publishing.jpg",
        "excerpt": "Publishing in academic journals is a critical milestone for researchers, yet it can be fraught with challenges. Learn how to avoid common pitfalls and strengthen your publication success.",
        "content": """
        <p>Publishing in academic journals is a critical milestone for researchers, yet it can be fraught with challenges. From selecting the right journal to adhering to strict submission guidelines, many factors can impact the success of your submission.</p>
        <p>Here, we explore common pitfalls in academic publishing strategies, how to avoid them, and how Array Research assists in navigating these challenges.</p>

        <h3>1. Choosing the Wrong Journal</h3>
        <p>A mismatch in scope or audience can lead to outright rejection.</p>
        <strong>Solution:</strong> Research potential journals thoroughly.<br>
        <strong>Array Research Helps:</strong> We assist in identifying SCOPUS and PubMed-indexed journals.

        <h3>2. Lack of Novelty or Significance</h3>
        <p>Editors look for originality and impact.</p>
        <strong>Solution:</strong> Highlight your research’s novelty.<br>
        <strong>Array Research Helps:</strong> We help articulate your work’s significance clearly.

        <h3>3. Poorly Written Manuscripts</h3>
        <p>Grammar or unclear structure reduces credibility.</p>
        <strong>Solution:</strong> Use professional editing.<br>
        <strong>Array Research Helps:</strong> We provide editing and proofreading services.

        <h3>4. Ignoring Journal Guidelines</h3>
        <p>Formatting errors delay or reject submissions.</p>
        <strong>Solution:</strong> Follow guidelines exactly.<br>
        <strong>Array Research Helps:</strong> We ensure adherence to journal-specific formatting.</p>

        <h3>Conclusion</h3>
        <p>By being mindful of these pitfalls, researchers can confidently publish high-quality work. Array Research is your trusted publication partner.</p>
        """
    },

    # 2
    {
        "id": "academic-support-career",
        "title": "Why Choosing the Right Academic Support Can Transform Your Career",
        "author": "arrayresearch3",
        "date": "Dec 21, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/support.jpg",
        "excerpt": "The correct academic assistance can help you realize your full potential. Discover how expert guidance transforms your research and career success.",
        "content": """
        <p>In today’s competitive academic landscape, choosing the right support can significantly shape your career trajectory.</p>

        <h3>The Challenges of Academic Excellence</h3>
        <ul>
            <li>Time constraints balancing studies, work, and research.</li>
            <li>Complex publication requirements.</li>
            <li>Skill gaps in writing and data analysis.</li>
        </ul>

        <h3>How Academic Support Helps</h3>
        <p>Academic assistance enhances confidence, skill development, and professional growth.</p>

        <h3>Array Research Advantage</h3>
        <p>We offer plagiarism checks, thesis writing, literature review, and career-aligned support customized to your goals.</p>

        <h3>Conclusion</h3>
        <p>Choosing Array Research means investing in a lifelong academic partnership dedicated to your success.</p>
        """
    },

    # 3
    {
        "id": "author-positioning-insights",
        "title": "From Manuscript to Publication: Navigating the Journey with Author Positioning Insights",
        "author": "arrayresearch3",
        "date": "Dec 18, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/manuscript.jpg",
        "excerpt": "Learn why author positioning matters in research publishing and how to ensure fair recognition for your contributions.",
        "content": """
        <p>Author positioning determines credit and recognition in scholarly publications.</p>

        <h3>What Is Author Positioning?</h3>
        <p>Order reflects contribution — first author leads research, last author supervises, middle authors support.</p>

        <h3>Common Challenges</h3>
        <ul>
            <li>Disagreements on contribution weight.</li>
            <li>Variations in journal author rules.</li>
        </ul>

        <h3>Array Research Assistance</h3>
        <p>We guide contribution mapping, conflict resolution, and ethical authorship alignment.</p>

        <h3>Conclusion</h3>
        <p>Proper author positioning builds collaboration and integrity. Array Research ensures every contributor receives fair recognition.</p>
        """
    },

    # 4
    {
        "id": "time-management-techniques",
        "title": "Successful Time Management Techniques for Master's and PhD Students",
        "author": "arrayresearch3",
        "date": "Dec 17, 2024",
        "read_time": "4 min read",
        "image": "images/blogs/time-management.jpg",
        "excerpt": "Time management is vital for research students balancing multiple responsibilities. Explore proven strategies for staying productive.",
        "content": """
        <h3>Key Techniques</h3>
        <ul>
            <li>Use Pomodoro, Trello, or Notion for structure.</li>
            <li>Apply Eisenhower Matrix to prioritize tasks.</li>
            <li>Take scheduled breaks to prevent burnout.</li>
        </ul>

        <h3>How Array Research Helps</h3>
        <p>We assist postgraduates with thesis planning, time scheduling, and organized progress tracking.</p>

        <h3>Conclusion</h3>
        <p>Mastering time management leads to efficient research and balanced academic life.</p>
        """
    },

    # 5
    {
        "id": "creating-perfect-abstract",
        "title": "Creating the Ideal Abstract: The Secret to Drawing in Reviewers and Readers",
        "author": "arrayresearch3",
        "date": "Dec 14, 2024",
        "read_time": "4 min read",
        "image": "images/blogs/abstract.jpg",
        "excerpt": "Your research begins with an abstract. Learn how to craft one that grabs attention and communicates your study’s essence effectively.",
        "content": """
        <p>A strong abstract summarizes your research and draws readers in instantly.</p>

        <h3>Essential Elements</h3>
        <ul>
            <li>Background and goal of research</li>
            <li>Methods and key results</li>
            <li>Impact and implications</li>
        </ul>

        <h3>Tips for Writing</h3>
        <ul>
            <li>Use active voice, avoid jargon</li>
            <li>Stay under 300 words</li>
            <li>Include relevant keywords</li>
        </ul>

        <p>Array Research helps craft abstracts that impress reviewers and boost visibility.</p>
        """
    },

    # 6
    {
        "id": "why-plagiarism-kills-research",
        "title": "Why Plagiarism Is the Death of Research Integrity – And How to Avoid It",
        "author": "arrayresearch3",
        "date": "Dec 13, 2024",
        "read_time": "4 min read",
        "image": "images/blogs/plagiarism.jpg",
        "excerpt": "Plagiarism destroys trust and credibility in research. Learn to maintain integrity and originality in your work.",
        "content": """
        <h3>The Consequences of Plagiarism</h3>
        <ul>
            <li>Loss of credibility and reputation</li>
            <li>Legal and ethical repercussions</li>
            <li>Stagnation of innovation</li>
        </ul>

        <h3>How to Avoid It</h3>
        <ul>
            <li>Always cite sources properly</li>
            <li>Use plagiarism detection tools like Turnitin</li>
            <li>Maintain detailed research notes</li>
        </ul>

        <p>Array Research provides plagiarism check and removal services ensuring academic originality.</p>
        """
    },

    # 7
    {
        "id": "publishing-in-scopus-pubmed",
        "title": "Top Tips for Getting Your Paper Published in Scopus and PubMed Journals",
        "author": "arrayresearch3",
        "date": "Dec 6, 2024",
        "read_time": "5 min read",
        "image": "images/blogs/scopus.jpg",
        "excerpt": "Increase your chances of acceptance in Scopus and PubMed journals with these proven publication strategies.",
        "content": """
        <h3>1. Choose the Right Journal</h3>
        <p>Match your paper’s scope and audience to the journal.</p>

        <h3>2. Follow Author Guidelines</h3>
        <p>Ensure formatting, word count, and citation accuracy.</p>

        <h3>3. Write a Compelling Abstract</h3>
        <p>Summarize your study with clarity and focus on contribution.</p>

        <h3>4. Ethical Practices</h3>
        <p>Be transparent about data and conflicts of interest.</p>

        <p>Array Research helps researchers prepare and refine manuscripts for top-tier publications.</p>
        """
    },

    # 8
    {
        "id": "conference-training-support",
        "title": "Unlock Knowledge and Collaboration with Conference, Workshop, and Training Support",
        "author": "arrayresearch3",
        "date": "Dec 3, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/conference.jpg",
        "excerpt": "Workshops and conferences drive professional growth. Discover how Array Research maximizes your participation success.",
        "content": """
        <h3>Why Events Matter</h3>
        <p>Conferences enable networking, collaboration, and exposure to new research trends.</p>

        <h3>Array Research Support</h3>
        <ul>
            <li>Presentation and paper writing assistance</li>
            <li>Event planning and promotional guidance</li>
            <li>Post-event engagement and feedback improvement</li>
        </ul>

        <p>We ensure your participation or event organization is seamless and impactful.</p>
        """
    },

    # 9
    {
        "id": "navigating-author-positions",
        "title": "Navigating Author Positions with Array Research: Ensuring Fair Recognition",
        "author": "arrayresearch3",
        "date": "Dec 3, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/author-position.jpg",
        "excerpt": "Understand author order and ensure fair credit for research contributions with professional guidance.",
        "content": """
        <p>Author positions reflect contribution and leadership within research publications.</p>

        <h3>Key Roles</h3>
        <ul>
            <li>First Author — main contributor</li>
            <li>Middle Authors — collaborative roles</li>
            <li>Last Author — supervisor or PI</li>
        </ul>

        <p>Array Research mediates authorship order, promotes fairness, and ensures publication ethics compliance.</p>
        """
    },

    # 10
    {
        "id": "plagiarism-check-services",
        "title": "Ensure Originality with Plagiarism Check and Removal Services by Array Research",
        "author": "arrayresearch3",
        "date": "Dec 3, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/plagiarism-check.jpg",
        "excerpt": "Maintain credibility and ensure originality with professional plagiarism detection and correction support.",
        "content": """
        <p>Plagiarism threatens originality and career credibility. Our services combine advanced tools with expert analysis to eliminate risks.</p>
        <ul>
            <li>Accurate plagiarism detection and correction</li>
            <li>Proper paraphrasing and citation adjustments</li>
            <li>Comprehensive originality reports</li>
        </ul>
        """
    },

    # 11
    {
        "id": "thesis-writing-support",
        "title": "Thesis Writing Made Easy with Customized Support by Array Research",
        "author": "arrayresearch3",
        "date": "Dec 2, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/thesis.jpg",
        "excerpt": "Simplify your thesis journey with tailored support from research design to final editing.",
        "content": """
        <p>Writing a thesis requires clarity, structure, and consistency. We help at every stage — topic selection, proposal drafting, research design, and editing.</p>
        <p>Our experts ensure your thesis meets all academic standards and submission requirements efficiently.</p>
        """
    },

    # 12
    {
        "id": "research-paper-services",
        "title": "Simplifying Academic Success with Research Paper Writing Services by Array Research",
        "author": "arrayresearch3",
        "date": "Dec 2, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/research-paper.jpg",
        "excerpt": "Professional research paper writing and editing support to help you publish confidently.",
        "content": """
        <p>From topic selection to publication, our team helps craft impactful research papers with precision and originality.</p>
        <ul>
            <li>Topic selection and proposal drafting</li>
            <li>Data analysis and literature review</li>
            <li>Formatting, proofreading, and submission help</li>
        </ul>
        """
    },

    # 13
    {
        "id": "phd-dissertation-services",
        "title": "PhD Dissertation Writing Services by Array Research: Your Partner in Academic Excellence",
        "author": "arrayresearch3",
        "date": "Dec 2, 2024",
        "read_time": "3 min read",
        "image": "images/blogs/dissertation.jpg",
        "excerpt": "Comprehensive dissertation writing support for PhD candidates from proposal to defense.",
        "content": """
        <p>PhD dissertations are complex and demanding. Array Research offers expert support for every phase — proposal, data analysis, writing, editing, and defense preparation.</p>
        <p>We ensure originality, structure, and academic rigor for successful submission.</p>
        """
    }
]
@app.route('/blog')
def blog():
    return render_template('blog.html', posts=posts)

@app.route('/blog/<post_id>')
def blog_detail(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        abort(404)
    return render_template('blog_detail.html', post=post)

@app.route('/event')
def event():
    return render_template('event.html')

@app.route('/book/<service_name>')
def book_service(service_name):
    service_details = next((s for s in SERVICES if s["title"].lower().replace(" ", "-") == service_name.lower()), None)
    if not service_details:
        return render_template('404.html'), 404
    return render_template('booking.html', service=service_details)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/programs')
def programs():
    return render_template('programs.html')

@app.route('/refer')
def refer():
    return render_template('refer.html')


# --------------------------------------------------------
# AUTHOR LIST ROUTE
# --------------------------------------------------------
@app.route("/author-list")
def author_list():
    return render_template("author_positions_list.html", author_positions=AUTHOR_POSITIONS)

# --------------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

# --------------------------------------------------------
# GOOGLE LOGIN
# --------------------------------------------------------
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(os.path.dirname(__file__), "client_secret.json")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

@app.route("/login/google")
def login_google():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="https://array-research-final.onrender.com/callback/google"

    )
    authorization_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback/google")
def callback_google():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="https://array-research-final.onrender.com/callback/google"

    )
    flow.fetch_token(authorization_response=request.url)
    if session["state"] != request.args["state"]:
        return redirect(url_for("login"))
    credentials = flow.credentials
    id_info = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                           headers={"Authorization": f"Bearer {credentials.token}"}).json()
    existing_user = User.query.filter_by(email=id_info["email"]).first()
    if not existing_user:
        db.session.add(User(name=id_info["name"], email=id_info["email"]))
        db.session.commit()
    session["user"] = id_info
    flash(f"Welcome {id_info['name']}!", "success")
    return redirect(url_for("index"))



# --------------------------------------------------------
# ADMIN ROUTES
# --------------------------------------------------------
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/admin/excel-manager', methods=['GET', 'POST'])
@admin_required
def admin_excel_manager():
    message = ""
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            save_path = os.path.join("static", "uploads", "Array Research Author Positions (2).xlsx")
            file.save(save_path)
            message = "Excel updated successfully!"
    return render_template('admin/excel_manager.html', message=message)

@app.route("/admin/run-migration")
def run_migration():
    if not session.get("admin"):
        return "Unauthorized", 401

    from author_migrate_from_excel import migrate_excel_to_db
    migrate_excel_to_db()
    return "Migration Completed!"



@app.route('/admin/author-positions')
@admin_required
def admin_author_positions():
    data = load_author_positions_from_excel()
    return render_template('admin/author_positions.html', data=data)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin/login.html", error="Invalid credentials")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    try:
        data = get_gsheet().get_all_records()
        return render_template("admin/bookings.html", bookings=data)
    except Exception as e:
        return f"Error loading Google Sheet: {e}"

@app.route("/admin/journals")
@admin_required
def admin_journals():
    try:
        journals = get_gsheet().get_all_records()
    except Exception as e:
        print("Error loading journals:", e)
        journals = []
    return render_template("admin/journals.html", journals=journals)

@app.route("/admin/journals/upload", methods=["POST"])
@admin_required
def upload_journal():
    file = request.files.get("file")
    title = request.form.get("title")
    if not file or not title:
        flash("⚠️ Title & PDF required!", "danger")
        return redirect(url_for("admin_journals"))
    upload_folder = os.path.join("static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    pdf_path = os.path.join(upload_folder, file.filename)
    file.save(pdf_path)
    sheet = get_gsheet()
    sheet.append_row([title, file.filename, datetime.now().strftime("%d-%m-%Y %H:%M:%S")])
    flash("✅ Journal uploaded successfully!", "success")
    return redirect(url_for("admin_journals"))

# --------------------------------------------------------
# API ROUTES (BOOKING + CONTACT)
# --------------------------------------------------------


@app.route('/api/book-service', methods=['POST'])
def book_service_api():
    try:
        data = request.get_json()
        name, email, service, details = data.get('name'), data.get('email'), data.get('service'), data.get('details')
        if not all([name, email, service]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        sheet = get_gsheet()
        sheet.append_row([name, email, service, details, datetime.now().strftime("%d-%m-%Y %H:%M:%S")])
        return jsonify({'success': True, 'message': 'Your booking has been received!'}), 200
    except Exception as e:
        print("🔥 GOOGLE SHEET ERROR:", e)
        return jsonify({'success': False, 'message': 'Error while saving booking!'}), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        name, email, phone, message = data.get('name'), data.get('email'), data.get('phone'), data.get('message')
        if not all([name, email, message]):
            return jsonify({'success': False, 'message': 'Please fill all required fields'}), 400
        msg = Message(subject=f'New Contact Form Submission from {name}',
                      recipients=['info@arrayresearch.co.in'],
                      body=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}")
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Thank you for contacting us! We will get back soon.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

# --------------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# --------------------------------------------------------
# RUN APP
# --------------------------------------------------------
#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5000)

def handler(event, context):
    return app