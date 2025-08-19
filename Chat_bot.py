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
PAGE_TITLE = get_setting("PAGE_TITLE", "Flasq AI Assistant")
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
        padding: 15px 20px;
        border-radius: 20px;
        margin: 15px 0;
        max-width: 75%;
        word-wrap: break-word;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        line-height: 1.5;
    }
    .user-message {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 8px;
    }
    .assistant-message {
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        margin-right: auto;
        border-bottom-left-radius: 8px;
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
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333 !important;
        border-radius: 25px;
        border: 2px solid #4ecdc4;
        padding: 12px 20px;
        font-size: 16px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #45b7d1 !important;
        box-shadow: 0 0 10px rgba(69, 183, 209, 0.3) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #4ecdc4 0%, #45b7d1 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .chat-container {
        margin-bottom: 120px;
        padding: 20px 0;
    }
    .input-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 -5px 25px rgba(0,0,0,0.3);
        z-index: 1000;
        backdrop-filter: blur(10px);
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-connected {
        background-color: #4CAF50;
        animation: pulse 2s infinite;
    }
    .status-disconnected {
        background-color: #f44336;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
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
if "available_models" not in st.session_state:
    st.session_state.available_models = []

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
            model_list = [model['name'] for model in models.get('models', [])]
            st.session_state.available_models = model_list
            return model_list
        return []
    except requests.exceptions.RequestException:
        st.session_state.available_models = []
        return []

def typewriter_effect(text: str, speed: float = 0.02):
    """Display typewriter effect for welcome message"""
    if st.session_state.typewriter_shown:
        st.markdown(f"<div style='text-align: center; font-size: 20px; margin: 30px 0; color: #4ecdc4;'>{text}</div>", unsafe_allow_html=True)
        return

    container = st.empty()
    displayed_text = ""

    for char in text:
        displayed_text += char
        container.markdown(
            f"<div style='text-align: center; font-size: 20px; margin: 30px 0; color: #4ecdc4;'>{displayed_text}<span style='animation: blink 1s infinite;'>▌</span></div>",
            unsafe_allow_html=True
        )
        time.sleep(speed)

    container.markdown(
        f"<div style='text-align: center; font-size: 20px; margin: 30px 0; color: #4ecdc4;'>{text}</div>",
        unsafe_allow_html=True
    )
    st.session_state.typewriter_shown = True

def generate_response(user_text: str, model_name: str, system_prompt: str, temperature: float):
    """Generate AI response using Ollama API"""
    if not user_text.strip():
        st.warning("⚠️ Please enter a message.")
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
            
            # Add conversation history (limit to last 10 exchanges to prevent token overflow)
            recent_messages = st.session_state.messages[-20:] if len(st.session_state.messages) > 20 else st.session_state.messages
            for msg in recent_messages:
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
            
            # Prepare the request payload
            payload = {
                "model": model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": 2048,
                    "top_k": 40,
                    "top_p": 0.9
                },
                "stream": False
            }
            
            # Make the API call to Ollama
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('message', {}).get('content', 'Sorry, I could not generate a response.')
                
                # Add AI response to session state
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # Success feedback
                st.success("✅ Response generated successfully!")
                time.sleep(1)
                
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                # Remove the user message since we couldn't process it
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The model might be loading, please try again in a moment.")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
    
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Could not connect to Ollama at {OLLAMA_BASE_URL}. Please ensure Ollama is running.")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
    
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()

# --- Logo and Header ---
st.markdown(f"<div class='logo-text'>🤖 {APP_NAME}</div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #4ecdc4; margin-bottom: 30px;'>💬 Your Professional AI Assistant</h2>", unsafe_allow_html=True)

