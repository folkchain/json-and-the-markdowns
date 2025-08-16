# JSON & the Markdowns

A powerful Streamlit app that converts TXT and PDF documents into structured Markdown and JSON with comprehensive metadata.

## 🚀 Live Demo

Try it out: [JSON and the Markdowns](https://json-and-the-markdowns.streamlit.app/)

## ✨ Features

- **Multi-format Support**: Upload TXT and PDF files
- **Smart Text Cleaning**: OCR error correction and text normalization
- **Chapter Detection**: Automatic chapter splitting with custom regex support
- **Rich Metadata**: Complete bibliographic information structure
- **Common Metadata**: Apply same metadata to all files in batch
- **Multiple Export Formats**: JSON, Markdown with YAML front matter, Plain text
- **Batch Processing**: Handle multiple files simultaneously
- **Interactive Preview**: Browse and preview converted content

## 📚 Use Cases

Perfect for:
- Digital humanities projects
- Academic research workflows
- Library digitization projects
- Content management systems
- Text analysis and processing
- Book series digitization
- Academic paper collections

## 🛠️ Technical Details

Built with:
- **Streamlit** - Web interface
- **pypdf** - PDF text extraction
- **pandas** - Data handling
- **Python regex** - Text processing

## 📖 Usage

1. Upload your TXT or PDF files
2. Configure processing options in the sidebar
3. Set common metadata that applies to all files (optional)
4. Click "Process Files" to convert
5. Preview results and download in your preferred format

### Common Metadata Features

- **Author(s)**: Set authors for all documents
- **Publisher**: Apply same publisher to all files
- **Year**: Set publication year for all documents
- **Series/Collection**: Group documents in a series
- **Journal Information**: For academic articles
- **Subjects/Keywords**: Classification terms
- **License**: Rights and licensing information

## 🏗️ Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
