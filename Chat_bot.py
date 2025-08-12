import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
from typing import List, Dict

# --- Environment Setup ---
load_dotenv()

def get_setting(name: str, default_value: str) -> str:
    """Read a setting from env with optional Streamlit secrets override."""
    # Base value from .env / OS env
    setting_value = os.getenv(name, default_value)
    # Optionally override with Streamlit Cloud secrets if present
    try:
        if name in st.secrets:
            setting_value = st.secrets[name]
    except Exception:
        # st.secrets may not be available locally
        pass
    return setting_value

OLLAMA_BASE_URL = get_setting("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = get_setting("DEFAULT_MODEL", "llama3.2:1b")
PAGE_TITLE = get_setting("PAGE_TITLE", "THIS IS YOUR FLASQ AI ASSISTANT")
APP_NAME = get_setting("APP_NAME", "Flasq")

# --- Page Configuration and Styling ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #2c3e50 0%, #000000 100%);
        background-attachment: fixed;
        color: white;
    }
    .user-message, .assistant-message {
        padding: 12px 18px;
        border-radius: 18px;
        margin: 10px 0;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }
    .assistant-message {
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        margin-right: auto;
        border-bottom-left-radius: 5px;
    }
    .logo-text {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 3s ease infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #333 !important;
        border-radius: 25px;
        border: none;
        padding: 12px 20px;
    }
    .stForm button {
        background: #4ecdc4;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        transition: transform 0.2s ease-in-out, background-color 0.2s ease-in-out;
    }
    .stForm button:hover {
        transform: scale(1.1) rotate(15deg);
        background: #3eb5a5;
    }
    .chat-container {
        margin-bottom: 120px;
        padding-bottom: 20px;
    }
    footer {
        visibility: hidden;
    }
    .stDeployButton {
        display: none;
    }
    #MainMenu {
        visibility: hidden;
    }
    header {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "typewriter_shown" not in st.session_state:
    st.session_state.typewriter_shown = False
if "ollama_connected" not in st.session_state:
    st.session_state.ollama_connected = False

# --- Logo and Header ---
st.markdown(f"<div class='logo-text'>🤖 {APP_NAME}</div>", unsafe_allow_html=True)
st.title("💬 Your Personal AI Assistant")

# --- Functions ---

def check_ollama_connection():
    """Check if Ollama is running and available"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            st.session_state.ollama_connected = True
            return True
        else:
            st.session_state.ollama_connected = False
            return False
    except requests.exceptions.RequestException:
        st.session_state.ollama_connected = False
        return False

def get_available_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            return [model['name'] for model in models.get('models', [])]
        return []
    except requests.exceptions.RequestException:
        return []

def typewriter_effect(text: str, speed: float = 0.03):
    """Display typewriter effect for welcome message"""
    if st.session_state.typewriter_shown:
        st.markdown(f"<div style='text-align: center; font-size: 24px; margin: 20px 0;'>{text}</div>", unsafe_allow_html=True)
        return

    container = st.empty()
    displayed_text = ""

    for char in text:
        displayed_text += char
        container.markdown(
            f"<div style='text-align: center; font-size: 24px; margin: 20px 0;'>{displayed_text}<span style='animation: blink 1s infinite;'>▌</span></div>",
            unsafe_allow_html=True
        )
        time.sleep(speed)

    container.markdown(
        f"<div style='text-align: center; font-size: 24px; margin: 20px 0;'>{text}</div>",
        unsafe_allow_html=True
    )
    st.session_state.typewriter_shown = True

def generate_response(user_text: str, model_name: str, system_prompt: str, temperature: float):
    """Generate AI response using Ollama API"""
    if not user_text.strip():
        st.warning("Please enter a message.")
        return
    
    if not st.session_state.ollama_connected:
        st.error("❌ Ollama is not running. Please start Ollama first.")
        return

    try:
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # Show thinking message
        with st.spinner("🤖 Flasq is thinking..."):
            
            # Prepare the conversation context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in st.session_state.messages:
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
            
            # Prepare the request payload
            payload = {
                "model": model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature
                },
                "stream": False
            }
            
            # Make the API call to Ollama
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('message', {}).get('content', 'Sorry, I could not generate a response.')
                
                # Add AI response to session state
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                # Remove the user message since we couldn't process it
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The model might be loading, please try again.")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
    
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to Ollama. Make sure Ollama is running on {OLLAMA_BASE_URL}")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
    
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()

# --- Check Ollama Connection ---
ollama_status = check_ollama_connection()

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Ollama Configuration")
    
    # Show connection status
    if ollama_status:
        st.success("✅ YOU ARE NOW CONNECTED TO AI")
        # Get available models
        available_models = get_available_models()
        if available_models:
            model = st.selectbox(
                "Choose a model",
                available_models,
                index=0 if "llama3.2:1b" not in available_models else available_models.index("llama3.2:1b")
            )
        else:
            st.warning("No models found. Please pull a model first.")
            model = st.text_input("Model name", value=DEFAULT_MODEL)
    else:
        st.error("❌ Ollama is not running")
        st.markdown("Please start Ollama by running:")
        st.code("ollama serve")
        st.markdown("Then pull a model:")
        st.code(f"ollama pull {DEFAULT_MODEL}")
        model = DEFAULT_MODEL

    system_prompt = st.text_area(
        "System Prompt",
        "You are Flasq, a helpful and friendly AI assistant.A proffecional in Coding and programming languages. Respond to the user's questions clearly, concisely, and in a conversational manner.",
        height=150
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    
    st.divider()
    
    if st.button("🔄 Refresh Connection"):
        check_ollama_connection()
        st.rerun()
    
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.typewriter_shown = False
        st.rerun()

# --- Typewriter Welcome Message ---
welcome_text = "Hi there, I'm your professional AI assistant powered by Ollama! How can I help you today?"
if not st.session_state.messages:  # Only show welcome on first load
    typewriter_effect(welcome_text)

# --- Main Chat UI and Logic ---
st.markdown("---")

# Display chat messages
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f"<div class='user-message'><strong>You:</strong><br>{msg['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='assistant-message'><strong>🤖 Flasq:</strong><br>{msg['content']}</div>",
            unsafe_allow_html=True
        )

# --- Input Section ---
st.markdown("<div style='margin-bottom: 100px;'></div>", unsafe_allow_html=True)

# Create input form at the bottom
with st.container():
    st.markdown("""
    <style>
    .element-container:has(> .stForm) {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.2);
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        with col1:
            user_input = st.text_input(
                "💬 Type your message here...",
                placeholder="Ask me anything...",
                label_visibility="collapsed",
                key="user_input",
                disabled=not ollama_status
            )
        with col2:
            submit_button = st.form_submit_button("✈️", disabled=not ollama_status)

        if submit_button and user_input and ollama_status:
            generate_response(user_input, model, system_prompt, temperature)
            st.rerun()

# Show setup instructions if Ollama is not running
if not ollama_status:
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    To use this chatbot, you need to have Ollama running and accessible at the base URL configured in your environment (currently `{OLLAMA_BASE_URL}`):
    
    1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai) to download
    2. **Start Ollama**: Run `ollama serve` in your terminal or server
    3. **Pull a model**: Run `ollama pull {DEFAULT_MODEL}`
    4. **Refresh this page** and start chatting!
    """)
    