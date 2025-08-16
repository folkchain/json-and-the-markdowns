import re
import json
import io
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

@dataclass
class Rule:
    label: str
    pattern: str
    repl: Any
    flags: int = re.UNICODE
    
    def apply(self, text: str) -> str:
        return re.sub(self.pattern, self.repl, text, flags=self.flags)

def apply_rules(text: str, rules: List[Rule]) -> str:
    for r in rules:
        text = r.apply(text)
    return text

# Text cleaning rules
NORMALIZE = [
    Rule("curly single quotes -> '", r"[\u2018\u2019\u201A\u201B\u2039\u203A]", "'"),
    Rule('curly double quotes -> "', r"[\u201C\u201D\u201E\u201F\u00AB\u00BB]", '"'),
    Rule("unicode spaces -> space", r"[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]", " "),
    Rule("ellipsis", r"\u2026", "..."),
    Rule("primes as apostrophes", r"([A-Za-z])[`´′]([A-Za-z])", r"\1'\2"),
    Rule("1/4", "¼", "1/4"), Rule("1/2", "½", "1/2"), Rule("3/4", "¾", "3/4"),
]

MISREADS = [
    Rule("tbe->the", r"\btbe\b", "the", re.IGNORECASE),
    Rule("tbis->this", r"\btbis\b", "this", re.IGNORECASE),
    Rule("tbat->that", r"\btbat\b", "that", re.IGNORECASE),
    Rule("wbat->what", r"\bwbat\b", "what", re.IGNORECASE),
    Rule("wbich->which", r"\bwbich\b", "which", re.IGNORECASE),
    Rule("wbo->who", r"\bwbo\b", "who", re.IGNORECASE),
]

CONTRACTIONS = [
    Rule("cant", r"\bcant\b", "can't", re.IGNORECASE),
    Rule("wont", r"\bwont\b", "won't", re.IGNORECASE),
    Rule("dont", r"\bdont\b", "don't", re.IGNORECASE),
    Rule("Ill", r"\bIll\b", "I'll"),
    Rule("I m", r"\bI m\b", "I'm"),
    Rule("Ive", r"\bIve\b", "I've"),
    Rule("youre", r"\byoure\b", "you're", re.IGNORECASE),
    Rule("theyre", r"\btheyre\b", "they're", re.IGNORECASE),
]

CONFUSIONS = [
    Rule("rn->m (make)", r"\brnake\b", "make", re.IGNORECASE),
    Rule("rn->m (many)", r"\brnany\b", "many", re.IGNORECASE),
    Rule("0f", r"\b0f\b", "of"),
    Rule("t0", r"\bt0\b", "to"),
    Rule("0r", r"\b0r\b", "or"),
]

MERGED = [
    Rule("ofthe", r"\bofthe\b", "of the", re.IGNORECASE),
    Rule("andthe", r"\bandthe\b", "and the", re.IGNORECASE),
    Rule("inthe", r"\binthe\b", "in the", re.IGNORECASE),
]

HYPHENS_WRAP = [
    Rule("soft hyphen", r"\u00AD", ""),
    Rule("dash normalize", r"[—–]", " - "),
    Rule("EOL hyphen + lowercase", r"([a-z])-\s*\r?\n\s*(?=[a-z])", r"\1"),
    Rule("join simple wraps", r"([a-z,;])\s*\r?\n(?=[a-z])", r"\1 "),
    Rule("inword hyphen + spaces", r"(\b[A-Za-z]+)-\s+([A-Za-z]+\b)", r"\1\2"),
]

# Updated whitespace rules with single word line fixes
WHITESPACE = [
    Rule("trim trailing", r"[ \t]+$", "", re.MULTILINE),
    Rule("collapse 3+ spaces", r"[ \t]{3,}", " "),
    Rule("collapse 4+ blank lines", r"(?:\r?\n){4,}", "\n\n"),
    Rule("no space before punct", r"\s+([,.;:!?])", r"\1"),
    Rule("space after sentence", r"([.?!])([A-Z])", r"\1 \2"),
    Rule("collapse 4+ periods", r"\.{4,}", "..."),
    # Fix single words on their own lines (join with next line if it's not a paragraph break)
    Rule("single word lines", r"^(\w+)\s*\n(?=\w)", r"\1 ", re.MULTILINE),
]

