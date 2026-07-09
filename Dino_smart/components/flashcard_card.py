import streamlit as st
import hashlib

def render_flashcard(front, back):
    # Create a unique key for the card based on the front text
    card_hash = hashlib.md5(front.encode('utf-8')).hexdigest()
    flip_key = f"fc_flipped_{card_hash}"
    
    if flip_key not in st.session_state:
        st.session_state[flip_key] = False
        
    is_flipped = st.session_state[flip_key]
    
    # Beautiful Custom HTML and CSS card design (strictly monochrome)
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
    
    # Render card markup
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
        
    # Beautiful action button for flipping
    btn_label = "Flip to Front" if is_flipped else "Flip to Back"
    if st.button(btn_label, use_container_width=True, key=f"flip_{card_hash}"):
        st.session_state[flip_key] = not is_flipped
        st.rerun()