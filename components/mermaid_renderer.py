import streamlit as st

def render_mermaid(code):
    st.code(code, language='mermaid')
    st.caption('📊 Mermaid diagram rendered in code block above.')
