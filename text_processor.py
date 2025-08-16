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

WHITESPACE = [
    Rule("trim trailing", r"[ \t]+$", "", re.MULTILINE),
    Rule("collapse 3+ spaces", r"[ \t]{3,}", " "),
    Rule("collapse 4+ blank lines", r"(?:\r?\n){4,}", "\n\n"),
    Rule("no space before punct", r"\s+([,.;:!?])", r"\1"),
    Rule("space after sentence", r"([.?!])([A-Z])", r"\1 \2"),
    Rule("collapse 4+ periods", r"\.{4,}", "..."),
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

def skeleton_doc() -> Dict[str, Any]:
    """Create empty document structure"""
    return {
        "data": {
            "title": "",
            "subtitle": "",
            "original_title": "",
            "publication_type": "book",
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
        "series_info": {
            "series_title": "",
            "series_number": "",
            "series_editor": "",
            "collection": ""
        },
        "journal_info": {
            "journal_title": "",
            "journal_abbreviation": "",
            "issn": "",
            "eissn": ""
        },
        "identifiers": {
            "isbn": "",
            "isbn13": "",
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

CHAPTER_RE_DEFAULT = re.compile(
    r'^\s*(?:chapter|chap\.?)\s+([ivxlcdm]+|\d+)\b(?:[\s:.\-—–]+(.+))?$',
    re.IGNORECASE
)

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

def split_into_chapters(text: str, chapter_re=CHAPTER_RE_DEFAULT):
    """Split text into chapters"""
    lines = text.splitlines()
    hits: List[Tuple[int, Optional[int], str]] = []
    for i, line in enumerate(lines):
        m = chapter_re.match(line.strip())
        if m:
            num_raw = m.group(1) or ""
            title = (m.group(2) or f"Chapter {num_raw}").strip()
            hits.append((i, parse_chapter_number(num_raw), title))
    
    if not hits:
        return []
    
    hits.append((len(lines), None, None))  # sentinel end
    chapters = []
    for idx in range(len(hits)-1):
        start_line, num, title = hits[idx]
        end_line, _, _ = hits[idx+1]
        body = "\n".join(lines[start_line+1:end_line]).strip()
        chapters.append({"number": num or (idx+1), "title": title, "content": body})
    return chapters

def build_doc(cleaned_text: str, filename: str, pub_type: str, file_size: int) -> Dict[str, Any]:
    """Build document structure from cleaned text"""
    doc = skeleton_doc()
    
    # Set basic data
    doc["data"]["title"] = guess_title_from_filename(filename)
    doc["data"]["publication_type"] = pub_type
    
    year = guess_year_from_name(filename)
    if year is not None:
        doc["data"]["year"] = year
    
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
        f"publisher: {yaml_escape(d['publication_details']['publisher'])}",
        f"journal: {yaml_escape(d['journal_info']['journal_title'])}",
        f"volume: {yaml_escape(d['publication_details']['volume'])}",
        f"issue: {yaml_escape(d['publication_details']['issue'])}",
        f"pages: {yaml_escape(pages)}",
        "authors:"
    ]
    if authors:
        lines += [f"  - {yaml_escape(a)}" for a in authors]
    else:
        lines += ["  - "]
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
