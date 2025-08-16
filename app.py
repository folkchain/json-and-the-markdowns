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
    
    # Initialize session state for results
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = None
    if 'export_settings' not in st.session_state:
        st.session_state.export_settings = {'markdown': False, 'text': False}
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Publication type
        pub_types = [
            "book","article","serial","magazine","journal","newspaper",
            "thesis","report","conference_paper","chapter","preprint","other"
        ]
        publication_type = st.selectbox("Publication Type", pub_types, index=0)
        
        # Common Metadata Section
        st.subheader("📝 Common Metadata")
        with st.expander("Set metadata for all files", expanded=False):
            st.markdown("*Apply the same metadata to all uploaded files*")
            
            # Title
            common_title = st.text_input(
                "Title", 
                placeholder="Document Title",
                help="Override filename-based title detection"
            )
            
            # Author information
            common_author = st.text_input(
                "Author(s)", 
                placeholder="John Doe, Jane Smith",
                help="Separate multiple authors with commas"
            )
            
            # Publication details
            col1, col2 = st.columns(2)
            with col1:
                common_publisher = st.text_input("Publisher")
                common_date = st.date_input(
                    "Publication Date",
                    value=None,
                    help="Full publication date"
                )
            with col2:
                common_language = st.selectbox(
                    "Language", 
                    ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja"], 
                    index=0
                )
                common_series = st.text_input("Series/Collection")
            
            # Publication type specific fields
            if publication_type in ["article", "journal", "magazine"]:
                st.markdown("**Journal Information:**")
                common_journal = st.text_input("Journal Title")
                jcol1, jcol2 = st.columns(2)
                with jcol1:
                    common_volume = st.text_input("Volume")
                with jcol2:
                    common_issue = st.text_input("Issue")
            else:
                common_journal = ""
                common_volume = ""
                common_issue = ""
            
            if publication_type == "book":
                st.markdown("**Book Information:**")
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    common_isbn = st.text_input("ISBN")
                with bcol2:
                    common_edition = st.text_input("Edition")
            else:
                common_isbn = ""
                common_edition = ""
            
            # Classification
            common_subjects = st.text_input(
                "Subjects/Keywords", 
                placeholder="history, science, literature",
                help="Separate with commas"
            )
            
            # Clear button
            if st.button("🗑️ Clear All Common Metadata", help="Reset all common metadata fields"):
                st.rerun()
        
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
        else:
            custom_chapter_regex = ""
        
        # Export options
        st.subheader("Export Options")
        export_markdown = st.checkbox("Export Markdown", value=False)
        export_text = st.checkbox("Export Plain Text", value=False)
        
        # Store export settings in session state
        st.session_state.export_settings = {
            'markdown': export_markdown,
            'text': export_text
        }
        
        # Help section
        with st.expander("ℹ️ Help & Tips"):
            st.markdown("""
            **Supported Files:** TXT and PDF
            
            **Common Metadata:**
            - Set once, applies to all files
            - Publication type determines available fields
            - Individual file metadata still detected
            
            **Text Cleaning Features:**
            - OCR error correction
            - Punctuation normalization
            - Single word line fixes
            - Page number removal
            
            **Chapter Detection:**
            - Automatically finds chapter headings
            - Removes book title headers
            - Handles page number patterns
            - Supports Roman numerals
            
            **Export Formats:**
            - JSON with full metadata
            - Markdown with YAML front matter
            - Clean plain text
            """)
    
    # Collect common metadata
    common_metadata = {"publication_type": publication_type}
    
    if common_title.strip():
        common_metadata["title"] = common_title.strip()
    if common_author.strip():
        common_metadata["author"] = common_author.strip()
    if common_publisher.strip():
        common_metadata["publisher"] = common_publisher.strip()
    if common_date:
        common_metadata["publication_date"] = common_date.isoformat()
        common_metadata["year"] = common_date.year
    if common_language and common_language != "en":
        common_metadata["language"] = common_language
    if common_series.strip():
        common_metadata["series"] = common_series.strip()
    if common_journal.strip():
        common_metadata["journal"] = common_journal.strip()
    if common_volume.strip():
        common_metadata["volume"] = common_volume.strip()
    if common_issue.strip():
        common_metadata["issue"] = common_issue.strip()
    if common_isbn.strip():
        common_metadata["isbn"] = common_isbn.strip()
    if common_edition.strip():
        common_metadata["edition"] = common_edition.strip()
    if common_subjects.strip():
        common_metadata["subjects"] = common_subjects.strip()
    
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
            
            # Show common metadata preview if any is set
            if len(common_metadata) > 1:  # More than just publication_type
                with st.expander("📋 Common Metadata Preview", expanded=True):
                    st.markdown("*The following metadata will be applied to all files:*")
                    for key, value in common_metadata.items():
                        if key == "author":
                            st.write(f"**Authors:** {value}")
                        elif key == "subjects":
                            st.write(f"**Subjects:** {value}")
                        elif key == "publication_type":
                            continue  # Skip showing this
                        else:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
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
                    results = process_files(
                        uploaded_files, 
                        publication_type, 
                        apply_cleaning, 
                        split_chapters, 
                        custom_chapter_regex if split_chapters else None,
                        common_metadata
                    )
                    # Store results in session state
                    st.session_state.processing_results = results
                    st.rerun()
    
    with col2:
        st.subheader("ℹ️ About This Tool")
        st.markdown("""
        This tool converts documents to structured JSON format with comprehensive metadata.
        
        **✨ Key Features:**
        - 📖 **Multi-format support**: TXT and PDF files
        - 🧹 **Smart text cleaning**: OCR error correction, punctuation normalization
        - 📑 **Chapter detection**: Automatic splitting with improved patterns
        - 🏷️ **Rich metadata**: Publication type-specific fields
        - 📝 **Multiple exports**: JSON, Markdown, Plain Text
        - 🚀 **Batch processing**: Handle multiple files at once
        - 📋 **Common metadata**: Apply same metadata to all files
        
        **📚 Publication Types:**
        - **Books**: ISBN, edition, publisher info
        - **Articles**: Journal, volume, issue info
        - **Thesis**: Academic institution fields
        - **Reports**: Organization and series info
        """)
        
        # Show sample metadata structure based on publication type
        if publication_type == "book":
            sample_structure = {
                "data": {"title": "Book Title", "publication_type": "book", "year": 2024},
                "authorship": {"authors": [{"name": "Author Name"}]},
                "publication_details": {"publisher": "Publisher", "edition": "1st"},
                "identifiers": {"isbn": "978-0123456789"},
                "content": {"full_text": "...", "chapters": []}
            }
        elif publication_type in ["article", "journal"]:
            sample_structure = {
                "data": {"title": "Article Title", "publication_type": "article", "year": 2024},
                "authorship": {"authors": [{"name": "Author Name"}]},
                "journal_info": {"journal_title": "Journal Name", "volume": "10", "issue": "2"},
                "content": {"full_text": "..."}
            }
        else:
            sample_structure = {
                "data": {"title": "Document Title", "publication_type": publication_type, "year": 2024},
                "authorship": {"authors": [{"name": "Author Name"}]},
                "content": {"full_text": "..."}
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
    
    # Display results if they exist
    if st.session_state.processing_results:
        display_results(st.session_state.processing_results)

def process_files(uploaded_files, publication_type, apply_cleaning, split_chapters, 
                 custom_regex, common_metadata):
    """Process uploaded files and return results"""
    
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
            
            # Build document structure with common metadata
            doc = build_doc(cleaned_text, uploaded_file.name, publication_type, 
                          uploaded_file.size, common_metadata)
            
            # Handle chapter splitting
            if split_chapters and cleaned_text.strip():
                chapter_re = CHAPTER_RE_DEFAULT
                if custom_regex and custom_regex.strip():
                    try:
                        chapter_re = re.compile(custom_regex.strip(), re.IGNORECASE)
                    except re.error as e:
                        st.warning(f"Invalid regex pattern for {uploaded_file.name}, using default: {e}")
                
                # Get book title for removal
                book_title = doc["data"]["title"]
                chapters = split_into_chapters(cleaned_text, chapter_re, book_title)
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
    
    return results

def display_results(results):
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
    
    # Immediate Download Section - Always visible after processing
    st.subheader("📥 Download Options")
    
    successful_results = [r for r in results if r['success']]
    export_settings = st.session_state.export_settings
    
    if len(successful_results) == 1:
        # Single file downloads
        result = successful_results[0]
        doc = result['doc']
        filename_base = Path(result['filename']).stem
        
        st.write(f"**Downloads for:** {result['filename']}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # JSON download
            json_str = json.dumps(doc, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"{filename_base}.json",
                mime="application/json",
                use_container_width=True,
                key=f"json_{filename_base}"
            )
        
        with col2:
            if export_settings['markdown']:
                # Markdown download
                md_content = create_markdown_export(doc)
                st.download_button(
                    label="📝 Download Markdown",
                    data=md_content,
                    file_name=f"{filename_base}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"md_{filename_base}"
                )
            else:
                st.info("Enable Markdown export in settings")
        
        with col3:
            if export_settings['text']:
                # Plain text download
                text_content = get_text_content(doc)
                st.download_button(
                    label="📃 Download Text",
                    data=text_content,
                    file_name=f"{filename_base}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"txt_{filename_base}"
                )
            else:
                st.info("Enable text export in settings")
        
        with col4:
            # Individual ZIP for single file (all formats)
            zip_buffer = create_single_file_zip(result, export_settings)
            st.download_button(
                label="📦 Download ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{filename_base}_all_formats.zip",
                mime="application/zip",
                use_container_width=True,
                key=f"zip_{filename_base}"
            )
    
    else:
        # Multiple files - batch download options
        st.write(f"**Batch downloads for {len(successful_results)} files**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # JSON only ZIP
            json_zip = create_format_zip(successful_results, "json")
            st.download_button(
                label="📄 All JSON Files",
                data=json_zip.getvalue(),
                file_name="all_json_files.zip",
                mime="application/zip",
                use_container_width=True,
                key="batch_json"
            )
        
        with col2:
            if export_settings['markdown']:
                # Markdown only ZIP
                md_zip = create_format_zip(successful_results, "markdown")
                st.download_button(
                    label="📝 All Markdown Files",
                    data=md_zip.getvalue(),
                    file_name="all_markdown_files.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="batch_md"
                )
            else:
                st.info("Enable Markdown export in settings")
        
        with col3:
            if export_settings['text']:
                # Text only ZIP
                txt_zip = create_format_zip(successful_results, "text")
                st.download_button(
                    label="📃 All Text Files",
                    data=txt_zip.getvalue(),
                    file_name="all_text_files.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="batch_txt"
                )
            else:
                st.info("Enable text export in settings")
        
        with col4:
            # Complete package with all formats
            complete_zip = create_complete_zip(successful_results, export_settings)
            st.download_button(
                label="📦 Complete Package",
                data=complete_zip.getvalue(),
                file_name="complete_document_package.zip",
                mime="application/zip",
                use_container_width=True,
                key="batch_complete"
            )
    
    # Results tabs for detailed view
    tab1, tab2 = st.tabs(["📋 Summary", "📄 Preview"])
    
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
                    authors = [a.get("name", "") for a in doc["authorship"]["authors"]]
                    st.write(f"**Authors:** {', '.join(authors) if authors else 'Not specified'}")
                with col2:
                    st.write(f"**Year:** {doc['data']['year'] or 'Not specified'}")
                    pub_details = doc.get('publication_details', {})
                    st.write(f"**Publisher:** {pub_details.get('publisher', 'Not specified')}")
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

def get_text_content(doc):
    """Extract text content from document"""
    if doc["content"]["chapters"]:
        parts = []
        for ch in doc["content"]["chapters"]:
            title = ch.get("title") or f"Chapter {ch.get('number','')}"
            parts.append(f"{title}\n\n{ch.get('content','')}\n\n")
        return "".join(parts).rstrip() + "\n"
    return doc["content"]["full_text"]

def create_single_file_zip(result, export_settings):
    """Create ZIP package for a single file with all formats"""
    zip_buffer = io.BytesIO()
    filename_base = Path(result['filename']).stem
    doc = result['doc']
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add JSON
        json_str = json.dumps(doc, ensure_ascii=False, indent=2)
        zip_file.writestr(f"{filename_base}.json", json_str)
        
        # Add Markdown if requested
        if export_settings['markdown']:
            md_content = create_markdown_export(doc)
            zip_file.writestr(f"{filename_base}.md", md_content)
        
        # Add text if requested
        if export_settings['text']:
            text_content = get_text_content(doc)
            zip_file.writestr(f"{filename_base}.txt", text_content)
    
    zip_buffer.seek(0)
    return zip_buffer

def create_format_zip(successful_results, format_type):
    """Create ZIP package for specific format only"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for result in successful_results:
            filename_base = Path(result['filename']).stem
            doc = result['doc']
            
            if format_type == "json":
                json_str = json.dumps(doc, ensure_ascii=False, indent=2)
                zip_file.writestr(f"{filename_base}.json", json_str)
            elif format_type == "markdown":
                md_content = create_markdown_export(doc)
                zip_file.writestr(f"{filename_base}.md", md_content)
            elif format_type == "text":
                text_content = get_text_content(doc)
                zip_file.writestr(f"{filename_base}.txt", text_content)
    
    zip_buffer.seek(0)
    return zip_buffer

def create_complete_zip(successful_results, export_settings):
    """Create complete ZIP package with all files and formats"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for result in successful_results:
            filename_base = Path(result['filename']).stem
            doc = result['doc']
            
            # Add JSON
            json_str = json.dumps(doc, ensure_ascii=False, indent=2)
            zip_file.writestr(f"json/{filename_base}.json", json_str)
            
            # Add Markdown if requested
            if export_settings['markdown']:
                md_content = create_markdown_export(doc)
                zip_file.writestr(f"markdown/{filename_base}.md", md_content)
            
            # Add text if requested
            if export_settings['text']:
                text_content = get_text_content(doc)
                zip_file.writestr(f"text/{filename_base}.txt", text_content)
    
    zip_buffer.seek(0)
    return zip_buffer

if __name__ == "__main__":
    main()
