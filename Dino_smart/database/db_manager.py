import sqlite3 
import os
import json
from datetime import datetime

# Local storage folders configuration
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ["uploads", "images", "guides", "quizzes", "exports", "database"]

def ensure_folders_exist():
    """Create local directories if they do not exist."""
    for folder in FOLDERS:
        path = os.path.join(WORKSPACE_DIR, folder)
        if not os.path.exists(path):
            os.makedirs(path)

# Initialize paths
ensure_folders_exist()
DB_PATH = os.path.join(WORKSPACE_DIR, "database", "study_buddy.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Workspaces
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                subject TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # 2. Documents
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                topics_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 3. Study Guides
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_guides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL UNIQUE,
                mode TEXT NOT NULL,
                topics_json TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 4. Quizzes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 5. Quiz History
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                time_spent INTEGER NOT NULL, -- in seconds
                accuracy REAL NOT NULL,
                topic_analysis_json TEXT,
                date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )""")
            
            # 6. Notes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL UNIQUE,
                content TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 7. Bookmarks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'guide' | 'note' | 'formula' | 'term'
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 8. Flashcards
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                is_difficult INTEGER DEFAULT 0, -- 0 = false, 1 = true
                last_reviewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            # 9. Study Progress (active tracking)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_progress (
                id INTEGER PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                date TEXT NOT NULL, -- YYYY-MM-DD
                active_seconds INTEGER DEFAULT 0,
                sessions_count INTEGER DEFAULT 0,
                UNIQUE(workspace_id, date) ON CONFLICT REPLACE,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )""")
            
            conn.commit()

    # --- WORKSPACE METHODS ---
    def create_workspace(self, name, subject):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO workspaces (name, subject) VALUES (?, ?)", 
                    (name, subject)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_workspaces(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspaces ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_workspace(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
            conn.commit()

    # --- DOCUMENT METHODS ---
    def add_document(self, workspace_id, name, file_type, content, summary=None, topics=None):
        topics_json = json.dumps(topics) if topics else "[]"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO documents (workspace_id, name, file_type, content, summary, topics_json) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (workspace_id, name, file_type, content, summary, topics_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_documents(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, doc_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    # --- STUDY GUIDE METHODS ---
    def save_study_guide(self, workspace_id, mode, topics, content_dict):
        topics_json = json.dumps(topics)
        content_json = json.dumps(content_dict)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO study_guides (workspace_id, mode, topics_json, content_json)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(workspace_id) DO UPDATE SET
                   mode=excluded.mode, topics_json=excluded.topics_json, content_json=excluded.content_json, created_at=CURRENT_TIMESTAMP""",
                (workspace_id, mode, topics_json, content_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_study_guide(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_guides WHERE workspace_id = ?", (workspace_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["topics"] = json.loads(res["topics_json"])
                res["content"] = json.loads(res["content_json"])
                return res
            return None

    # --- QUIZ METHODS ---
    def save_quiz(self, workspace_id, difficulty, questions):
        questions_json = json.dumps(questions)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quizzes (workspace_id, difficulty, questions_json) VALUES (?, ?, ?)",
                (workspace_id, difficulty, questions_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_quizzes(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM quizzes WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            res = []
            for row in cursor.fetchall():
                d = dict(row)
                d["questions"] = json.loads(d["questions_json"])
                res.append(d)
            return res

    def add_quiz_history(self, workspace_id, quiz_id, score, total_questions, time_spent, accuracy, topic_analysis):
        topic_analysis_json = json.dumps(topic_analysis)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO quiz_history (workspace_id, quiz_id, score, total_questions, time_spent, accuracy, topic_analysis_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (workspace_id, quiz_id, score, total_questions, time_spent, accuracy, topic_analysis_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_quiz_history(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT qh.*, q.difficulty FROM quiz_history qh 
                   JOIN quizzes q ON qh.quiz_id = q.id
                   WHERE qh.workspace_id = ? ORDER BY qh.date_taken DESC""", 
                (workspace_id,)
            )
            res = []
            for row in cursor.fetchall():
                d = dict(row)
                d["topic_analysis"] = json.loads(d["topic_analysis_json"]) if d["topic_analysis_json"] else {}
                res.append(d)
            return res

    # --- NOTES METHODS ---
    def save_notes(self, workspace_id, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO notes (workspace_id, content) VALUES (?, ?)
                   ON CONFLICT(workspace_id) DO UPDATE SET content=excluded.content, updated_at=CURRENT_TIMESTAMP""",
                (workspace_id, content)
            )
            conn.commit()

    def get_notes(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE workspace_id = ?", (workspace_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"workspace_id": workspace_id, "content": ""}

    # --- BOOKMARKS METHODS ---
    def add_bookmark(self, workspace_id, bookmark_type, title, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bookmarks (workspace_id, type, title, content) VALUES (?, ?, ?, ?)",
                (workspace_id, bookmark_type, title, content)
            )
            conn.commit()
            return cursor.lastrowid

    def get_bookmarks(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bookmarks WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_bookmark(self, bookmark_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
            conn.commit()

    # --- FLASHCARDS METHODS ---
    def clear_flashcards(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flashcards WHERE workspace_id = ?", (workspace_id,))
            conn.commit()

    def add_flashcards(self, workspace_id, cards):
        # cards is a list of dicts: [{"front": "...", "back": "..."}]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for card in cards:
                cursor.execute(
                    "INSERT INTO flashcards (workspace_id, front, back, is_difficult) VALUES (?, ?, ?, 0)",
                    (workspace_id, card["front"], card["back"])
                )
            conn.commit()

    def get_flashcards(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM flashcards WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            return [dict(row) for row in cursor.fetchall()]

    def update_flashcard_difficulty(self, card_id, is_difficult):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE flashcards SET is_difficult = ? WHERE id = ?",
                (1 if is_difficult else 0, card_id)
            )
            conn.commit()

    def delete_flashcard(self, card_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
            conn.commit()

    # --- PROGRESS METHODS ---
    def log_progress(self, workspace_id, active_seconds=0, increment_session=False):
        date_str = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT active_seconds, sessions_count FROM study_progress WHERE workspace_id = ? AND date = ?",
                (workspace_id, date_str)
            )
            row = cursor.fetchone()
            if row:
                new_sec = row["active_seconds"] + active_seconds
                new_sessions = row["sessions_count"] + (1 if increment_session else 0)
                cursor.execute(
                    "UPDATE study_progress SET active_seconds = ?, sessions_count = ? WHERE workspace_id = ? AND date = ?",
                    (new_sec, new_sessions, workspace_id, date_str)
                )
            else:
                cursor.execute(
                    "INSERT INTO study_progress (workspace_id, date, active_seconds, sessions_count) VALUES (?, ?, ?, ?)",
                    (workspace_id, date_str, active_seconds, 1 if increment_session else 0)
                )
            conn.commit()

    def get_progress(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_progress WHERE workspace_id = ? ORDER BY date ASC", (workspace_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_streak(self, workspace_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT date FROM study_progress WHERE workspace_id = ? ORDER BY date DESC", (workspace_id,))
            rows = cursor.fetchall()
            if not rows:
                return 0
            
            dates = [datetime.strptime(row["date"], "%Y-%m-%d").date() for row in rows]
            
            # Check if active today or yesterday to continue streak
            from datetime import date, timedelta
            today = date.today()
            if dates[0] != today and dates[0] != today - timedelta(days=1):
                return 0
            
            streak = 1
            for i in range(len(dates) - 1):
                if dates[i] - dates[i+1] == timedelta(days=1):
                    streak += 1
                else:
                    break
            return streak
