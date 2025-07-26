import streamlit as st
import openai
import tempfile
import subprocess
import os
import sqlite3
from datetime import datetime
from streamlit.components.v1 import html

# Set API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Page config
st.set_page_config(page_title="Cloud Visio Generator", layout="wide")
st.title("🧠 Prompt to Cloud Architecture Diagram")

# Initialize SQLite DB for storing diagrams
conn = sqlite3.connect("diagrams.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS diagrams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT,
    format TEXT,
    prompt TEXT,
    code TEXT
)
""")
conn.commit()

# User login
username = st.text_input("Enter your username to begin:")
if not username:
    st.stop()

# User input prompt
prompt = st.text_area("Describe your cloud architecture (e.g., Azure AKS + Load Balancer):", height=150)
diagram_format = st.selectbox("Choose Diagram Format", ["Mermaid", "PlantUML", "D2"])

# Function to generate diagram code from OpenAI
@st.cache_data(show_spinner=False)
def generate_diagram(prompt, format):
    if format == "Mermaid":
        format_instruction = "using Mermaid.js syntax in 'graph TD' format."
    elif format == "PlantUML":
        format_instruction = "using PlantUML @startuml...@enduml format."
    else:
        format_instruction = "using D2 language syntax."

    system_prompt = (
        f"You are a cloud architecture assistant. Generate a concise diagram {format_instruction} "
        "Only return the code inside triple backticks."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    content = response['choices'][0]['message']['content']
    if "```" in content:
        return content.split("```")[-2].strip()
    return content.strip()

# Function to save diagram to local file
def save_diagram(content, format):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "mmd" if format == "Mermaid" else ("puml" if format == "PlantUML" else "d2")
    filename = f"diagram_{timestamp}.{ext}"
    with open(filename, "w") as f:
        f.write(content)
    return filename

# Function to export diagram to PNG (for PlantUML/D2 via CLI tools)
def export_to_png(file_path, format):
    png_path = file_path.replace(file_path.split(".")[-1], "png")
    try:
        if format == "PlantUML":
            subprocess.run(["plantuml", "-tpng", file_path], check=True)
        elif format == "D2":
            subprocess.run(["d2", file_path, png_path], check=True)
        return png_path if os.path.exists(png_path) else None
    except Exception as e:
        st.error(f"Export failed: {e}")
        return None

# Function to export to VSDX using draw.io CLI
def export_to_visio(file_path):
    vsdx_path = file_path.replace(file_path.split(".")[-1], "vsdx")
    try:
        subprocess.run([
            "npx", "@hediet/diagram-cli", "render", file_path,
            "--output", vsdx_path
        ], check=True)
        return vsdx_path if os.path.exists(vsdx_path) else None
    except Exception as e:
        st.error(f"VSDX export failed: {e}")
        return None

# Generate diagram on button click
if st.button("Generate Diagram"):
    if not prompt:
        st.warning("Please enter an architecture description.")
    else:
        with st.spinner("Generating diagram using GPT-4..."):
            diagram_code = generate_diagram(prompt, diagram_format)

        st.subheader("🖋️ Diagram Code")
        code_lang = "mermaid" if diagram_format == "Mermaid" else "text"
        st.code(diagram_code, language=code_lang)

        st.subheader("🌍 Live Diagram Preview")
        if diagram_format == "Mermaid":
            st.markdown(f"""
            ```mermaid
            {diagram_code}
            ```
            """, unsafe_allow_html=True)
        else:
            st.info("Live preview only supported for Mermaid. Use download buttons for other formats.")

        # Embed editable canvas (experimental for visual feedback)
        st.subheader("🖼 Interactive Canvas (Experimental)")
        html(f"""
        <iframe src="https://embed.d2lang.com/" width="100%" height="400px" style="border:1px solid #ccc;"></iframe>
        """, height=400)

        # Save diagram source
        saved_file = save_diagram(diagram_code, diagram_format)
        st.download_button(f"Download {diagram_format} Source", diagram_code, file_name=saved_file)

        # Export PNG if PlantUML or D2
        if diagram_format in ["PlantUML", "D2"]:
            png_file = export_to_png(saved_file, diagram_format)
            if png_file:
                with open(png_file, "rb") as f:
                    st.download_button("Download PNG Diagram", f, file_name=png_file, mime="image/png")

        # Export Visio (VSDX) via draw.io CLI
        vsdx_file = export_to_visio(saved_file)
        if vsdx_file:
            with open(vsdx_file, "rb") as f:
                st.download_button("Download Visio (.vsdx) File", f, file_name=vsdx_file, mime="application/vnd.visio")

        # Save to database
        cursor.execute("""
            INSERT INTO diagrams (username, timestamp, format, prompt, code)
            VALUES (?, ?, ?, ?, ?)
        """, (username, datetime.now().isoformat(), diagram_format, prompt, diagram_code))
        conn.commit()

# Diagram Gallery
st.subheader("📁 Your Saved Diagrams")
cursor.execute("SELECT timestamp, format, prompt, code FROM diagrams WHERE username = ? ORDER BY id DESC", (username,))
diagrams = cursor.fetchall()

for t, f, p, c in diagrams:
    with st.expander(f"{t} - {f}"):
        st.markdown(f"**Prompt:** {p}")
        st.code(c, language="mermaid" if f == "Mermaid" else "text")
