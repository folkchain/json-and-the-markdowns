import streamlit as st
import json
import io
import zipfile
from pathlib import Path
import pandas as pd
from text_processor import *

# Configure page
st.set_page_config(
    page_title="JSON and the Markdowns", 
    page_icon="📄", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📄 JSON and the Markdowns")
    st.markdown("Convert TXT and PDF documents to structured JSON with metadata, plus export options.")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Publication type
        pub_types = [
            "book","article","serial","magazine","journal","newspaper",
            "thesis","report","conference_paper","chapter","preprint","other"
        ]
        publication_type = st.selectbox("Publication Type", pub_types, index=0)
        
        # Text processing options
        st.subheader("Text Processing")
        apply_cleaning = st.checkbox("Apply text cleaning rules", value=True, 
                                   help="Fix OCR errors, normalize punctuation, etc.")
        
        # Chapter splitting
        split_chapters = st.checkbox("Split into chapters", value=False,
                                   help="Detect and split chapters automatically")
        
        if split_chapters:
            custom_chapter_regex = st.text_input(
                "Custom chapter regex (optional)",
                placeholder=r"^\s*(?:chapter|chap\.?)\s+([ivxlcdm]+|\d+)\b",
                help="Leave empty to use default pattern"
            )
        
        # Export options
        st.subheader("Export Options")
        export_markdown = st.checkbox("Export Markdown", value=False)
        export_text = st.checkbox("Export Plain Text", value=False)
        
        # Help section
        with st.expander("ℹ️ Help & Tips"):
            st.markdown("""
            **Supported Files:** TXT and PDF
            
            **Text Cleaning Features:**
            - OCR error correction
            - Punctuation normalization
            - Ligature fixes
            - Whitespace cleanup
            
            **Chapter Detection:**
            - Automatically finds chapter headings
            - Supports Roman numerals
            - Customizable regex patterns
            
            **Export Formats:**
            - JSON with full metadata
            - Markdown with YAML front matter
            - Clean plain text
            """)
    
    # Main content area
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Choose TXT or PDF files",
            type=['txt', 'pdf'],
            accept_multiple_files=True,
            help="Upload one or more TXT or PDF files to convert"
        )
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} file(s)")
            
            # Show file details
            with st.expander("📋 File Details"):
                for file in uploaded_files:
                    st.write(f"**{file.name}**")
                    st.write(f"Size: {file.size:,} bytes")
                    st.write(f"Type: {file.type}")
                    st.write("---")
            
            # Process files button
            if st.button("🔄 Process Files", type="primary", use_container_width=True):
                with st.spinner("Processing files..."):
                    process_files(uploaded_files, publication_type, apply_cleaning, 
                                split_chapters, custom_chapter_regex if split_chapters else None,
                                export_markdown, export_text)
    
    with col2:
        st.subheader("ℹ️ About This Tool")
        st.markdown("""
        This tool converts documents to structured JSON format with comprehensive metadata.
        
        **✨ Key Features:**
        - 📖 **Multi-format support**: TXT and PDF files
        - 🧹 **Smart text cleaning**: OCR error correction, punctuation normalization
        - 📑 **Chapter detection**: Automatic splitting with custom patterns
        - 🏷️ **Rich metadata**: Complete bibliographic information
        - 📝 **Multiple exports**: JSON, Markdown, Plain Text
        - 🚀 **Batch processing**: Handle multiple files at once
        
        **📚 Metadata Structure:**
        """)
        
        # Show sample metadata structure
        sample_structure = {
            "data": {"title": "Document Title", "publication_type": "book", "year": 2024},
            "authorship": {"authors": [{"name": "Author Name"}]},
            "publication_details": {"publisher": "Publisher", "pages": {"total": 100}},
            "content": {"full_text": "...", "chapters": []},
            "identifiers": {"doi": "", "isbn": ""},
            "classification": {"subjects": [], "keywords": []}
        }
        
        with st.expander("📋 Sample JSON Structure"):
            st.json(sample_structure)
        
        st.markdown("""
        **🎯 Perfect for:**
        - Digital humanities projects
        - Academic research
        - Library digitization
        - Content management systems
        - Text analysis workflows
        """)