# --- Check Ollama Connection ---
ollama_status = check_ollama_connection()

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Show connection status with indicator
    if ollama_status:
        st.markdown("<span class='status-indicator status-connected'></span>**Connected to Ollama**", unsafe_allow_html=True)
        st.success("✅ Ready to chat!")
        
        # Get available models
        available_models = get_available_models()
        if available_models:
            # Try to find the default model, otherwise use the first available
            default_index = 0
            if DEFAULT_MODEL in available_models:
                default_index = available_models.index(DEFAULT_MODEL)
            
            model = st.selectbox(
                "🤖 Choose AI Model",
                available_models,
                index=default_index,
                help="Select the AI model for conversation"
            )
        else:
            st.warning("⚠️ No models found. Please pull a model first.")
            model = st.text_input("Model name", value=DEFAULT_MODEL, help="Enter model name manually")
    else:
        st.markdown("<span class='status-indicator status-disconnected'></span>**Disconnected**", unsafe_allow_html=True)
        st.error("❌ Ollama not accessible")
        model = DEFAULT_MODEL

    st.divider()
    
    # System prompt configuration
    system_prompt = st.text_area(
        "🎯 System Prompt",
        "You are Flasq, a helpful and professional AI assistant specialized in coding and programming languages. Provide clear, concise, and accurate responses. When helping with code, include explanations and best practices.",
        height=120,
        help="Define the AI's personality and expertise"
    )
    
    # Temperature slider
    temperature = st.slider(
        "🌡️ Creativity Level", 
        0.0, 1.0, 0.7, 0.05,
        help="Lower values = more focused, Higher values = more creative"
    )
    
    st.divider()
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", help="Check Ollama connection"):
            check_ollama_connection()
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            st.session_state.messages = []
            st.session_state.typewriter_shown = False
            st.success("Chat cleared!")
            time.sleep(1)
            st.rerun()

    # Show model info if connected
    if ollama_status and available_models:
        st.divider()
        st.markdown("### 📊 Available Models")
        for i, model_name in enumerate(available_models[:5]):  # Show first 5 models
            st.markdown(f"• {model_name}")
        if len(available_models) > 5:
            st.markdown(f"... and {len(available_models) - 5} more")

# --- Main Content Area ---
# Typewriter Welcome Message
welcome_text = f"Hello! I'm {APP_NAME}, your professional AI assistant powered by Ollama. I'm here to help with coding, programming, and any questions you have!"

if not st.session_state.messages:  # Only show welcome on first load
    typewriter_effect(welcome_text)

st.markdown("---")

# Display chat messages in a container
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(
                f"<div class='user-message'><strong>👤 You:</strong><br>{msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='assistant-message'><strong>🤖 {APP_NAME}:</strong><br>{msg['content']}</div>",
                unsafe_allow_html=True
            )

# Add spacing for fixed input
st.markdown("<div style='margin-bottom: 120px;'></div>", unsafe_allow_html=True)

# --- Fixed Input Section ---
input_container = st.container()
with input_container:
    st.markdown("""
    <style>
    .element-container:has(> .stForm) {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        background: rgba(255, 255, 255, 0.98);
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 -5px 25px rgba(0,0,0,0.3);
        z-index: 1000;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(78, 205, 196, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([9, 1])
        
        with col1:
            user_input = st.text_input(
                "💬 Message",
                placeholder="Ask me anything about coding, programming, or any topic...",
                label_visibility="collapsed",
                key="user_input",
                disabled=not ollama_status
            )
        
        with col2:
            submit_button = st.form_submit_button(
                "🚀", 
                disabled=not ollama_status,
                help="Send message" if ollama_status else "Connect to Ollama first"
            )

        # Handle form submission
        if submit_button and user_input and ollama_status:
            generate_response(user_input, model, system_prompt, temperature)
            st.rerun()

# --- Setup Instructions (shown when Ollama is not running) ---
if not ollama_status:
    st.markdown("---")
    st.markdown("### 🚀 Getting Started with Ollama")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Step 1: Install Ollama**
        - Visit [ollama.ai](https://ollama.ai) to download
        - Follow installation instructions for your OS
        
        **Step 2: Start Ollama**
        ```bash
        ollama serve
        ```
        """)
    
    with col2:
        st.markdown(f"""
        **Step 3: Pull a Model**
        ```bash
        ollama pull {DEFAULT_MODEL}
        ```
        
        **Step 4: Refresh Connection**
        - Click the "🔄 Refresh" button in the sidebar
        - Start chatting once connected!
        """)
    
    st.info(f"💡 **Current Configuration:** Trying to connect to `{OLLAMA_BASE_URL}`")

# --- Footer Information ---
if ollama_status:
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666; font-size: 14px; margin-top: 20px;'>"
        f"Connected to Ollama at {OLLAMA_BASE_URL} | Model: {model if 'model' in locals() else DEFAULT_MODEL}"
        f"</div>", 
        unsafe_allow_html=True
    )