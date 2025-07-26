import streamlit as st
import openai

# Set API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Page config
st.set_page_config(page_title="Cloud Visio Generator", layout="wide")
st.title("🧠 Prompt to Cloud Architecture Diagram")

# User input prompt
prompt = st.text_area("Describe your cloud architecture (e.g., Azure AKS + Load Balancer):", height=150)

# Function to generate diagram code from OpenAI
@st.cache_data(show_spinner=False)
def generate_mermaid(prompt):
    system_prompt = (
        "You are a cloud architecture assistant. Generate a concise Mermaid.js diagram "
        "based on the following cloud architecture description. Only return the diagram code "
        "inside triple backticks using 'graph TD' format."
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

# Generate diagram on button click
if st.button("Generate Diagram"):
    if not prompt:
        st.warning("Please enter an architecture description.")
    else:
        with st.spinner("Generating diagram using GPT-4..."):
            mermaid_code = generate_mermaid(prompt)

        st.subheader("🖋️ Diagram Code")
        st.code(mermaid_code, language="mermaid")

        st.subheader("🌍 Live Diagram Preview")
        st.markdown(f"""
        ```mermaid
        {mermaid_code}
        ```
        """, unsafe_allow_html=True)

        # Option to download the diagram code
        st.download_button("Download Mermaid Code", mermaid_code, file_name="diagram.mmd")