def process_files(uploaded_files, publication_type, apply_cleaning, split_chapters, custom_regex, export_markdown, export_text):
    """Process uploaded files and display results"""
    
    results = []
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}...")
        
        try:
            # Read file content
            if uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    raw_text = content.decode('utf-8', errors='replace')
                else:
                    raw_text = str(content)
            elif uploaded_file.type == "application/pdf" or uploaded_file.name.endswith('.pdf'):
                raw_text = extract_pdf_text(uploaded_file.read())
                if not raw_text.strip():
                    st.warning(f"No text extracted from {uploaded_file.name}. PDF might be image-based.")
            else:
                st.error(f"Unsupported file type: {uploaded_file.type}")
                continue
            
            # Apply text cleaning
            if apply_cleaning:
                cleaned_text = clean_text(raw_text)
            else:
                cleaned_text = raw_text
            
            # Build document structure
            doc = build_doc(cleaned_text, uploaded_file.name, publication_type, uploaded_file.size)
            
            # Handle chapter splitting
            if split_chapters and cleaned_text.strip():
                chapter_re = CHAPTER_RE_DEFAULT
                if custom_regex and custom_regex.strip():
                    try:
                        chapter_re = re.compile(custom_regex.strip(), re.IGNORECASE)
                    except re.error as e:
                        st.warning(f"Invalid regex pattern for {uploaded_file.name}, using default: {e}")
                
                chapters = split_into_chapters(cleaned_text, chapter_re)
                if chapters:
                    doc["content"]["chapters"] = chapters
                    doc["content"]["table_of_contents"] = [
                        {"level": 1, "title": c["title"], "section_id": f"ch-{i+1}"}
                        for i, c in enumerate(chapters)
                    ]
                    # Clear full text if chapters found
                    doc["content"]["full_text"] = ""
            
            results.append({
                'filename': uploaded_file.name,
                'doc': doc,
                'success': True,
                'error': None,
                'chapters_found': len(doc["content"]["chapters"]) if doc["content"]["chapters"] else 0
            })
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            results.append({
                'filename': uploaded_file.name,
                'doc': None,
                'success': False,
                'error': str(e),
                'chapters_found': 0
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    display_results(results, export_markdown, export_text)

def display_results(results, export_markdown, export_text):
    """Display processing results and download options"""
    
    st.subheader("📊 Processing Results")
    
    # Summary metrics
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    total_chapters = sum(r.get('chapters_found', 0) for r in results if r['success'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files", len(results))
    with col2:
        st.metric("Successful", successful, delta=None)
    with col3:
        st.metric("Failed", failed, delta=None if failed == 0 else f"-{failed}")
    with col4:
        st.metric("Chapters Found", total_chapters)
    
    if successful == 0:
        st.error("No files were successfully processed.")
        return
    
    # Results tabs
    tab1, tab2, tab3 = st.tabs(["📋 Summary", "📄 Preview", "📥 Downloads"])
    
    with tab1:
        # Create summary dataframe
        summary_data = []
        for result in results:
            summary_data.append({
                'Filename': result['filename'],
                'Status': '✅ Success' if result['success'] else '❌ Failed',
                'Title': result['doc']['data']['title'] if result['success'] else '-',
                'Type': result['doc']['data']['publication_type'] if result['success'] else '-',
                'Year': result['doc']['data']['year'] if result['success'] and result['doc']['data']['year'] else '-',
                'Size (bytes)': f"{result['doc']['digital_format']['file_size']:,}" if result['success'] else '-',
                'Chapters': result.get('chapters_found', 0),
                'Error': result['error'] if not result['success'] else ''
            })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        # Preview successful files
        successful_results = [r for r in results if r['success']]
        if successful_results:
            selected_file = st.selectbox(
                "Select file to preview:",
                options=range(len(successful_results)),
                format_func=lambda x: successful_results[x]['filename']
            )
            
            if selected_file is not None:
                doc = successful_results[selected_file]['doc']
                
                # Show key metadata
                st.subheader("📋 Metadata")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Title:** {doc['data']['title']}")
                    st.write(f"**Type:** {doc['data']['publication_type']}")
                    st.write(f"**Language:** {doc['data']['language']}")
                with col2:
                    st.write(f"**Year:** {doc['data']['year'] or 'Not specified'}")
                    st.write(f"**File Size:** {doc['digital_format']['file_size']:,} bytes")
                    st.write(f"**Chapters:** {len(doc['content']['chapters'])}")
                
                # Show content preview
                st.subheader("📄 Content Preview")
                if doc['content']['chapters']:
                    chapter_options = [f"Chapter {c['number']}: {c['title']}" for c in doc['content']['chapters']]
                    selected_chapter = st.selectbox("Select chapter:", chapter_options)
                    if selected_chapter:
                        chapter_idx = int(selected_chapter.split(':')[0].split()[-1]) - 1
                        if 0 <= chapter_idx < len(doc['content']['chapters']):
                            chapter_content = doc['content']['chapters'][chapter_idx]['content']
                            st.text_area("Chapter content:", chapter_content[:1000] + "..." if len(chapter_content) > 1000 else chapter_content, height=200)
                else:
                    full_text = doc['content']['full_text']
                    preview_text = full_text[:1000] + "..." if len(full_text) > 1000 else full_text
                    st.text_area("Document content:", preview_text, height=200)
                
                # Full JSON structure
                with st.expander("🔍 Complete JSON Structure"):
                    st.json(doc)
    
    with tab3:
        # Download section
        st.subheader("📥 Download Options")
        
        successful_results = [r for r in results if r['success']]
        
        if len(successful_results) == 1:
            # Single file downloads
            result = successful_results[0]
            doc = result['doc']
            filename_base = Path(result['filename']).stem
            
            st.write(f"**Downloads for:** {result['filename']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # JSON download
                json_str = json.dumps(doc, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_str,
                    file_name=f"{filename_base}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                if export_markdown:
                    # Markdown download
                    md_content = create_markdown_export(doc)
                    st.download_button(
                        label="📝 Download Markdown",
                        data=md_content,
                        file_name=f"{filename_base}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                else:
                    st.info("Enable Markdown export in settings")
            
            with col3:
                if export_text:
                    # Plain text download
                    text_content = get_text_content(doc)
                    st.download_button(
                        label="📃 Download Text",
                        data=text_content,
                        file_name=f"{filename_base}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.info("Enable text export in settings")
        
        else:
            # Multiple files - create ZIP
            st.write(f"**Bulk download for {len(successful_results)} files**")
            
            zip_buffer = create_zip_package(successful_results, export_markdown, export_text)
            
            st.download_button(
                label="📦 Download All Files (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="converted_documents.zip",
                mime="application/zip",
                use_container_width=True
            )

def get_text_content(doc):
    """Extract text content from document"""
    if doc["content"]["chapters"]:
        parts = []
        for ch in doc["content"]["chapters"]:
            title = ch.get("title") or f"Chapter {ch.get('number','')}"
            parts.append(f"{title}\n\n{ch.get('content','')}\n\n")
        return "".join(parts).rstrip() + "\n"
    return doc["content"]["full_text"]

def create_zip_package(successful_results, export_markdown, export_text):
    """Create ZIP package with all files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for result in successful_results:
            filename_base = Path(result['filename']).stem
            doc = result['doc']
            
            # Add JSON
            json_str = json.dumps(doc, ensure_ascii=False, indent=2)
            zip_file.writestr(f"{filename_base}.json", json_str)
            
            # Add Markdown if requested
            if export_markdown:
                md_content = create_markdown_export(doc)
                zip_file.writestr(f"{filename_base}.md", md_content)
            
            # Add text if requested
            if export_text:
                text_content = get_text_content(doc)
                zip_file.writestr(f"{filename_base}.txt", text_content)
    
    zip_buffer.seek(0)
    return zip_buffer

if __name__ == "__main__":
    main()
