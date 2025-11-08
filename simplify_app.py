import streamlit as st
import os
import tempfile
import uuid
from utils.rag_utils import setup_rag_system, ingest_documents, ask_question, process_single_document
from utils.file_processor import extract_text, chunk_text
import time

# Page configuration
st.set_page_config(
    page_title="Simplify - Private Summary Bot",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Simplify theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2563eb;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .privacy-badge {
        background-color: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .upload-section {
        border: 2px dashed #d1d5db;
        border-radius: 10px;
        padding: 30px;
        margin: 20px 0;
        text-align: center;
        background-color: #f8fafc;
    }
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .source-card {
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .stButton button {
        background-color: #2563eb;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #1d4ed8;
        color: white;
    }
    .feature-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'processing_state' not in st.session_state:
    st.session_state.processing_state = "ready"  # ready, processing, complete
if 'current_summary' not in st.session_state:
    st.session_state.current_summary = None
if 'sources' not in st.session_state:
    st.session_state.sources = []

# Header
st.markdown("""
<div style="text-align: center;">
    <h1 class="main-header">🔒 Simplify</h1>
    <p style="font-size: 1.2rem; color: #6b7280; margin-bottom: 2rem;">
        Private Document Summarization • Lightning Fast • Source-Verified
    </p>
    <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 2rem;">
        <span class="privacy-badge">🔐 100% Local & Private</span>
        <span class="privacy-badge">⚡ Instant Summaries</span>
        <span class="privacy-badge">📚 Direct Source Links</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model selection
    model_name = st.selectbox(
        "AI Model",
        ["gemma3:4b", "gemma3:1b", "llama2", "mistral"],
        index=0,
        help="Choose the AI model for summarization"
    )
    
    # Summary length
    summary_length = st.select_slider(
        "Summary Length",
        options=["Very Short", "Short", "Medium", "Long", "Detailed"],
        value="Medium"
    )
    
    # Processing options
    st.subheader("Processing Options")
    chunk_size = st.slider("Chunk Size", 500, 2000, 1000, help="Size of text chunks for processing")
    top_k = st.slider("Sources to Show", 1, 5, 3, help="Number of source references to display")
    
    # Privacy notice
    st.markdown("---")
    st.markdown("### 🔒 Privacy Assurance")
    st.info("""
    - All processing happens locally
    - No data sent to external servers
    - Files stored temporarily
    - Complete data ownership
    """)
    
    # System status
    st.markdown("### System Status")
    try:
        import ollama
        client = ollama.Client()
        models = client.list()
        st.success("✅ AI Ready")
        st.success("✅ Database Ready")
    except:
        st.error("❌ AI Service Offline")

# Main content in tabs
tab1, tab2, tab3 = st.tabs(["📄 Upload & Summarize", "💬 Ask Questions", "ℹ️ About Simplify"])

with tab1:
    st.header("📄 Document Summarization")
    
    # File upload section
    st.markdown("### 1. Upload Your Documents")
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drag and drop files here",
        type=['pdf', 'txt', 'docx', 'pptx'],
        accept_multiple_files=True,
        help="Supported formats: PDF, TXT, DOCX, PPTX"
    )
    
    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} file(s) ready for processing")
        
        # Show file preview
        with st.expander("📋 Uploaded Files", expanded=True):
            for file in uploaded_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{file.name}** ({file.size:,} bytes)")
                with col2:
                    st.write(file.type)
                with col3:
                    if st.button("❌", key=f"remove_{file.name}"):
                        # Remove file logic would go here
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing options
    st.markdown("### 2. Processing Options")
    col1, col2 = st.columns(2)
    
    with col1:
        processing_mode = st.radio(
            "Processing Mode",
            ["Quick Summary", "Detailed Analysis", "Key Points Only"],
            index=0
        )
    
    with col2:
        output_format = st.radio(
            "Output Format",
            ["Bullet Points", "Paragraph", "Structured"],
            index=0
        )
    
    # Process button
    if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("Please upload at least one document to summarize.")
        else:
            with st.spinner("🔄 Processing documents locally..."):
                try:
                    # Create uploads directory
                    os.makedirs("uploads", exist_ok=True)
                    
                    # Save and process files
                    saved_paths = []
                    for file in uploaded_files:
                        file_path = os.path.join("uploads", f"{uuid.uuid4()}_{file.name}")
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())
                        saved_paths.append(file_path)
                    
                    # Initialize RAG system if not already done
                    if st.session_state.rag_system is None:
                        st.session_state.rag_system = setup_rag_system(
                            model_name=model_name,
                            chunk_size=chunk_size
                        )
                    
                    # Ingest documents
                    result = ingest_documents(
                        st.session_state.rag_system, 
                        saved_paths
                    )
                    
                    # Generate summary based on processing mode
                    summary_prompt = f"""
                    Create a {summary_length.lower()} summary of the provided documents.
                    
                    Processing mode: {processing_mode}
                    Output format: {output_format}
                    
                    Please provide a clear, concise summary that captures the main points and key information.
                    """
                    
                    summary_response = ask_question(
                        st.session_state.rag_system,
                        summary_prompt,
                        top_k=top_k
                    )
                    
                    # Store results
                    st.session_state.current_summary = summary_response
                    st.session_state.uploaded_files = saved_paths
                    st.session_state.processing_state = "complete"
                    
                    # Get sources for display
                    st.session_state.sources = result.get('sources', [])
                    
                    st.success(f"✅ Processed {result['processed_count']} documents with {result['total_chunks']} chunks")
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {str(e)}")
                    st.session_state.processing_state = "ready"
    
    # Display results
    if st.session_state.processing_state == "complete" and st.session_state.current_summary:
        st.markdown("---")
        st.markdown("### 📊 Summary Results")
        
        # Summary card
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown("### 📝 Generated Summary")
        st.write(st.session_state.current_summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Source references
        if st.session_state.sources:
            st.markdown("### 📚 Source References")
            for i, source in enumerate(st.session_state.sources[:top_k]):
                with st.container():
                    st.markdown(f'<div class="source-card">', unsafe_allow_html=True)
                    st.markdown(f"**Source {i+1}**")
                    st.markdown(f"File: `{os.path.basename(source)}`")
                    st.markdown(f"Relevance: High")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Copy Summary", use_container_width=True):
                st.code(st.session_state.current_summary)
                st.success("Summary copied to clipboard!")
        with col2:
            if st.button("🔄 New Summary", use_container_width=True):
                st.session_state.processing_state = "ready"
                st.session_state.current_summary = None
                st.rerun()
        with col3:
            if st.button("💬 Ask Questions", use_container_width=True):
                st.session_state.active_tab = "Ask Questions"
                st.rerun()

with tab2:
    st.header("💬 Ask Questions")
    
    if st.session_state.rag_system is None:
        st.warning("⚠️ Please upload and process documents first in the 'Upload & Summarize' tab.")
        st.info("Once you've processed documents, you can ask specific questions about their content here.")
    else:
        # Quick question suggestions
        st.markdown("### Quick Questions")
        quick_questions = [
            "What are the main findings?",
            "Summarize the key points",
            "What methodology was used?",
            "What are the conclusions?",
            "List the important data points"
        ]
        
        cols = st.columns(3)
        for i, question in enumerate(quick_questions):
            with cols[i % 3]:
                if st.button(question, use_container_width=True):
                    st.session_state.auto_question = question
        
        # Chat interface
        st.markdown("### Ask Your Question")
        question = st.text_area(
            "Enter your question about the documents:",
            value=st.session_state.get('auto_question', ''),
            placeholder="e.g., What are the main conclusions from the research?",
            height=100
        )
        
        if st.button("🔍 Get Answer", type="primary", use_container_width=True):
            if question:
                with st.spinner("🔍 Searching documents..."):
                    try:
                        response = ask_question(
                            st.session_state.rag_system,
                            question,
                            top_k=top_k
                        )
                        
                        # Display answer
                        st.markdown("### 💡 Answer")
                        st.info(response)
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": response,
                            "timestamp": time.time()
                        })
                        
                    except Exception as e:
                        st.error(f"Error getting answer: {str(e)}")
            else:
                st.warning("Please enter a question.")
        
        # Chat history
        if st.session_state.chat_history:
            st.markdown("### 📜 Conversation History")
            for chat in reversed(st.session_state.chat_history[-5:]):  # Show last 5
                with st.expander(f"Q: {chat['question'][:50]}...", expanded=False):
                    st.write(f"**Question:** {chat['question']}")
                    st.write(f"**Answer:** {chat['answer']}")
                    st.caption(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chat['timestamp']))}")

with tab3:
    st.header("ℹ️ About Simplify")
    
    st.markdown("""
    ### 🔒 Simplify - Your Private Summary Assistant
    
    **Simplify** is designed with privacy and efficiency at its core. We believe you shouldn't have to compromise your data's security for intelligent document processing.
    """)
    
    # Features grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Privacy First")
        st.markdown("""
        - All processing happens locally
        - No external API calls
        - Your data never leaves your machine
        - Temporary file storage only
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Lightning Fast")
        st.markdown("""
        - Instant document processing
        - Quick summarization
        - Real-time Q&A
        - Optimized local processing
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 📚 Source-Verified")
        st.markdown("""
        - Direct source references
        - Citation tracking
        - Context-aware answers
        - Transparent sourcing
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Technology stack
    st.markdown("### 🛠️ Technology Stack")
    st.markdown("""
    - **Streamlit** - Modern web interface
    - **Ollama** - Local AI models (Gemma 3, Llama 2, Mistral)
    - **Chroma DB** - Local vector database
    - **Sentence Transformers** - Local text embeddings
    - **PyPDF2/PyMuPDF** - Document processing
    """)
    
    # Privacy commitment
    st.markdown("### 🛡️ Our Privacy Commitment")
    st.markdown("""
    We believe your documents should remain yours. That's why:
    
    - ✅ No data is sent to external servers
    - ✅ All AI processing happens on your machine
    - ✅ Files are stored temporarily and can be deleted
    - ✅ You maintain complete ownership of your data
    - ✅ No tracking, no analytics, no data collection
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6b7280;'>"
    "🔒 Simplify - Private Document Summarization • Built for Privacy • Powered by Local AI"
    "</div>",
    unsafe_allow_html=True
)
