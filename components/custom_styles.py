import streamlit as st

def apply_custom_styles():
    st.markdown('''
        <style>
        .gradient-title {
            background: linear-gradient(90deg, #34d399, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .metric-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .metric-label {
            font-size: 0.9rem;
            color: #94a3b8;
        }
        .metric-val {
            font-size: 1.8rem;
            font-weight: bold;
            color: #e2e8f0;
        }
        .glass-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        </style>
    ''', unsafe_allow_html=True)
