import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
import docx
import time

# Page configuration - Same layout as React
st.set_page_config(
    page_title="Simplify - Private Summary Bot",
    page_icon="🔒",
    layout="wide"
)

# Custom CSS matching React theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #0B3D91;
        text-align: center;
        margin-bottom: 2rem;
    }
    .simplify-red {
        color: #FC3D21;
    }
    .upload-section {
        border: 2px dashed #0B3D91;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stButton button {
        background-color: #0B3D91;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #FC3D21;
        color: white;
    }
    .message-user {
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .message-ai {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #0B3D91;
    }
    .citation-chip {
        background-color: #e8eaf6;
        padding: 8px 12px;
        border-radius: 20px;
        margin: 5px;
        display: inline-block;
        cursor: pointer;
    }
    .welcome-screen {
        text-align: center;
        padding: 40px 20px;
    }
    .quick-suggestions {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 20px;
    }
    .suggestion-chip {
        background-color: white;
        border: 1px solid #0B3D91;
        padding: 12px 20px;
        border-radius: 25px;
        text-align: left;
        cursor: pointer;
    }
    .suggestion-chip:hover {
        background-color: #0B3D91;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state - Same as React state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'input' not in st.session_state:
    st.session_state.input = ''
if 'loading' not in st.session_state:
    st.session_state.loading = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'selected_citation' not in st.session_state:
    st.session_state.selected_citation = None
if 'pdf_url' not in st.session_state:
    st.session_state.pdf_url = None

# Quick suggestions - Same as React
quick_suggestions = [
    "What is the final conclusion of the paper regarding genome DNA methylation?",
    "Which two epigenomic regulators were found to differentially condition the spaceflight response?", 
    "What is suggested to be the principal immune response generated during deep space exposures?",
    "What is the maximum concentration that hydrated magnesium sulfate mineral levels can reach?"
]

# File processing functions
def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading text file: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def process_file(file):
    """Process uploaded file and extract text"""
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.name)
    
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    
    if file.name.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file.name.lower().endswith('.txt'):
        return extract_text_from_txt(file_path)
    elif file.name.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format"

def generate_mock_response(query):
    """Generate mock AI response similar to React version"""
    responses = {
        "default": "I would analyze your documents and provide a comprehensive answer based on the content. This is a demo response showing how the AI would process your query.",
        "summary": "Based on the documents you've uploaded, I would generate a detailed summary highlighting key points, main findings, and important conclusions from the research materials.",
        "specific": f"For your question about '{query}', I would search through the uploaded documents and provide specific citations and evidence from the source materials."
    }
    
    if "summary" in query.lower() or "conclusion" in query.lower():
        return responses["summary"]
    elif any(word in query.lower() for word in ["what", "which", "how", "when"]):
        return responses["specific"]
    else:
        return responses["default"]

# Header - Same as React
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid #e0e0e0;">
    <div style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
        <div style="width: 40px; height: 40px; background: #0B3D91; color: white; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold;">
            S
        </div>
        <div style="font-size: 1.5rem; font-weight: bold; color: #0B3D91;">Simplify</div>
    </div>
    <div>
        <button style="background: none; border: none; font-size: 1.2rem; cursor: pointer;">ℹ️</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Main layout - Same 3-column layout as React
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("### Chat History")
    
    # New Chat button
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.session_state.uploaded_files = []
        st.rerun()
    
    # Chat history list
    st.markdown("---")
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            if st.button(f"💬 {chat.get('title', 'Chat')}", key=chat.get('id'), use_container_width=True):
                st.session_state.messages = chat.get('messages', [])
                st.session_state.current_chat_id = chat.get('id')
    else:
        st.info("No chat history yet")

with col2:
    # Main chat area
    if not st.session_state.messages:
        # Welcome screen - Same as React
        st.markdown('<div class="welcome-screen">', unsafe_allow_html=True)
        st.markdown("""
        <div style="width: 80px; height: 80px; background: #0B3D91; color: white; display: flex; align-items: center; justify-content: center; border-radius: 16px; margin: 0 auto 20px; font-size: 2rem;">
            S
        </div>
        <h2>Simplify</h2>
        <p style="color: #666; margin-bottom: 30px;">
        Advanced AI interface for document research. 
        Access and analyze documents with intelligent citations.
        </p>
        """, unsafe_allow_html=True)
        
        # Quick suggestions
        st.markdown("### Quick Start")
        for suggestion in quick_suggestions:
            if st.button(suggestion, key=f"sugg_{suggestion[:10]}", use_container_width=True):
                st.session_state.input = suggestion
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Display messages
        for message in st.session_state.messages:
            if message["type"] == "user":
                st.markdown(f"""
                <div class="message-user">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <div style="width: 30px; height: 30px; background: #0B3D91; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                            👤
                        </div>
                        <strong>You</strong>
                        <span style="margin-left: auto; color: #666; font-size: 0.8rem;">{message.get('timestamp', '')}</span>
                    </div>
                    <div>{message['text']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-ai">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <div style="width: 30px; height: 30px; background: #FC3D21; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                            S
                        </div>
                        <strong>Simplify AI</strong>
                        <span style="margin-left: auto; color: #666; font-size: 0.8rem;">{message.get('timestamp', '')}</span>
                    </div>
                    <div>{message['text']}</div>
                    
                    {/* Citations - Same as React */}
                    {message.get('citations') and f"""
                    <div style="margin-top: 15px;">
                        <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 10px; color: #666;">
                            <span>📚</span>
                            <strong>Sources</strong>
                        </div>
                        <div>
                            {' '.join([f'<button class="citation-chip" onclick="alert(\'Source {i+1}\')">{cit.get("title", "Source")}</button>' for i, cit in enumerate(message.get("citations", []))])}
                        </div>
                    </div>
                    """ or ''}
                    
                    {/* Message actions - Same as React */}
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button style="background: none; border: 1px solid #0B3D91; padding: 5px 10px; border-radius: 5px; cursor: pointer;">🔊 Read</button>
                        <button style="background: none; border: 1px solid #0B3D91; padding: 5px 10px; border-radius: 5px; cursor: pointer;">📋 Copy</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Loading indicator
    if st.session_state.loading:
        st.markdown("""
        <div class="message-ai">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <div style="width: 30px; height: 30px; background: #FC3D21; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                    S
                </div>
                <strong>Simplify AI</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="loading-dots">
                    <div style="width: 8px; height: 8px; background: #0B3D91; border-radius: 50%; animation: bounce 1.3s linear infinite;"></div>
                    <div style="width: 8px; height: 8px; background: #0B3D91; border-radius: 50%; animation: bounce 1.3s linear infinite 0.15s;"></div>
                    <div style="width: 8px; height: 8px; background: #0B3D91; border-radius: 50%; animation: bounce 1.3s linear infinite 0.3s;"></div>
                </div>
                Searching documents...
            </div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    st.markdown("### Document Upload")
    
    # File upload section - Same as React
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose PDF or TXT files",
        type=['pdf', 'txt', 'docx'],
        accept_multiple_files=True,
        help="Upload documents you want to query against",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} file(s) selected")
        
        for file in uploaded_files:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{file.name}** ({file.size} bytes)")
            with col_b:
                if st.button("Remove", key=f"remove_{file.name}"):
                    pass
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Ingest button
    if st.button("🚀 Ingest Documents", use_container_width=True):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                time.sleep(2)  # Simulate processing
                
                # Process files
                for file in uploaded_files:
                    text = process_file(file)
                    st.session_state.uploaded_files.append({
                        'name': file.name,
                        'text': text[:500] + "..." if len(text) > 500 else text
                    })
                
                st.success("✅ Documents ingested successfully!")
        else:
            st.error("Please upload files first")

# Input area - Same as React (at bottom)
st.markdown("---")
input_col1, input_col2 = st.columns([6, 1])

with input_col1:
    user_input = st.text_input(
        "Ask about your documents...",
        value=st.session_state.input,
        key="user_input",
        placeholder="Type your question here...",
        label_visibility="collapsed"
    )

with input_col2:
    send_button = st.button("↑", use_container_width=True)

if send_button and user_input.strip():
    # Add user message
    user_message = {
        "id": len(st.session_state.messages),
        "type": "user",
        "text": user_input,
        "timestamp": time.strftime("%H:%M")
    }
    st.session_state.messages.append(user_message)
    
    # Set loading state
    st.session_state.loading = True
    st.session_state.input = ""
    st.rerun()
    
    # Simulate AI processing
    time.sleep(1)
    
    # Add AI response
    ai_message = {
        "id": len(st.session_state.messages),
        "type": "ai", 
        "text": generate_mock_response(user_input),
        "timestamp": time.strftime("%H:%M"),
        "citations": [
            {"id": 1, "number": 1, "title": "Research Document", "fileName": "document.pdf", "page": 1},
            {"id": 2, "number": 2, "title": "Source Material", "fileName": "data.txt", "page": 1}
        ] if st.session_state.uploaded_files else []
    }
    st.session_state.messages.append(ai_message)
    
    # Update chat history
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.chat_history.append({
            "id": st.session_state.current_chat_id,
            "title": user_input[:30] + "..." if len(user_input) > 30 else user_input,
            "messages": st.session_state.messages.copy()
        })
    
    st.session_state.loading = False
    st.rerun()

# Disclaimer - Same as React
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 10px;">
    ⚠️ Information is generated by AI and may be inaccurate or contain mistakes.
</div>
""", unsafe_allow_html=True)
