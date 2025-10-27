import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_mic_recorder import speech_to_text

# --- 1. CONFIGURATION AND CLIENT SETUP ---

@st.cache_resource
def get_gemini_client():
    """Initializes the Gemini client only once."""
    try:
        return genai.Client()
    except Exception as e:
        st.error(f"Error initializing the Gemini Client. Check if GEMINI_API_KEY is set correctly.")
        st.stop()

client = get_gemini_client()
st.title("🤖 Multimodal Gemini Chatbot (Voice & Vision)")

# Initialize chat session and message history
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
    st.session_state.messages = []


# --- 2. MULTIMODAL INPUTS (MOVED TO SIDEBAR) ---

uploaded_image = None

# Everything inside this 'with' block will appear in the sidebar
with st.sidebar:
    st.header("Upload/Capture Image 🖼️")
    
    # Use tabs for a cleaner layout within the sidebar
    tab1, tab2 = st.tabs(["File Upload", "Camera"])

    with tab1:
        # A. File Upload Input
        file_buffer = st.file_uploader("Upload an image (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if file_buffer:
            uploaded_image = Image.open(file_buffer)
            st.image(uploaded_image, caption='Image uploaded', use_column_width=True)
            
    with tab2:
        # B. Camera Input
        camera_buffer = st.camera_input("Take a picture for analysis")
        if camera_buffer:
            uploaded_image = Image.open(camera_buffer)
            st.image(uploaded_image, caption='Image captured', use_column_width=True)

    st.header("Voice Input 🎤")
    # C. Voice Input
    recorded_text = speech_to_text(
        language='en',
        start_prompt="Click to Start Recording",
        stop_prompt="Click to Stop Recording",
        just_once=True,
        use_container_width=True,
        key='voice_recorder'
    )
    if recorded_text:
        st.session_state['voice_input'] = recorded_text
        st.info(f"🎤 Transcribed: {recorded_text}")
    


# --- 3. DISPLAY CHAT HISTORY ---

# The display code remains in the main area of the screen
for role, content in st.session_state.messages:
    with st.chat_message(role):
        for part in content:
            if isinstance(part, str):
                st.markdown(part)
            elif isinstance(part, Image.Image):
                st.image(part, width=200)

# --- 4. HANDLE NEW INPUT AND GENERATE RESPONSE ---

# Get user input from either the chat box OR the voice recorder
user_text_input = st.chat_input("Ask me a question about the image or just chat...")

# --- Determine the FINAL input that will trigger the model ---
final_user_input = None
if user_text_input:
    final_user_input = user_text_input
elif 'voice_input' in st.session_state and st.session_state['voice_input']:
    final_user_input = st.session_state['voice_input']
    st.session_state['voice_input'] = None 

# If we have any input (text or voice), proceed to send to Gemini
if final_user_input:
    
    # 1. Construct the prompt (text and optional image)
    prompt_parts = []
    
    if uploaded_image is not None:
        prompt_parts.append(uploaded_image)
        file_buffer = None
        camera_buffer = None
        
    prompt_parts.append(final_user_input)

    # 2. Display the user's message
    with st.chat_message("user"):
        st.markdown(final_user_input)
        if uploaded_image is not None:
            st.image(uploaded_image, caption='Input image.', width=200)
    
    # 3. Add user message to history
    st.session_state.messages.append(("user", prompt_parts)) 
    
    # 4. Get the AI's response
    with st.chat_message("assistant"):
        with st.spinner("Genie is thinking..."):
            response = st.session_state.chat_session.send_message(prompt_parts)
        
        # 5. Show and save the AI's response
        st.markdown(response.text)
        st.session_state.messages.append(("assistant", [response.text]))


    st.rerun()