def clean_text(text: str) -> str:
    """Apply all text cleaning rules"""
    pipeline = [NORMALIZE, MISREADS, CONTRACTIONS, CONFUSIONS, MERGED, HYPHENS_WRAP, WHITESPACE]
    for group in pipeline:
        text = apply_rules(text, group)
    return text.strip()

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        try:
            import pypdf
            pdf_file = io.BytesIO(pdf_bytes)
            reader = pypdf.PdfReader(pdf_file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        except ImportError:
            import streamlit as st
            st.error("pypdf not installed. PDF text extraction not available.")
            return ""
    except Exception as e:
        import streamlit as st
        st.error(f"Error extracting PDF text: {str(e)}")
        return ""

def guess_title_from_filename(filename: str) -> str:
    """Extract title from filename"""
    stem = Path(filename).stem
    title = re.sub(r"[_]+", " ", stem.strip())
    title = re.sub(r"\s{2,}", " ", title)
    return title

def guess_year_from_name(name: str) -> Optional[int]:
    """Extract year from filename"""
    matches = re.findall(r"(1[6-9]\d{2}|20\d{2})", name)
    if matches:
        try:
            return int(matches[-1])
        except ValueError:
            return None
    return None

def skeleton_doc(publication_type: str = "book") -> Dict[str, Any]:
    """Create document structure specific to publication type"""
    
    # Base structure common to all types
    doc = {
        "data": {
            "title": "",
            "subtitle": "",
            "original_title": "",
            "publication_type": publication_type,
            "language": "en",
            "abstract": "",
            "description": "",
            "year": None
        },
        "authorship": {
            "authors": [],
            "editors": [],
            "contributors": []
        },
        "publication_details": {
            "publisher": "",
            "imprint": "",
            "place_of_publication": "",
            "publication_date": "",
            "edition": "",
            "version": "",
            "volume": "",
            "issue": "",
            "number": "",
            "pages": {"start": None, "end": None, "total": None, "range": ""}
        },
        "identifiers": {
            "doi": "",
            "pmid": "",
            "arxiv_id": "",
            "handle": "",
            "url": "",
            "urn": "",
            "doc_id": "",
            "local_id": ""
        },
        "classification": {
            "subjects": [],
            "keywords": [],
            "tags": [],
            "genre": "",
            "dewey_decimal": "",
            "lcc": "",
            "mesh_terms": []
        },
        "physical_format": {"format": "", "dimensions": "", "weight": "", "binding": ""},
        "digital_format": {
            "filename": "",
            "file_format": "",
            "file_size": 0,
            "mime_type": ""
        },
        "content": {"table_of_contents": [], "chapters": [], "sections": [], "full_text": ""},
        "rights_licensing": {"copyright": "", "license": "", "rights_statement": "", "open_access": False, "usage_rights": ""},
        "citations_references": {
            "bibliography": [],
            "cited_by_count": 0,
            "references_count": 0,
            "citation_formats": {"apa": "", "mla": "", "chicago": "", "bibtex": ""}
        }
    }
    
    # Add publication type specific fields
    if publication_type == "book":
        doc["identifiers"]["isbn"] = ""
        doc["identifiers"]["isbn13"] = ""
        doc["series_info"] = {
            "series_title": "",
            "series_number": "",
            "series_editor": "",
            "collection": ""
        }
    
    elif publication_type in ["article", "journal", "magazine"]:
        doc["journal_info"] = {
            "journal_title": "",
            "journal_abbreviation": "",
            "issn": "",
            "eissn": ""
        }
    
    elif publication_type == "thesis":
        doc["academic_info"] = {
            "institution": "",
            "department": "",
            "degree_type": "",
            "advisor": "",
            "committee_members": []
        }
    
    elif publication_type in ["report", "conference_paper"]:
        doc["organization_info"] = {
            "organization": "",
            "department": "",
            "report_number": "",
            "contract_number": ""
        }
        if publication_type == "conference_paper":
            doc["conference_info"] = {
                "conference_name": "",
                "conference_location": "",
                "conference_date": "",
                "proceedings_title": ""
            }
    
    return doc

# Enhanced chapter detection patterns
CHAPTER_RE_DEFAULT = re.compile(
    r'^\s*(?:chapter|chap\.?)\s+([ivxlcdm]+|\d+)\b(?:[\s:.\-—–]+(.+))?$',
    re.IGNORECASE
)

# Additional patterns for chapter detection
PAGE_NUMBER_PATTERNS = [
    # Just page numbers: "1", "23", "456"
    re.compile(r'^\s*(\d{1,3})\s*$'),
    # Chapter title with page number: "Chapter Title - 23", "Chapter Title / 45"
    re.compile(r'^(.+?)\s*[-/]\s*(\d{1,3})\s*$'),
    # Page number then chapter title: "23 Chapter Title"
    re.compile(r'^(\d{1,3})\s+(.+)$'),
    # Chapter with Roman numerals and page: "Chapter IV - 42"
    re.compile(r'^(chapter\s+[ivxlcdm]+)\s*[-/]\s*(\d{1,3})\s*$', re.IGNORECASE),
]

def is_book_title_line(line: str, book_title: str) -> bool:
    """Check if a line is likely the book title (often ALL CAPS)"""
    line_clean = line.strip()
    title_clean = book_title.strip()
    
    # Check if line is all caps version of title
    if line_clean.upper() == title_clean.upper():
        return True
    
    # Check if line is mostly uppercase and similar to title
    if line_clean.isupper() and len(line_clean) > 5:
        # Simple similarity check - if 70% of words match
        line_words = set(line_clean.lower().split())
        title_words = set(title_clean.lower().split())
        if len(title_words) > 0:
            overlap = len(line_words.intersection(title_words))
            similarity = overlap / len(title_words)
            if similarity > 0.7:
                return True
    
    return False

def is_page_number_line(line: str) -> bool:
    """Check if a line is just a page number or chapter heading with page number"""
    line_clean = line.strip()
    
    for pattern in PAGE_NUMBER_PATTERNS:
        if pattern.match(line_clean):
            return True
    
    return False

def roman_to_int(s: str) -> int:
    """Convert Roman numeral to integer"""
    vals = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    s = s.upper()
    total = 0
    prev = 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        if v < prev: 
            total -= v
        else: 
            total += v
            prev = v
    return total if total else 0

def parse_chapter_number(s: str) -> int:
    """Parse chapter number from string"""
    s = (s or "").strip()
    return int(s) if s.isdigit() else roman_to_int(s)

def split_into_chapters(text: str, chapter_re=CHAPTER_RE_DEFAULT, book_title: str = ""):
    """Split text into chapters with improved detection and cleanup"""
    lines = text.splitlines()
    hits: List[Tuple[int, Optional[int], str]] = []
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # Skip empty lines
        if not line_clean:
            continue
        
        # Skip book title lines
        if book_title and is_book_title_line(line_clean, book_title):
            continue
        
        # Skip page number only lines
        if is_page_number_line(line_clean):
            continue
        
        # Check for chapter patterns
        m = chapter_re.match(line_clean)
        if m:
            num_raw = m.group(1) or ""
            title = (m.group(2) or f"Chapter {num_raw}").strip()
            hits.append((i, parse_chapter_number(num_raw), title))
            continue
        
        # Check for additional chapter patterns with page numbers
        for pattern in PAGE_NUMBER_PATTERNS:
            match = pattern.match(line_clean)
            if match and len(match.groups()) == 2:
                # This could be "Chapter Title - Page" format
                potential_title = match.group(1).strip()
                page_num = match.group(2).strip()
                
                # Check if the first part looks like a chapter title
                if (len(potential_title) > 3 and 
                    not potential_title.isdigit() and 
                    any(word in potential_title.lower() for word in ['chapter', 'part', 'section'])):
                    
                    # Try to extract chapter number from title
                    chapter_match = re.search(r'(?:chapter|chap\.?)\s+([ivxlcdm]+|\d+)', potential_title, re.IGNORECASE)
                    if chapter_match:
                        num_raw = chapter_match.group(1)
                        hits.append((i, parse_chapter_number(num_raw), potential_title))
                        break
    
    if not hits:
        return []
    
    hits.append((len(lines), None, None))  # sentinel end
    chapters = []
    
    for idx in range(len(hits)-1):
        start_line, num, title = hits[idx]
        end_line, _, _ = hits[idx+1]
        
        # Collect content, skipping the chapter header line and cleaning up
        content_lines = []
        for line_idx in range(start_line + 1, end_line):
            line = lines[line_idx].strip()
            
            # Skip book title lines and page numbers in content
            if (book_title and is_book_title_line(line, book_title)) or is_page_number_line(line):
                continue
            
            content_lines.append(lines[line_idx])
        
        body = "\n".join(content_lines).strip()
        chapters.append({"number": num or (idx+1), "title": title, "content": body})
    
    return chapters

def parse_authors(author_string: str) -> List[Dict[str, str]]:
    """Parse author string into list of author dictionaries"""
    if not author_string or not author_string.strip():
        return []
    
    authors = []
    for name in author_string.split(","):
        name = name.strip()
        if name:
            authors.append({"name": name})
    return authors

def parse_subjects(subjects_string: str) -> List[str]:
    """Parse subjects string into list"""
    if not subjects_string or not subjects_string.strip():
        return []
    
    return [s.strip() for s in subjects_string.split(",") if s.strip()]

def build_doc(cleaned_text: str, filename: str, pub_type: str, file_size: int, 
              common_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build document structure from cleaned text with common metadata"""
    doc = skeleton_doc(pub_type)
    
    # Set basic data from filename (can be overridden by common metadata)
    doc["data"]["title"] = guess_title_from_filename(filename)
    doc["data"]["publication_type"] = pub_type
    
    # Extract year from filename (will be overridden by common metadata if provided)
    year = guess_year_from_name(filename)
    if year is not None:
        doc["data"]["year"] = year
    
    # Apply common metadata if provided
    if common_metadata:
        # Title override
        if "title" in common_metadata:
            doc["data"]["title"] = common_metadata["title"]
        
        # Authors
        if "author" in common_metadata:
            doc["authorship"]["authors"] = parse_authors(common_metadata["author"])
        
        # Publication details
        if "publisher" in common_metadata:
            doc["publication_details"]["publisher"] = common_metadata["publisher"]
        
        if "publication_date" in common_metadata:
            doc["publication_details"]["publication_date"] = common_metadata["publication_date"]
        
        if "year" in common_metadata:
            doc["data"]["year"] = common_metadata["year"]  # Override filename year
        
        if "language" in common_metadata:
            doc["data"]["language"] = common_metadata["language"]
        
        if "edition" in common_metadata:
            doc["publication_details"]["edition"] = common_metadata["edition"]
        
        # Series info (for books)
        if "series" in common_metadata and "series_info" in doc:
            doc["series_info"]["series_title"] = common_metadata["series"]
        
        # Journal information (for articles)
        if "journal" in common_metadata and "journal_info" in doc:
            doc["journal_info"]["journal_title"] = common_metadata["journal"]
        
        if "volume" in common_metadata:
            doc["publication_details"]["volume"] = common_metadata["volume"]
        
        if "issue" in common_metadata:
            doc["publication_details"]["issue"] = common_metadata["issue"]
        
        # ISBN (for books)
        if "isbn" in common_metadata and "isbn" in doc["identifiers"]:
            doc["identifiers"]["isbn"] = common_metadata["isbn"]
        
        # Classification
        if "subjects" in common_metadata:
            subjects = parse_subjects(common_metadata["subjects"])
            doc["classification"]["subjects"] = subjects
            doc["classification"]["keywords"] = subjects  # Also add as keywords
    
    # Set digital format info
    ext = Path(filename).suffix.lower().lstrip(".")
    mime = "text/plain" if ext == "txt" else ("application/pdf" if ext == "pdf" else "application/octet-stream")
    
    doc["digital_format"].update({
        "filename": filename,
        "file_format": ext,
        "file_size": file_size,
        "mime_type": mime
    })
    
    doc["identifiers"]["local_id"] = Path(filename).stem
    doc["content"]["full_text"] = cleaned_text
    
    return doc

def yaml_escape(s: str) -> str:
    """Escape string for YAML"""
    if s is None:
        return ""
    s = str(s)
    return "'" + s.replace("'", "''") + "'"

def create_markdown_export(doc: Dict[str, Any]) -> str:
    """Create markdown export with front matter"""
    d = doc
    authors = [a.get("name","").strip() for a in d["authorship"]["authors"]]
    tags = d["classification"]["tags"]
    pages = (d["publication_details"]["pages"].get("range") or "").strip()
    
    lines = [
        "---",
        f"title: {yaml_escape(d['data']['title'])}",
        f"type: {yaml_escape(d['data']['publication_type'])}",
        f"language: {yaml_escape(d['data']['language'])}",
        f"year: {d['data']['year'] if d['data']['year'] is not None else ''}",
        f"publication_date: {yaml_escape(d['publication_details']['publication_date'])}",
        f"publisher: {yaml_escape(d['publication_details']['publisher'])}",
    ]
    
    # Add type-specific fields
    if "journal_info" in d:
        lines.extend([
            f"journal: {yaml_escape(d['journal_info']['journal_title'])}",
            f"volume: {yaml_escape(d['publication_details']['volume'])}",
            f"issue: {yaml_escape(d['publication_details']['issue'])}",
        ])
    
    if "isbn" in d["identifiers"]:
        lines.append(f"isbn: {yaml_escape(d['identifiers']['isbn'])}")
    
    lines.extend([
        f"pages: {yaml_escape(pages)}",
        "authors:"
    ])
    
    if authors:
        lines += [f"  - {yaml_escape(a)}" for a in authors]
    else:
        lines += ["  - "]
    
    # Add subjects as tags if no tags specified
    if not tags and d["classification"]["subjects"]:
        tags = d["classification"]["subjects"]
    
    lines += ["tags:"]
    if tags:
        lines += [f"  - {yaml_escape(t)}" for t in tags]
    else:
        lines += ["  - "]
    
    lines += [
        "identifiers:",
        f"  doi: {yaml_escape(d['identifiers']['doi'])}",
        f"  url: {yaml_escape(d['identifiers']['url'])}",
        f"  local_id: {yaml_escape(d['identifiers']['local_id'])}",
        "---",
        ""
    ]
    
    body = doc["content"]["full_text"] or ""
    if doc["content"]["chapters"]:
        parts = []
        for ch in doc["content"]["chapters"]:
            title = ch.get("title") or f"Chapter {ch.get('number','')}"
            parts.append(f"\n\n## {title}\n\n{ch.get('content','')}")
        body = "".join(parts).lstrip()
    
    return "\n".join(lines) + body
