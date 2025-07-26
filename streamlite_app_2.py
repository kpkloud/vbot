import streamlit as st
import openai
import tempfile
import subprocess
import os
from datetime import datetime

# Set API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Page config
st.set_page_config(page_title="Cloud Visio Generator", layout="wide")
st.title("🧠 Prompt to Cloud Architecture Diagram")

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

        # Save diagram source
        saved_file = save_diagram(diagram_code, diagram_format)
        st.download_button(f"Download {diagram_format} Source", diagram_code, file_name=saved_file)

        # Export PNG if PlantUML or D2
        if diagram_format in ["PlantUML", "D2"]:
            png_file = export_to_png(saved_file, diagram_format)
            if png_file:
                with open(png_file, "rb") as f:
                    st.download_button("Download PNG Diagram", f, file_name=png_file, mime="image/png")
