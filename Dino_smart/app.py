import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st

# Fix: Proper bootstrap detection
if not hasattr(st, 'runtime') or not st.runtime.exists():
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", sys.argv[0]] + sys.argv[1:]
    sys.exit(stcli.main())

import os
import json
import re
import time
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import traceback



try:
    from database.db_manager import DatabaseManager
except ImportError as e:
    st.error(f"Database module error: {e}")
    st.stop()

try:
    from providers.llm_factory import LLMFactory
except ImportError:
    class LLMFactory:
        @staticmethod
        def get_provider(**kwargs):
            return None

try:
    from services.doc_processor import DocumentProcessor
except ImportError:
    class DocumentProcessor:
        @staticmethod
        def process_document(**kwargs):
            st.warning("Document processor not available")

try:
    from services.guide_generator import GuideGenerator
except ImportError:
    class GuideGenerator:
        @staticmethod
        def generate_full_guide(**kwargs):
            return None
        @staticmethod
        def regenerate_topic(**kwargs):
            return None
        @staticmethod
        def get_workspace_context(**kwargs):
            return ""

try:
    from services.quiz_service import QuizService
except ImportError:
    class QuizService:
        @staticmethod
        def generate_quiz(**kwargs):
            return []
        @staticmethod
        def evaluate_quiz(**kwargs):
            return {"score": 0, "total": 0, "accuracy": 0, "topic_analysis": {}, "details": {}}

try:
    from services.flashcard_service import FlashcardService
except ImportError:
    class FlashcardService:
        @staticmethod
        def generate_flashcards(**kwargs):
            return []

try:
    from services.chat_service import ChatService
except ImportError:
    class ChatService:
        @staticmethod
        def get_grounded_response(**kwargs):
            return "Chat service not available"

try:
    from services.revision_service import RevisionService
except ImportError:
    class RevisionService:
        @staticmethod
        def generate_revision_material(**kwargs):
            return "Revision service not available"

try:
    from components.custom_styles import apply_custom_styles
