import streamlit as st

def render_flashcard(front, back):
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'**📖 Front:** {front}')
        with col2:
            st.markdown(f'**📝 Back:** {back}')
