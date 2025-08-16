# JSON & the Markdowns: A Document to JSON Converter

A powerful Streamlit app that converts TXT and PDF documents into structured JSON format with comprehensive metadata.

## 🚀 Live Demo

Try it out: [JSON and the Markdowns](https://json-and-the-markdowns.streamlit.app/)

## ✨ Features

- **Multi-format Support**: Upload TXT and PDF files
- **Smart Text Cleaning**: OCR error correction and text normalization
- **Chapter Detection**: Automatic chapter splitting with custom regex support
- **Rich Metadata**: Complete bibliographic information structure
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

## 🛠️ Technical Details

Built with:
- **Streamlit** - Web interface
- **pypdf** - PDF text extraction
- **pandas** - Data handling
- **Python regex** - Text processing

## 📖 Usage

1. Upload your TXT or PDF files
2. Configure processing options in the sidebar
3. Click "Process Files" to convert
4. Preview results and download in your preferred format

## 🏗️ Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
