import os

# Define the content for each component file as lists of lines
files_content = {
    "components/custom_styles.py": [
        "import streamlit as st",
        "",
        "def apply_custom_styles():",
        "    st.markdown('''",
        "        <style>",
        "        .gradient-title {",
        "            background: linear-gradient(90deg, #34d399, #38bdf8);",
        "            -webkit-background-clip: text;",
        "            -webkit-text-fill-color: transparent;",
        "            font-weight: bold;",
        "        }",
        "        .metric-card {",
        "            background: rgba(255,255,255,0.05);",
        "            border-radius: 10px;",
        "            padding: 15px;",
        "            text-align: center;",
        "            border: 1px solid rgba(255,255,255,0.1);",
        "        }",
        "        .metric-label {",
        "            font-size: 0.9rem;",
        "            color: #94a3b8;",
        "        }",
        "        .metric-val {",
        "            font-size: 1.8rem;",
        "            font-weight: bold;",
        "            color: #e2e8f0;",
        "        }",
        "        .glass-card {",
        "            background: rgba(255,255,255,0.05);",
        "            border-radius: 12px;",
        "            padding: 20px;",
        "            border: 1px solid rgba(255,255,255,0.1);",
        "            backdrop-filter: blur(10px);",
        "        }",
        "        </style>",
        "    ''', unsafe_allow_html=True)",
    ],

    "components/flashcard_card.py": [
        "import streamlit as st",
        "",
        "def render_flashcard(front, back):",
        "    with st.container(border=True):",
        "        col1, col2 = st.columns(2)",
        "        with col1:",
        "            st.markdown(f'**📖 Front:** {front}')",
        "        with col2:",
        "            st.markdown(f'**📝 Back:** {back}')",
    ],

    "components/mermaid_renderer.py": [
        "import streamlit as st",
        "",
        "def render_mermaid(code):",
        "    st.code(code, language='mermaid')",
        "    st.caption('📊 Mermaid diagram rendered in code block above.')",
    ],
}

# Ensure directories exist
for path in files_content.keys():
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

# Write each file
for filepath, lines in files_content.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')  # trailing newline
    print(f"✅ Fixed {filepath}")

# Ensure providers/llm_factory.py exists
os.makedirs('providers', exist_ok=True)
if not os.path.exists('providers/llm_factory.py'):
    with open('providers/llm_factory.py', 'w', encoding='utf-8') as f:
        f.write('''class LLMFactory:
    @staticmethod
    def get_provider(provider_name=None, api_key=None, model_name=None, base_url=None):
        return None
''')
    print("✅ Created providers/llm_factory.py stub")
else:
    print("ℹ️ providers/llm_factory.py already exists, skipping creation.")

# Also create an empty __init__.py for providers if missing
with open('providers/__init__.py', 'w', encoding='utf-8') as f:
    f.write('# Provider module\n')
print("✅ Created providers/__init__.py")

print("\n🎉 All files have been fixed successfully!")
print("Now run: streamlit run app.py")