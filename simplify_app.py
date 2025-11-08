import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
import docx
import time

# Page configuration
st.set_page_config(
    page_title="Simplify - Smart Document Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with white theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    .feature-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin: 10px 0;
    }
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        background: #f8f9ff;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    .upload-zone:hover {
        border-color: #764ba2;
        background: #f0f2ff;
    }
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .chat-message {
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    .user-message {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
    }
    .ai-message {
        background: white;
        border-left: 4px solid #764ba2;
    }
    .suggestion-chip {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 10px 20px;
        border-radius: 25px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .suggestion-chip:hover {
        border-color: #667eea;
        background: #f8f9ff;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'current_summary' not in st.session_state:
    st.session_state.current_summary = None

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
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Save file
    file_path = os.path.join("uploads", file.name)
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    
    # Extract text based on file type
    if file.name.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file.name.lower().endswith('.txt'):
        return extract_text_from_txt(file_path)
    elif file.name.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format"

def generate_mock_summary(text, length="medium"):
    """Generate a mock summary for demo purposes"""
    words = text.split()[:100]  # Take first 100 words
    preview = " ".join(words)
    
    summary_templates = {
        "short": f"This document discusses: {preview}... [Short summary would be generated here]",
        "medium": f"""Key Points:
        
• The document covers important topics related to the content
• Main themes include analysis and insights from the provided text
• Key findings suggest meaningful conclusions

Summary: {preview}... [AI would generate a comprehensive summary here]""",
        "detailed": f"""Detailed Analysis:

Document Overview:
This appears to be a document containing valuable information that would be processed by AI to generate insights.

Main Sections:
1. Introduction and context
2. Key data points and analysis
3. Conclusions and recommendations

Key Insights:
- The content suggests important information worth summarizing
- Multiple perspectives could be extracted
- Actionable insights would be highlighted

Full AI Summary: {preview}... [Detailed AI analysis would appear here]"""
    }
    
    return summary_templates.get(length, summary_templates["medium"])

# Header Section
st.markdown('<h1 class="main-header">✨ Simplify</h1>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <p style="font-size: 1.2rem; color: #666; font-weight: 500;">
        Smart Document Summarization • Privacy Focused • Instant Results
    </p>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["📄 Summarize", "💬 Chat", "⚙️ About"])

with tab1:
    st.header("📄 Document Summarization")
    
    # File upload section
    st.markdown("### 1. Upload Documents")
    st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drag & drop files or click to browse",
        type=['pdf', 'txt', 'docx'],
        accept_multiple_files=True,
        help="Supported formats: PDF, TXT, DOCX"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")
        # Show file list
        for file in uploaded_files:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{file.name}** ({file.size:,} bytes)")
            with col2:
                if st.button("Remove", key=f"remove_{file.name}"):
                    pass
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing options
    col1, col2 = st.columns(2)
    
    with col1:
        summary_length = st.selectbox(
            "Summary Length",
            ["Short", "Medium", "Detailed"],
            index=1
        )
    
    with col2:
        output_format = st.selectbox(
            "Output Style",
            ["Bullet Points", "Paragraph", "Structured"],
            index=0
        )
    
    # Process button
    if st.button("🚀 Generate Summary", use_container_width=True):
        if not uploaded_files:
            st.error("Please upload at least one document")
        else:
            with st.spinner("🔄 Processing your documents..."):
                # Simulate processing time
                time.sleep(2)
                
                # Process files
                all_text = ""
                for file in uploaded_files:
                    text = process_file(file)
                    all_text += f"\n\n--- {file.name} ---\n{text}"
                
                # Generate mock summary
                summary = generate_mock_summary(all_text, summary_length.lower())
                st.session_state.current_summary = summary
                st.session_state.uploaded_files = uploaded_files
                
                st.success("✅ Documents processed successfully!")
    
    # Display summary
    if st.session_state.current_summary:
        st.markdown("### 📊 Your Summary")
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.current_summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Copy Summary", use_container_width=True):
                st.success("Summary copied to clipboard!")
        with col2:
            if st.button("📥 Download", use_container_width=True):
                st.info("Download feature would be implemented")
        with col3:
            if st.button("🔄 New Summary", use_container_width=True):
                st.session_state.current_summary = None
                st.rerun()

with tab2:
    st.header("💬 Chat with Documents")
    
    if not st.session_state.uploaded_files:
        st.info("💡 Upload documents in the Summarize tab to enable chat")
    else:
        # Quick questions
        st.markdown("### Quick Questions")
        quick_questions = [
            "What are the main points?",
            "Summarize the key findings",
            "What methodology was used?",
            "List the important data",
            "What are the conclusions?"
        ]
        
        cols = st.columns(3)
        for i, question in enumerate(quick_questions):
            with cols[i % 3]:
                if st.button(question, use_container_width=True):
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user",
                        "content": question,
                        "time": time.strftime("%H:%M")
                    })
                    # Simulate AI response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"I would analyze your documents and provide insights about: {question}",
                        "time": time.strftime("%H:%M")
                    })
        
        # Chat interface
        st.markdown("### Conversation")
        
        # Display messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div style="font-weight: 600; color: #667eea;">You</div>
                    <div>{message['content']}</div>
                    <div style="font-size: 0.8rem; color: #888; text-align: right;">{message['time']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <div style="font-weight: 600; color: #764ba2;">Simplify AI</div>
                    <div>{message['content']}</div>
                    <div style="font-size: 0.8rem; color: #888; text-align: right;">{message['time']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_area(
            "Your question:",
            placeholder="Ask anything about your documents...",
            key="chat_input",
            height=100
        )
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button("Send Message", use_container_width=True):
                if user_input.strip():
                    # Add user message
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_input,
                        "time": time.strftime("%H:%M")
                    })
                    # Add AI response
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"Based on your documents, I would provide a detailed answer about: {user_input}",
                        "time": time.strftime("%H:%M")
                    })
                    st.rerun()
        
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

with tab3:
    st.header("⚙️ About Simplify")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🔒 Privacy First")
        st.markdown("""
        - Your data never leaves your device
        - No external servers
        - Complete data ownership
        - Secure local processing
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Instant Results")
        st.markdown("""
        - Quick document processing
        - Real-time summarization
        - Fast chat responses
        - Efficient AI analysis
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Smart Features")
        st.markdown("""
        - Multi-format support
        - Intelligent summaries
        - Document Q&A
        - Context-aware responses
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Technology info
    st.markdown("### 🛠️ How It Works")
    st.markdown("""
    Simplify processes your documents locally using advanced AI techniques:
    
    1. **Upload** - Drag and drop your documents
    2. **Process** - AI analyzes content locally
    3. **Summarize** - Get instant key insights
    4. **Chat** - Ask questions about your documents
    
    *Note: This demo shows the interface. Full AI integration would require additional setup.*
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 20px;'>"
    "✨ Simplify - Making Document Understanding Simple & Secure"
    "</div>",
    unsafe_allow_html=True
)