except ImportError:
    def apply_custom_styles():
        st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        .gradient-title { color: #000000 !important; font-size: 2.5rem !important; font-weight: 900 !important; border-bottom: 2px solid #000000 !important; padding-bottom: 8px !important; }
        .metric-card { background-color: #ffffff !important; border: 2px solid #000000 !important; border-radius: 8px !important; padding: 20px !important; box-shadow: 4px 4px 0 #000000 !important; }
        .metric-label { font-size: 0.9rem !important; font-weight: 700 !important; color: #555555 !important; }
        .metric-val { font-size: 2.2rem !important; font-weight: 900 !important; color: #000000 !important; }
        .glass-card { background-color: #ffffff !important; border: 2px solid #000000 !important; border-radius: 12px !important; padding: 25px !important; box-shadow: 6px 6px 0 #000000 !important; }
        </style>
        """, unsafe_allow_html=True)

try:
    from components.flashcard_card import render_flashcard
except ImportError:
    import hashlib
    def render_flashcard(front, back):
        card_hash = hashlib.md5(front.encode('utf-8')).hexdigest()
        flip_key = f"fc_flipped_{card_hash}"
        if flip_key not in st.session_state:
            st.session_state[flip_key] = False
        is_flipped = st.session_state[flip_key]
        card_style = """
        <style>
        .flashcard-wrapper {
            margin: 20px 0;
            display: flex;
            justify-content: center;
            width: 100%;
        }
        .fc-card {
            background-color: #ffffff;
            border: 2px solid #000000;
            border-radius: 16px;
            padding: 40px 30px;
            min-height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            width: 100%;
            box-shadow: 4px 4px 0 #000000;
            transition: all 0.3s ease;
        }
        .fc-card.flipped {
            border-color: #000000;
            background-color: #ffffff;
            box-shadow: 6px 6px 0 #000000;
        }
        .fc-header {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #555555;
            margin-bottom: 20px;
            font-weight: 700;
        }
        .fc-card.flipped .fc-header {
            color: #000000;
        }
        .fc-content {
            font-size: 1.4rem;
            font-weight: 500;
            color: #000000;
            line-height: 1.5;
        }
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        if is_flipped:
            st.markdown(f"""
            <div class="flashcard-wrapper">
                <div class="fc-card flipped">
                    <div class="fc-header">Back (Answer)</div>
                    <div class="fc-content">{back}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="flashcard-wrapper">
                <div class="fc-card">
                    <div class="fc-header">Front (Question)</div>
                    <div class="fc-content">{front}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        btn_label = "Flip to Front" if is_flipped else "Flip to Back"
        if st.button(btn_label, use_container_width=True, key=f"flip_{card_hash}"):
            st.session_state[flip_key] = not is_flipped
            st.rerun()

try:
    from components.mermaid_renderer import render_mermaid
except ImportError:
    def render_mermaid(code):
        st.code(code, language='mermaid')

try:
    from utils.exporters import StudyBuddyExporter
except ImportError:
    class StudyBuddyExporter:
        @staticmethod
        def export_to_markdown(title, content):
            return f"# {title}\n\n{content}"
        @staticmethod
        def export_to_docx(title, content):
            return b""
        @staticmethod
        def export_to_pdf(title, content):
            return b""

try:
    from utils.search_helper import SearchHelper
except ImportError:
    class SearchHelper:
        pass

# Page configuration
st.set_page_config(
    page_title="Dino_Smart",
    page_icon="🦕",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except:
        pass

local_config = load_config()

# Initialize database
try:
    db = DatabaseManager()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# Session state initialization
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

if "active_ws_id" not in st.session_state:
    st.session_state.active_ws_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get workspaces
try:
    workspaces = db.get_workspaces()
except Exception as e:
    workspaces = []
    st.warning(f"Could not load workspaces: {e}")

if workspaces and st.session_state.active_ws_id is None:
    st.session_state.active_ws_id = workspaces[0]["id"]

if st.session_state.active_ws_id:
    elapsed = time.time() - st.session_state.session_start_time
    if elapsed > 5:
        try:
            db.log_progress(st.session_state.active_ws_id, active_seconds=int(elapsed))
        except:
            pass
    st.session_state.session_start_time = time.time()

logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
if os.path.exists(logo_path):
    st.logo(logo_path, size="large")

with st.sidebar:
    if not os.path.exists(logo_path):
        st.markdown('<div class="gradient-title" style="font-size: 1.8rem; text-align: center;">Dino Smart</div>', unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    
    st.subheader("Workspace Settings")
    
    ws_names = [w["name"] for w in workspaces]
    
    col_ws_sel, col_ws_add = st.columns([4, 1])
    with col_ws_sel:
        active_ws_idx = 0
        if st.session_state.active_ws_id:
            for idx, w in enumerate(workspaces):
                if w["id"] == st.session_state.active_ws_id:
                    active_ws_idx = idx
                    break
        
        ws_select = st.selectbox(
            "Select Workspace",
            options=ws_names,
            index=active_ws_idx if ws_names else 0,
            key="ws_select_box"
        )
        
        if workspaces and ws_select:
            for w in workspaces:
                if w["name"] == ws_select:
                    if st.session_state.active_ws_id != w["id"]:
                        st.session_state.active_ws_id = w["id"]
                        st.session_state.chat_history = []
                        st.session_state.card_index = 0
                        st.rerun()
                    break

    with col_ws_add:
        if st.button("➕", help="Create new workspace"):
            st.session_state.show_ws_creator = True
            
    if st.session_state.get("show_ws_creator", False):
        with st.form("new_workspace_form"):
            st.markdown("##### Create Workspace")
            new_ws_name = st.text_input("Name (e.g. Finals Prep)")
            new_ws_subject = st.text_input("Subject (e.g. Biology)")
            col_form_a, col_form_b = st.columns(2)
            with col_form_a:
                submitted = st.form_submit_button("Create")
            with col_form_b:
                cancelled = st.form_submit_button("Cancel")
                
            if submitted and new_ws_name and new_ws_subject:
                ws_id = db.create_workspace(new_ws_name, new_ws_subject)
                if ws_id:
                    st.session_state.active_ws_id = ws_id
                    st.session_state.show_ws_creator = False
                    st.session_state.chat_history = []
                    st.success("Workspace created!")
                    st.rerun()
                else:
                    st.error("Workspace name already exists.")
            if cancelled:
                st.session_state.show_ws_creator = False
                st.rerun()

    current_ws = None
    if st.session_state.active_ws_id:
        for w in workspaces:
            if w["id"] == st.session_state.active_ws_id:
                current_ws = w
                break

    if current_ws is None and workspaces:
        st.session_state.active_ws_id = workspaces[0]["id"]
        current_ws = workspaces[0]

    if current_ws:
        st.caption(f"Subject: **{current_ws['subject']}**")
    
    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    
    st.subheader(" AI Settings")
    
    providers_list = ["Smart Router", "Gemini", "Groq", "OpenRouter"]
    
    saved_prov = local_config.get("provider_name", "Smart Router")
    prov_idx = providers_list.index(saved_prov) if saved_prov in providers_list else 0
    
    provider_sel = st.selectbox(
        "Provider",
        options=providers_list,
        index=prov_idx,
        key="ai_provider_selection"
    )
    
    if provider_sel == "Smart Router":
        st.info(
            "🧠 **Smart Router Mode**\n\n"
            "Cascades calls dynamically for maximum uptime and cost efficiency:\n"
            "- ⚡ **Groq** $\\rightarrow$ 🌐 **OpenRouter** $\\rightarrow$ 🧠 **Gemini** (for short chat queries).\n"
            "- 🧠 **Gemini** $\\rightarrow$ 🌐 **OpenRouter** $\\rightarrow$ ⚡ **Groq** (for large context study materials, guides, and OCR).\n"
            "- 🔄 **Automatic Cascade**: If one provider is slow, offline, rate-limited, or lacks credentials, the router instantly cascades to the next.\n\n"
            "👉 *Be sure to save API keys in the individual 'Gemini', 'Groq', and 'OpenRouter' sections first.*"
        )
    
    default_urls = {
        "Groq": "https://api.groq.com/openai/v1",
        "OpenRouter": "https://openrouter.ai/api/v1"
    }
    
    base_url_input = ""
    if provider_sel in ["Groq", "OpenRouter"]:
        base_url_input = st.text_input(
            "Base URL",
            value=local_config.get(f"{provider_sel}_base_url", default_urls.get(provider_sel, ""))
        )
        
    api_key_input = ""
    if provider_sel not in ["Smart Router"]:
        default_key = local_config.get(f"{provider_sel}_api_key", "")
        if not default_key:
            if provider_sel == "Gemini":
                default_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
            elif provider_sel == "Groq":
                default_key = os.environ.get("GROQ_API_KEY", "")
            elif provider_sel == "OpenRouter":
                default_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=default_key
        )

    model_sel = ""
    if provider_sel != "Smart Router":
        model_sel = st.text_input(
            "Model Name",
            value=local_config.get(f"{provider_sel}_model_name", 
                                   "gemini-3.5-flash" if provider_sel == "Gemini" 
                                   else "llama-3.1-8b-instant" if provider_sel == "Groq"
                                   else "meta-llama/llama-3.1-8b-instruct:free" if provider_sel == "OpenRouter"
                                   else "")
        )
    
    temp_sel = st.slider("Temperature", 0.0, 1.0, value=local_config.get("temperature", 0.7), step=0.1)
    max_tokens_sel = st.slider("Max Tokens", 256, 4096, value=local_config.get("max_tokens", 2048), step=128)
    
    if st.button("Save Settings", width="stretch"):
        local_config["provider_name"] = provider_sel
        local_config["temperature"] = temp_sel
        local_config["max_tokens"] = max_tokens_sel
        if api_key_input:
            local_config[f"{provider_sel}_api_key"] = api_key_input
        if base_url_input:
            local_config[f"{provider_sel}_base_url"] = base_url_input
        if model_sel:
            local_config[f"{provider_sel}_model_name"] = model_sel
        save_config(local_config)
        st.success("AI Configuration saved!")
        time.sleep(0.5)
        st.rerun()

    # Render version information at the bottom of the sidebar
    st.markdown("<hr style='margin: 20px 0 10px 0; opacity: 0.15;'>", unsafe_allow_html=True)
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
    vdata = {"version": "1.0.0", "build": "001", "timestamp": "09 Jul 2026 11:42 PM"}
    try:
        if os.path.exists(version_file):
            with open(version_file, "r") as vf:
                vdata = json.load(vf)
    except Exception:
        pass
    
    st.markdown(
        f"""
        <div style="font-family: monospace; font-size: 0.75rem; color: #64748b; line-height: 1.3;">
            <div>📦 <b>Version</b>: {vdata.get('version', '1.0.0')}</div>
            <div>🛠️ <b>Build</b>: {vdata.get('build', '001')}</div>
            <div>🕒 <b>Deployed</b>: {vdata.get('timestamp', '09 Jul 2026 11:42 PM')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    ai_provider = None
    try:
        active_api_key = local_config.get(f"{provider_sel}_api_key", "")
        if not active_api_key and provider_sel != "Smart Router":
            if provider_sel == "Gemini":
                active_api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
            elif provider_sel == "Groq":
                active_api_key = os.environ.get("GROQ_API_KEY", "")
            elif provider_sel == "OpenRouter":
                active_api_key = os.environ.get("OPENROUTER_API_KEY", "")

        active_base_url = local_config.get(f"{provider_sel}_base_url", default_urls.get(provider_sel, ""))
        active_model = local_config.get(f"{provider_sel}_model_name", "")
        
        has_smart_router_keys = False
        if provider_sel == "Smart Router":
            has_smart_router_keys = bool(
                local_config.get("Gemini_api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            ) or bool(
                local_config.get("Groq_api_key") or os.environ.get("GROQ_API_KEY")
            ) or bool(
                local_config.get("OpenRouter_api_key") or os.environ.get("OPENROUTER_API_KEY")
            )
        
        if provider_sel in ["Smart Router"] or active_api_key or has_smart_router_keys:
            ai_provider = LLMFactory.get_provider(
                provider_name=provider_sel,
                api_key=active_api_key,
                model_name=active_model,
                base_url=active_base_url
            )
    except Exception as e:
        st.sidebar.error(f"Failed to load AI adapter: {str(e)}")

    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    
    st.subheader("Quick Actions")
    if st.session_state.active_ws_id:
        guide_data = db.get_study_guide(st.session_state.active_ws_id)
        if guide_data and current_ws:
            export_md = StudyBuddyExporter.export_to_markdown(f"Study Guide: {current_ws['name']}", guide_data["content"])
            st.download_button(
                "Export Guide (Markdown)",
                data=export_md,
                file_name=f"{current_ws['name']}_study_guide.md",
                mime="text/markdown",
                width="stretch"
            )
            
        if st.button("Clear Workspace Content", width="stretch"):
            db.delete_workspace(st.session_state.active_ws_id)
            st.session_state.active_ws_id = None
            st.success("Workspace cleared and removed.")
            time.sleep(0.5)
            st.rerun()

if not workspaces:
    st.markdown("<div style='text-align: center; margin-top: 100px;'>", unsafe_allow_html=True)
    st.markdown('<div class="gradient-title" style="font-size: 3rem;">Welcome to Dino_Smart</div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2rem; color:#555555;'>Your ultimate offline-first personalized study assistant.</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### Let's create your first workspace to begin!")
        with st.form("first_workspace"):
            name = st.text_input("Workspace Name", placeholder="e.g., Computer Science 101, History Final")
            subject = st.text_input("Subject", placeholder="e.g., Programming, European History")
            submit = st.form_submit_button("Create Workspace", width="stretch")
            if submit and name and subject:
                ws_id = db.create_workspace(name, subject)
                if ws_id:
                    st.session_state.active_ws_id = ws_id
                    st.success("Workspace created successfully!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Name already exists. Use a unique name.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

workspace_id = st.session_state.active_ws_id
if workspace_id is None:
    st.error("Please select or create a workspace to continue.")
    st.stop()

current_ws = None
if st.session_state.active_ws_id:
    for w in workspaces:
        if w["id"] == st.session_state.active_ws_id:
            current_ws = w
            break

# ============================================
# TABS - 9 tabs total (0 to 8)
# ============================================
tab_names = [
    "00. Dashboard", 
    "01. Study Material", 
    "02. Study Guide", 
    "03. Quiz Arena", 
    "04. Adaptive Learning", 
    "05. Flashcards", 
    "06. My Notes", 
    "07. AI Tutor", 
    "08. Revision Hub"
]

tabs = st.tabs(tab_names)

# Tab 0: Dashboard
with tabs[0]:
    if current_ws:
        st.markdown(f'<div class="gradient-title" style="font-size: 2rem;">Dashboard: {current_ws["name"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="gradient-title" style="font-size: 2rem;">Dashboard</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    guide_data = db.get_study_guide(workspace_id)
    quizzes = db.get_quizzes(workspace_id)
    quiz_history = db.get_quiz_history(workspace_id)
    cards = db.get_flashcards(workspace_id)
    
    col_str, col_doc, col_gui, col_q = st.columns(4)
    with col_str:
        streak = db.get_streak(workspace_id)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Study Streak</div>
            <div class="metric-val">{streak} Days</div>
        </div>
        """, unsafe_allow_html=True)
    with col_doc:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Files Ingested</div>
            <div class="metric-val">{len(docs)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_gui:
        guide_status = "Available" if guide_data else "Not Generated"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Study Guide</div>
            <div class="metric-val">{guide_status}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_q:
        avg_score = int(sum([qh["accuracy"] for qh in quiz_history])/len(quiz_history)) if quiz_history else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Accuracy</div>
            <div class="metric-val">{avg_score}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Active Study Sessions")
        progress = db.get_progress(workspace_id)
        if progress:
            df = pd.DataFrame(progress)
            df["minutes"] = df["active_seconds"] / 60
            fig = px.line(df, x="date", y="minutes", labels={"minutes": "Study Time (Min)", "date": "Date"},
                          title="Study Minutes Over Time", line_shape="linear", markers=True)
            fig.update_traces(line=dict(color="#000000", width=2.5), marker=dict(color="#000000", size=7))
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title_font=dict(color="#000000", family="Satoshi"),
                font=dict(color="#000000", family="Satoshi")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Study more to display progress graphs!")
            
    with col_right:
        st.subheader("Quiz History Trends")
        if quiz_history:
            df_q = pd.DataFrame(quiz_history)
            df_q["date"] = df_q["date_taken"].apply(lambda x: x.split(" ")[0])
            fig_q = px.bar(df_q, x="date", y="accuracy", color="difficulty", labels={"accuracy": "Accuracy (%)"},
                           title="Quiz Scores History", barmode="group",
                           color_discrete_map={"Easy": "#e2e8f0", "Medium": "#94a3b8", "Hard": "#000000", "Mixed": "#475569"})
            fig_q.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title_font=dict(color="#000000", family="Satoshi"),
                font=dict(color="#000000", family="Satoshi")
            )
            st.plotly_chart(fig_q, use_container_width=True)
        else:
            st.info("Take quizzes to see accuracy records.")
            
    col_act, col_weak = st.columns(2)
    with col_act:
        st.subheader("Recent Ingested Materials")
        if docs:
            for d in docs[:4]:
                st.markdown(f"**{d['name']}** ({d['file_type'].upper()}) — *Ingested {d['created_at'].split(' ')[0]}*")
        else:
            st.info("No documents uploaded yet.")
            
    with col_weak:
        st.subheader("Weak Focus Areas")
        weak_topics = []
        topic_scores = {}
        for qh in quiz_history:
            t_analysis = qh.get("topic_analysis", {})
            for topic, score_data in t_analysis.items():
                if topic not in topic_scores:
                    topic_scores[topic] = {"correct": 0, "total": 0}
                topic_scores[topic]["correct"] += score_data.get("correct", 0)
                topic_scores[topic]["total"] += score_data.get("total", 0)
                
        for t, scores in topic_scores.items():
            acc = (scores["correct"]/scores["total"])*100 if scores["total"] > 0 else 100
            if acc < 65:
                weak_topics.append((t, int(acc)))
                
        if weak_topics:
            for t, acc in weak_topics:
                st.markdown(f"[!] **{t}** — Accuracy: `{acc}%` *(Needs review)*")
        else:
            st.success("Looking strong! No weak areas detected yet.")

# Tab 1: Study Material
with tabs[1]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Ingest Study Materials</div>', unsafe_allow_html=True)
    
    col_upload, col_paste = st.columns(2)
    with col_upload:
        st.subheader("Upload Files")
        uploaded_files = st.file_uploader(
            "Upload course docs (PDF, DOCX, PPTX, TXT, MD, Images)",
            type=["pdf", "docx", "pptx", "txt", "md", "png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if not ai_provider:
                st.warning("No active AI Provider configured. Image OCR and automatic summaries will fall back to local parsing only.")
                
            if st.button("Process & Ingest Files", width="stretch"):
                with st.spinner("Processing uploads..."):
                    for file in uploaded_files:
                        bytes_data = file.read()
                        ext = os.path.splitext(file.name)[1].lower().replace(".", "")
                        DocumentProcessor.process_document(
                            file_bytes=bytes_data,
                            file_name=file.name,
                            file_type=ext,
                            provider=ai_provider,
                            db_manager=db,
                            workspace_id=workspace_id
                        )
                st.success("All files ingested successfully!")
                time.sleep(0.5)
                st.rerun()
                
    with col_paste:
        st.subheader("Copy-Paste Notes")
        note_title = st.text_input("Note Title", placeholder="e.g. Lecture 1 Notes")
        note_content = st.text_area("Note Text Content", height=200, placeholder="Paste study text here...")
        if st.button("Save Text Material", width="stretch") and note_title and note_content:
            with st.spinner("Processing note..."):
                DocumentProcessor.process_document(
                    file_bytes=note_content.encode("utf-8"),
                    file_name=note_title + ".txt",
                    file_type="txt",
                    provider=ai_provider,
                    db_manager=db,
                    workspace_id=workspace_id
                )
            st.success("Note saved successfully!")
            time.sleep(0.5)
            st.rerun()
            
    st.markdown("<hr style='opacity: 0.1;'>", unsafe_allow_html=True)
    st.subheader("Managed Materials in Workspace")
    
    docs = db.get_documents(workspace_id)
    if docs:
        for d in docs:
            c1, c2, c3 = st.columns([6, 3, 1])
            with c1:
                st.markdown(f"**{d['name']}** ({d['file_type'].upper()}) — *{len(d['content'])} chars*")
                if d["summary"]:
                    st.caption(f"Summary: {d['summary']}")
            with c2:
                topics_str = ", ".join(json.loads(d["topics_json"]))
                st.caption(f"Topics: {topics_str}")
            with c3:
                if st.button("Delete", key=f"del_doc_{d['id']}"):
                    db.delete_document(d["id"])
                    st.success("Document deleted!")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("No materials ingested. Upload items above to start.")

# Tab 2: Study Guide
with tabs[2]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">AI Study Guide</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    if not docs:
        st.info("Please upload study materials to generate study guides.")
    else:
        guide_data = db.get_study_guide(workspace_id)
        
        col_ctrls_1, col_ctrls_2 = st.columns([2, 5])
        with col_ctrls_1:
            guide_mode = st.radio("Guide Mode", ["Deep Dive (6 topics)", "Cram Mode (8 topics)"])
            
            gen_label = "Regenerate Study Guide" if guide_data else "Generate Study Guide"
            if not ai_provider:
                st.error("Please configure your AI Provider and API key in the sidebar.")
            elif st.button(gen_label, width="stretch"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def guide_progress_cb(pct, status):
                    progress_bar.progress(pct / 100)
                    status_text.markdown(f"⚡ *{status}*")
                    
                mode_key = "deep_dive" if "Deep" in guide_mode else "cram"
                
                try:
                    guide_data = GuideGenerator.generate_full_guide(
                        provider=ai_provider,
                        db_manager=db,
                        workspace_id=workspace_id,
                        mode=mode_key,
                        progress_bar_callback=guide_progress_cb
                    )
                    st.success("Guide generated successfully!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Study Guide Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                
        with col_ctrls_2:
            if guide_data:
                st.subheader("📚 Generated Topics")
                st.markdown(f"Mode: **{guide_data['mode'].replace('_', ' ').upper()}**")
                
                exp_all = st.button("Expand All")
                
                for topic in guide_data["topics"]:
                    content = guide_data["content"].get(topic, "Generating...")
                    
                    with st.expander(topic, expanded=exp_all):
                        st.markdown(content, unsafe_allow_html=True)
                        
                        mermaid_blocks = re.findall(r'```mermaid(.*?)```', content, re.DOTALL)
                        for block in mermaid_blocks:
                            st.caption("🖼️ Visual Model")
                            render_mermaid(block)
                            
                        col_topic_btn1, col_topic_btn2 = st.columns(2)
                        with col_topic_btn1:
                            if st.button("🔄 Regenerate Topic", key=f"regen_{topic}"):
                                with st.spinner(f"Regenerating {topic}..."):
                                    GuideGenerator.regenerate_topic(ai_provider, db, workspace_id, topic)
                                st.success(f"{topic} updated!")
                                time.sleep(0.5)
                                st.rerun()
                        with col_topic_btn2:
                            if st.button("📌 Bookmark Topic", key=f"bookmark_{topic}"):
                                db.add_bookmark(workspace_id, "guide", topic, content)
                                st.success("Bookmarked!")
            else:
                st.info("Study guide not generated yet. Select settings and click Generate.")

# Tab 3: Quiz Arena
with tabs[3]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Quiz Arena</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    if not docs:
        st.info("Please upload study materials to generate quizzes.")
    else:
        if "active_quiz_questions" not in st.session_state:
            st.session_state.active_quiz_questions = None
            st.session_state.quiz_start_time = None
            st.session_state.quiz_difficulty = None
            st.session_state.quiz_id = None
            
        if not st.session_state.active_quiz_questions:
            st.subheader("✏️ Configure Your Quiz")
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                q_diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Mixed"])
                q_count = st.selectbox("Number of Questions", [5, 10, 20, 50])
            with col_q2:
                st.markdown("<br>", unsafe_allow_html=True)
                if not ai_provider:
                    st.error("Please configure your AI Provider.")
                elif st.button("Generate and Start Quiz", width="stretch"):
                    with st.spinner("Generating quiz questions based on materials..."):
                        try:
                            if "quiz_results" in st.session_state:
                                del st.session_state.quiz_results
                            questions = QuizService.generate_quiz(
                                provider=ai_provider,
                                db_manager=db,
                                workspace_id=workspace_id,
                                difficulty=q_diff,
                                count=q_count,
                                temperature=local_config.get("temperature", 0.7)
                            )
                            if questions:
                                st.session_state.active_quiz_questions = questions
                                st.session_state.quiz_start_time = time.time()
                                st.session_state.quiz_difficulty = q_diff
                                st.session_state.quiz_run_token = str(int(time.time()))
                                quizzes = db.get_quizzes(workspace_id)
                                st.session_state.quiz_id = quizzes[0]["id"] if quizzes else 1
                                st.rerun()
                            else:
                                st.error("No questions generated. Please verify your study materials are uploaded and contain readable text.")
                        except Exception as e:
                            st.error(f"❌ Quiz Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
        else:
            st.subheader(f"Quiz Mode: **{st.session_state.quiz_difficulty}**")
            
            responses = {}
            with st.form("active_quiz_form"):
                for idx, q in enumerate(st.session_state.active_quiz_questions):
                    q_id = q["id"]
                    st.markdown(f"**Q{idx+1}: {q['question']}** *({q['type'].upper()} - {q.get('topic', 'General')})*")
                    
                    if q["type"] == "mcq":
                        responses[q_id] = st.radio(f"Select answer for Q{idx+1}", options=q["options"], index=None, key=f"q_radio_{st.session_state.get('quiz_run_token', 'default')}_{q_id}")
                    elif q["type"] == "tf":
                        responses[q_id] = st.radio(f"Select true/false for Q{idx+1}", options=["True", "False"], index=None, key=f"q_radio_{st.session_state.get('quiz_run_token', 'default')}_{q_id}")
                    elif q["type"] == "matching":
                        st.caption("Pair the items on the left to the options in the selection below:")
                        user_match = {}
                        left_items = list(q["answer"].keys()) if isinstance(q["answer"], dict) else ["Item A", "Item B"]
                        right_options = q["options"]
                        for item in left_items:
                            user_match[item] = st.selectbox(f"Match: {item}", options=["None"] + right_options, key=f"q_match_{st.session_state.get('quiz_run_token', 'default')}_{q_id}_{item}")
                        responses[q_id] = user_match
                    elif q["type"] in ["fill", "short"]:
                        responses[q_id] = st.text_input(f"Your answer for Q{idx+1}", key=f"q_text_{st.session_state.get('quiz_run_token', 'default')}_{q_id}")
                    elif q["type"] == "numerical":
                        responses[q_id] = st.text_input(f"Numeric response for Q{idx+1}", key=f"q_num_{st.session_state.get('quiz_run_token', 'default')}_{q_id}")
                    
                    st.markdown("<hr style='opacity: 0.05;'>", unsafe_allow_html=True)
                    
                submitted = st.form_submit_button("Submit Quiz Responses")
                if submitted:
                    duration = int(time.time() - st.session_state.quiz_start_time)
                    
                    results = QuizService.evaluate_quiz(st.session_state.active_quiz_questions, responses)
                    
                    db.add_quiz_history(
                        workspace_id=workspace_id,
                        quiz_id=st.session_state.quiz_id,
                        score=results["score"],
                        total_questions=results["total"],
                        time_spent=duration,
                        accuracy=results["accuracy"],
                        topic_analysis=results["topic_analysis"]
                    )
                    
                    st.session_state.quiz_results = results
                    st.session_state.active_quiz_questions = None
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌ Cancel and Reset Quiz", key="reset_active_quiz", use_container_width=True):
                st.session_state.active_quiz_questions = None
                if "quiz_results" in st.session_state:
                    del st.session_state.quiz_results
                st.rerun()
                    
    if "quiz_results" in st.session_state:
        res = st.session_state.quiz_results
        
        # Removed st.balloons() to keep design calm and clean
        st.markdown(f"""
        <div class="glass-card">
            <h3>Quiz Submitted</h3>
            <h4>Score: <strong>{res['score']} / {res['total']}</strong> | Accuracy: <strong>{int(res['accuracy'])}%</strong></h4>
        </div>
        """, unsafe_allow_html=True)
        
        for q_id, q_det in res["details"].items():
            st.markdown(f"**Question Details:**")
            status_text = "[✓] CORRECT" if q_det["correct"] else "[✗] INCORRECT"
            st.markdown(f"Status: **{status_text}**")
            st.markdown(f"Your Answer: `{q_det['user_answer']}`")
            st.markdown(f"Correct Answer: `{q_det['correct_answer']}`")
            st.markdown(f"Explanation: *{q_det['explanation']}*")
            st.markdown("<hr style='opacity: 0.1;'>", unsafe_allow_html=True)
            
        if st.button("Close Results Panel"):
            del st.session_state.quiz_results
            st.rerun()

# Tab 4: Adaptive Learning
with tabs[4]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Adaptive Learning Hub</div>', unsafe_allow_html=True)
    
    quiz_history = db.get_quiz_history(workspace_id)
    topic_scores = {}
    for qh in quiz_history:
        t_analysis = qh.get("topic_analysis", {})
        for topic, score_data in t_analysis.items():
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["correct"] += score_data.get("correct", 0)
            topic_scores[topic]["total"] += score_data.get("total", 0)
            
    weak_topics = []
    for t, scores in topic_scores.items():
        acc = (scores["correct"]/scores["total"])*100 if scores["total"] > 0 else 100
        if acc < 65:
            weak_topics.append(t)
            
    if not weak_topics:
        st.success("No weak areas detected yet! Keep testing yourself in the Quiz Arena.")
    else:
        st.markdown("### Identified Weak Topics")
        selected_weak = st.selectbox("Select topic to reinforce:", weak_topics)
        
        col_adapt1, col_adapt2 = st.columns(2)
        with col_adapt1:
            st.markdown(f"Topic: **{selected_weak}**")
            
            if st.button("Explain Concept Simply (ELI10)", width="stretch"):
                if ai_provider:
                    with st.spinner("Generating easier explanation..."):
                        try:
                            docs_text = GuideGenerator.get_workspace_context(db, workspace_id)
                            prompt = f"Explain the topic '{selected_weak}' using very simple analogies and stories so a 10 year old can easily understand. Ground it in: {docs_text[:10000]}"
                            exp = ai_provider.generate_text(prompt, system_instruction="Simplify concepts.")
                            st.session_state.adaptive_explain = exp
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                else:
                    st.error("AI Provider not configured.")
                    
            if st.button("Generate Hard practice questions", width="stretch"):
                if ai_provider:
                    with st.spinner("Generating challenge questions..."):
                        try:
                            docs_text = GuideGenerator.get_workspace_context(db, workspace_id)
                            prompt = f"Generate 3 highly challenging practice questions with answers about '{selected_weak}' to test deep comprehension. Ground in: {docs_text[:10000]}"
                            qs = ai_provider.generate_text(prompt, system_instruction="Generate hard questions.")
                            st.session_state.adaptive_explain = qs
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                else:
                    st.error("AI Provider not configured.")
                    
            if st.button("Generate Topic Flashcards", width="stretch"):
                if ai_provider:
                    with st.spinner("Generating flashcards..."):
                        try:
                            docs_text = GuideGenerator.get_workspace_context(db, workspace_id)
                            prompt = f"Generate 5 targeted flashcard question/answers for the topic '{selected_weak}'. Output JSON list: [{{'front': '...', 'back': '...'}}]. Ground in: {docs_text[:10000]}"
                            raw_cards = ai_provider.generate_text(prompt, system_instruction="Output JSON list.")
                            try:
                                cleaned = raw_cards.strip()
                                if cleaned.startswith("```"):
                                    cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
                                    cleaned = re.sub(r'\n```$', '', cleaned)
                                cards_list = json.loads(cleaned)
                                db.add_flashcards(workspace_id, cards_list)
                                st.success("Added new cards to Flashcard pile!")
                            except:
                                st.error("Failed to parse cards JSON. Try again.")
                        except Exception as e:
                            st.error(f"❌ Flashcards Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                else:
                    st.error("AI Provider not configured.")
                    
        with col_adapt2:
            if "adaptive_explain" in st.session_state:
                st.subheader("💡 Focus Explanation")
                st.markdown(st.session_state.adaptive_explain)
                if st.button("Clear Panel"):
                    del st.session_state.adaptive_explain
                    st.rerun()

# Tab 5: Flashcards
with tabs[5]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Flashcards Arena</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    if not docs:
        st.info("Please upload study materials to generate flashcards.")
    else:
        cards = db.get_flashcards(workspace_id)
        
        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            if st.button("Generate Flashcard Pile", width="stretch"):
                if ai_provider:
                    with st.spinner("Creating flashcards..."):
                        try:
                            db.clear_flashcards(workspace_id)
                            FlashcardService.generate_flashcards(ai_provider, db, workspace_id)
                            st.session_state.card_index = 0
                            st.success("Cards generated!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Flashcard Pile Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                else:
                    st.error("AI Provider not configured.")
            
            review_mode = st.toggle("Difficult-only Review Mode")
            
        with col_c2:
            if cards:
                active_deck = [c for c in cards if c["is_difficult"] == 1] if review_mode else cards
                
                if not active_deck:
                    st.info("No cards in this deck selection.")
                else:
                    if "card_index" not in st.session_state:
                        st.session_state.card_index = 0
                        
                    st.session_state.card_index = min(max(0, st.session_state.card_index), len(active_deck)-1)
                    current_card = active_deck[st.session_state.card_index]
                    
                    st.markdown(f"Card **{st.session_state.card_index + 1} of {len(active_deck)}**")
                    
                    render_flashcard(current_card["front"], current_card["back"])
                    
                    cc1, cc2, cc3, cc4 = st.columns(4)
                    with cc1:
                        if st.button("< Previous", width="stretch"):
                            if st.session_state.card_index > 0:
                                st.session_state.card_index -= 1
                                st.rerun()
                    with cc2:
                        if st.button("Next >", width="stretch"):
                            if st.session_state.card_index < len(active_deck) - 1:
                                st.session_state.card_index += 1
                                st.rerun()
                    with cc3:
                        is_diff = current_card["is_difficult"] == 1
                        lbl = "Remove Difficult Flag" if is_diff else "Mark as Difficult"
                        if st.button(lbl, width="stretch"):
                            db.update_flashcard_difficulty(current_card["id"], not is_diff)
                            st.success("Updated card difficulty flag!")
                            time.sleep(0.3)
                            st.rerun()
                    with cc4:
                        if st.button("Delete Card", width="stretch"):
                            db.delete_flashcard(current_card["id"])
                            st.success("Card deleted.")
                            time.sleep(0.3)
                            st.rerun()
            else:
                st.info("No flashcards available. Click 'Generate Flashcard Pile' on the left to start.")

# Tab 6: Notes Editor
with tabs[6]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Interactive Notes</div>', unsafe_allow_html=True)
    
    notes_record = db.get_notes(workspace_id)
    notes_content = notes_record["content"] if notes_record else ""
    notes_content = st.text_area("Write/Highlight formulas, facts, and notes:", notes_content, height=400)
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if st.button("Save Notes", width="stretch"):
            db.save_notes(workspace_id, notes_content)
            st.success("Notes saved successfully!")
    with col_n2:
        st.download_button(
            "Export Notes (Markdown)",
            data=notes_content,
            file_name=f"{current_ws['name'] if current_ws else 'notes'}_notes.md",
            mime="text/markdown",
            width="stretch"
        )
        
    st.markdown("<hr style='opacity: 0.1;'>", unsafe_allow_html=True)
    st.subheader("Bookmarked Concepts")
    bookmarks = db.get_bookmarks(workspace_id)
    if bookmarks:
        for b in bookmarks:
            with st.expander(f"{b['type'].upper()}: {b['title']}"):
                st.markdown(b["content"])
                if st.button("Delete Bookmark", key=f"del_bm_{b['id']}"):
                    db.delete_bookmark(b["id"])
                    st.success("Bookmark removed!")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("No bookmarks saved yet. You can bookmark sections of your Study Guide.")

# Tab 7: AI Tutor
with tabs[7]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">AI Tutor Chat</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    if not docs:
        st.info("Please upload study materials to start learning with the AI Tutor.")
    else:
        col_tc1, col_tc2 = st.columns([1, 4])
        with col_tc1:
            tutor_mode = st.selectbox(
                "Tutor Strategy",
                ["Ask Anything", "Explain like I'm 10 (ELI10)", "Explain like a professor", "Give hints only", "Solve step-by-step", "Generate examples", "Simplify difficult concepts"]
            )
            
            mode_mapping = {
                "Ask Anything": "regular",
                "Explain like I'm 10 (ELI10)": "eli10",
                "Explain like a professor": "professor",
                "Give hints only": "hints",
                "Solve step-by-step": "step_by_step",
                "Generate examples": "examples",
                "Simplify difficult concepts": "simplify"
            }
            
            if st.button("Clear Chat Log", width="stretch"):
                st.session_state.chat_history = []
                st.rerun()
                
        with col_tc2:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            query = st.chat_input("Ask about your course materials:")
            if query:
                st.session_state.chat_history.append({"role": "user", "content": query})
                with st.chat_message("user"):
                    st.markdown(query)
                    
                if ai_provider:
                    with st.spinner("Tutor is thinking..."):
                        try:
                            resp = ChatService.get_grounded_response(
                                provider=ai_provider,
                                db_manager=db,
                                workspace_id=workspace_id,
                                question=query,
                                mode=mode_mapping.get(tutor_mode, "regular"),
                                chat_history=st.session_state.chat_history[:-1]
                            )
                            st.session_state.chat_history.append({"role": "assistant", "content": resp})
                            with st.chat_message("assistant"):
                                st.markdown(resp)
                        except Exception as e:
                            st.error(f"❌ AI Tutor Chat Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                else:
                    st.error("AI Provider not configured. Set provider details in the sidebar first.")

# Tab 8: Revision Hub
with tabs[8]:
    st.markdown('<div class="gradient-title" style="font-size: 2rem;">Revision Hub</div>', unsafe_allow_html=True)
    
    docs = db.get_documents(workspace_id)
    if not docs:
        st.info("Please upload study materials to generate revision sheets.")
    else:
        col_rev1, col_rev2 = st.columns([1, 3])
        with col_rev1:
            st.subheader("Quick Guides")
            rev_type = st.radio(
                "Select Revision Type",
                [
                    "Cheat Sheet", 
                    "Formula Sheet", 
                    "Last Minute Notes", 
                    "5-Minute Revision", 
                    "Important Definitions", 
                    "Exam Checklist"
                ]
            )
            
            rev_mapping = {
                "Cheat Sheet": "cheat_sheet",
                "Formula Sheet": "formula_sheet",
                "Last Minute Notes": "last_minute",
                "5-Minute Revision": "five_min",
                "Important Definitions": "definitions",
                "Exam Checklist": "checklist"
            }
            
            if not ai_provider:
                st.error("Please configure AI provider.")
            elif st.button("Generate Sheet", width="stretch"):
                with st.spinner(f"Compiling {rev_type}..."):
                    try:
                        res = RevisionService.generate_revision_material(
                            provider=ai_provider,
                            db_manager=db,
                            workspace_id=workspace_id,
                            material_type=rev_mapping[rev_type]
                        )
                        st.session_state.generated_revision = res
                        st.session_state.generated_revision_title = rev_type
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Revision Sheet Generation Failed: {str(e)}. If using the Gemini free tier, you may have exceeded your daily quota. You can switch to another AI Provider (e.g. Groq) or update your API key in the AI Settings sidebar.")
                    
        with col_rev2:
            if "generated_revision" in st.session_state:
                st.subheader(st.session_state.generated_revision_title)
                st.markdown(st.session_state.generated_revision)
                
                st.markdown("<br>", unsafe_allow_html=True)
                title = f"{st.session_state.generated_revision_title} - {current_ws['name'] if current_ws else 'workspace'}"
                
                exp_col1, exp_col2, exp_col3 = st.columns(3)
                with exp_col1:
                    md_bytes = st.session_state.generated_revision.encode("utf-8")
                    st.download_button(
                        "Export Markdown",
                        data=md_bytes,
                        file_name=f"{title.replace(' ', '_')}.md",
                        mime="text/markdown",
                        width="stretch"
                    )
                with exp_col2:
                    content_dict = {st.session_state.generated_revision_title: st.session_state.generated_revision}
                    docx_bytes = StudyBuddyExporter.export_to_docx(title, content_dict)
                    st.download_button(
                        "Export Word (DOCX)",
                        data=docx_bytes,
                        file_name=f"{title.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        width="stretch"
                    )
                with exp_col3:
                    pdf_bytes = StudyBuddyExporter.export_to_pdf(title, content_dict)
                    st.download_button(
                        "Export PDF Document",
                        data=pdf_bytes,
                        file_name=f"{title.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
            else:
                st.info("Select a revision type on the left and click 'Generate Sheet'.")

