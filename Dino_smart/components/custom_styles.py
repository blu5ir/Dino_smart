import streamlit as st

def apply_custom_styles():
    # 1. Inject Satoshi & General Sans fonts
    st.markdown('<link href="https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&f[]=general-sans@700,500,400&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    
    # 2. Inject massive CSS overrides to force strict monochrome print design
    st.markdown('''
        <style>
        /* Base page overrides */
        .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
            font-family: 'Satoshi', 'General Sans', sans-serif !important;
        }
        
        /* Noise Texture Overlay */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            opacity: 0.04;
            z-index: 999990;
            pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 250 250' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }
        
        /* Sidebar styling overrides */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 2px solid #000000 !important;
            color: #000000 !important;
            z-index: 100;
        }

        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
            color: #000000 !important;
            font-family: 'General Sans', sans-serif !important;
        }
        [data-testid="stSidebar"] .stButton button {
            border: 2px solid #000000 !important;
            border-radius: 999px !important;
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        
        /* Headers / Texts styling */
        h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #000000 !important;
            font-family: 'Satoshi', sans-serif !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            letter-spacing: -0.02em !important;
            margin-top: 1.5rem !important;
            margin-bottom: 1rem !important;
        }
        
        p, li, label, .stMarkdown p {
            color: #000000 !important;
            font-family: 'Satoshi', sans-serif !important;
            font-weight: 500 !important;
        }
        
        /* Form, Blocks, Containers styling */
        .stForm {
            border: 2px solid #000000 !important;
            border-radius: 8px !important;
            background-color: #ffffff !important;
            padding: 2rem !important;
            box-shadow: 4px 4px 0 #000000 !important;
        }
        
        div[data-testid="stBlock"] {
            border-radius: 0px !important;
        }
        
        /* Metric Card Overrides */
        .metric-card {
            background-color: #ffffff !important;
            border: 2px solid #000000 !important;
            border-radius: 8px !important;
            padding: 20px !important;
            text-align: center !important;
            box-shadow: 4px 4px 0 #000000 !important;
            margin-bottom: 20px !important;
        }
        .metric-label {
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            letter-spacing: 1.5px !important;
            color: #555555 !important;
            text-transform: uppercase !important;
            margin-bottom: 8px !important;
        }
        .metric-val {
            font-family: 'Satoshi', sans-serif !important;
            font-weight: 900 !important;
            font-size: 2.2rem !important;
            color: #000000 !important;
        }
        
        /* Glass Card overrides to make them Brutalist zine-style */
        .glass-card {
            background-color: #ffffff !important;
            border: 2px solid #000000 !important;
            border-radius: 12px !important;
            padding: 25px !important;
            box-shadow: 6px 6px 0 #000000 !important;
            margin-bottom: 20px !important;
            backdrop-filter: none !important;
        }
        
        /* Streamlit Input fields overrides (Notebook style) */
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            border: 2px solid #000000 !important;
            border-radius: 4px !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            font-family: 'Satoshi', sans-serif !important;
            padding: 10px 15px !important;
            box-shadow: 2px 2px 0 #000000 !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #000000 !important;
            box-shadow: 4px 4px 0 #000000 !important;
        }
        
        /* Streamlit Button overrides (Printed style) */
        .stButton button, .stDownloadButton button {
            border: 2px solid #000000 !important;
            border-radius: 999px !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            padding: 10px 30px !important;
            transition: opacity 0.2s ease, transform 0.1s ease !important;
            box-shadow: none !important;
        }
        
        .stButton button:hover, .stDownloadButton button:hover {
            opacity: 0.75 !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #000000 !important;
        }
        
        .stButton button:active, .stDownloadButton button:active {
            transform: scale(0.98) !important;
        }
        
        /* Tabs design system overrides */
        [data-baseweb="tab-list"] {
            border-bottom: 2px solid #000000 !important;
            gap: 15px !important;
            padding-bottom: 5px !important;
            background-color: transparent !important;
        }
        
        [data-baseweb="tab"] {
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: 2px solid transparent !important;
            border-bottom: none !important;
            border-radius: 6px 6px 0 0 !important;
            padding: 10px 20px !important;
            background-color: transparent !important;
            color: #555555 !important;
            transition: all 0.2s ease !important;
        }
        
        [data-baseweb="tab"]:hover {
            color: #000000 !important;
            opacity: 0.8 !important;
        }
        
        [data-baseweb="tab"][aria-selected="true"] {
            background-color: #ffffff !important;
            border-color: #000000 !important;
            color: #000000 !important;
            position: relative;
            z-index: 10;
            margin-bottom: -2px;
        }
        
        /* Table overrides (Notebook lines style) */
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 20px 0 !important;
        }
        
        th {
            font-family: 'General Sans', sans-serif !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            border-bottom: 2px solid #000000 !important;
            padding: 12px 15px !important;
            text-transform: uppercase !important;
            color: #000000 !important;
        }
        
        td {
            border-bottom: 1px dashed rgba(0,0,0,0.2) !important;
            padding: 10px 15px !important;
            color: #222222 !important;
        }
        
        /* Custom progress bar overrides */
        .stProgress > div > div > div > div {
            background-color: #000000 !important;
        }
        
        /* Mascot interactive style */
        .mascot-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999995;
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
            pointer-events: auto;
        }
        
        .dino-svg {
            width: 55px;
            height: 55px;
            fill: none;
            stroke: #000000;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            background-color: #ffffff;
            border: 2px solid #000000;
            border-radius: 50%;
            padding: 6px;
            box-shadow: 3px 3px 0 #000000;
            transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .mascot-container:hover .dino-svg {
            transform: scale(1.1) rotate(5deg);
        }
        
        /* Mascot CSS Blinking Animation */
        @keyframes dino-blink {
            0%, 90%, 100% { opacity: 1; }
            93%, 97% { opacity: 0; }
        }
        @keyframes dino-blink-line {
            0%, 90%, 100% { opacity: 0; }
            93%, 97% { opacity: 1; }
        }
        
        .dino-eye {
            animation: dino-blink 4s infinite;
        }
        .dino-eye-blink {
            animation: dino-blink-line 4s infinite;
            stroke: #000000;
            stroke-width: 2.5;
        }
        
        .mascot-speech-bubble {
            background-color: #ffffff;
            border: 2px solid #000000;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 700;
            max-width: 180px;
            box-shadow: 2px 2px 0 #000000;
            position: relative;
            opacity: 0;
            transform: translateX(10px);
            transition: opacity 0.3s ease, transform 0.3s ease;
            pointer-events: none;
        }
        
        .mascot-container:hover .mascot-speech-bubble {
            opacity: 1;
            transform: translateX(0);
        }
        
        .mascot-speech-bubble::after {
            content: "";
            position: absolute;
            right: -8px;
            top: 50%;
            transform: translateY(-50%) rotate(45deg);
            width: 10px;
            height: 10px;
            background-color: #ffffff;
            border-right: 2px solid #000000;
            border-top: 2px solid #000000;
        }
        
        /* Zine layout utilities */
        .gradient-title {
            background: none !important;
            -webkit-text-fill-color: initial !important;
            color: #000000 !important;
            font-size: 2.5rem !important;
            font-weight: 900 !important;
            border-bottom: 2px solid #000000 !important;
            padding-bottom: 8px !important;
            margin-bottom: 25px !important;
            letter-spacing: -1px !important;
        }
        </style>
        
        <!-- Blinking Mascot HTML element -->
        <div class="mascot-container" id="st-dino-mascot">
            <div class="mascot-speech-bubble">Study with craft. Keep it raw.</div>
            <svg class="dino-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <!-- Mascot body -->
                <path d="M 20 80 Q 20 40 45 40 Q 60 40 65 25 Q 67 20 72 20 Q 78 20 78 28 Q 78 40 70 48 Q 85 52 82 70 Q 80 80 85 80 L 15 80 Z" />
                <path d="M 20 80 Q 5 75 8 60 Q 12 55 18 70" />
                <!-- Eyes: normal & blinking -->
                <circle class="dino-eye" cx="70" cy="30" r="2.5" />
                <line class="dino-eye-blink" x1="67.5" y1="30" x2="72.5" y2="30" style="opacity: 0;" />
                <!-- Mouth smile -->
                <path d="M 68 36 Q 71 39 74 36" />
                <!-- Doodles spikes -->
                <path d="M 40 40 L 43 36 L 46 40 M 30 46 L 33 41 L 36 46 M 22 56 L 24 50 L 27 56" />
            </svg>
        </div>
    ''', unsafe_allow_html=True)