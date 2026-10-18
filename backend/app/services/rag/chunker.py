import re
from typing import List, Dict, Any, Optional

def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract high-value civic and domain keywords from text, ignoring stopwords.
    """
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "are", "have", "has", "been",
        "shall", "will", "under", "per", "pertaining", "any", "all", "not", "such", "other",
        "into", "about", "which", "whose", "their", "more", "most", "also", "each", "both"
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1

    sorted_kws = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, count in sorted_kws[:max_keywords]]

class ChunkResult:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        section_title: Optional[str] = None,
        page_number: int = 1,
        keywords: Optional[List[str]] = None,
        token_count: int = 0
    ):
        self.chunk_index = chunk_index
        self.content = content.strip()
        self.section_title = section_title or "General Information"
        self.page_number = page_number
        self.keywords = keywords or []
        self.token_count = token_count or len(content.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "content": self.content,
            "section_title": self.section_title,
            "page_number": self.page_number,
            "keywords": self.keywords,
            "token_count": self.token_count
        }

def chunk_document_text(
    text: str,
    default_page: int = 1,
    target_chunk_chars: int = 650,
    overlap_chars: int = 70
) -> List[ChunkResult]:
    """
    Chunk document text by paragraphs or section headers with intelligent overlap.
    Preserves section headers and extracts keywords for hybrid search.
    """
    if not text or not text.strip():
        return []

    chunks: List[ChunkResult] = []
    
    # Check for explicit section breaks like "## Section", "1. SECTION TITLE", "Section N:", "Chapter N:", etc.
    # Matches Markdown headings (any case) OR unheaded major uppercase section titles (e.g., "1. OBJECTIVE & SCOPE")
    # Excludes numbered list items (e.g., "1. Aadhaar Card") by requiring uppercase section titles on unheaded numbered lines
    section_pattern = re.compile(
        r"(?:^|\n)(?:#{1,3}\s+([^\n]+)|(?:\d+\.|\b(?:Section|Chapter|Clause|Part)\s+\w+:?)\s+([A-Z][A-Z0-9\s,\-&/()+]{3,}))(?:\n|$)",
        re.MULTILINE
    )
    
    raw_sections = []
    last_pos = 0
    current_title = "Introduction & Overview"
    
    for match in section_pattern.finditer(text):
        start = match.start()
        if start > last_pos:
            sec_text = text[last_pos:start].strip()
            if sec_text:
                raw_sections.append((current_title, sec_text))
        matched_title = (match.group(1) or match.group(2) or "").strip()
        current_title = matched_title if matched_title else current_title
        last_pos = match.end()
        
    if last_pos < len(text):
        sec_text = text[last_pos:].strip()
        if sec_text:
            raw_sections.append((current_title, sec_text))

    if not raw_sections:
        raw_sections = [("General Guidelines", text.strip())]

    chunk_idx = 0
    for sec_title, sec_content in raw_sections:
        # If section is small enough, keep as single chunk
        if len(sec_content) <= target_chunk_chars + overlap_chars:
            kws = extract_keywords_from_text(sec_content)
            chunks.append(ChunkResult(
                chunk_index=chunk_idx,
                content=f"[{sec_title}]\n{sec_content}",
                section_title=sec_title,
                page_number=default_page,
                keywords=kws,
                token_count=len(sec_content.split())
            ))
            chunk_idx += 1
        else:
            # Split into overlapping windows along sentence or paragraph boundaries
            paragraphs = [p.strip() for p in sec_content.split("\n\n") if p.strip()]
            buffer = ""
            for p in paragraphs:
                if len(buffer) + len(p) > target_chunk_chars:
                    if buffer:
                        kws = extract_keywords_from_text(buffer)
                        chunks.append(ChunkResult(
                            chunk_index=chunk_idx,
                            content=f"[{sec_title}]\n{buffer}",
                            section_title=sec_title,
                            page_number=default_page,
                            keywords=kws,
                            token_count=len(buffer.split())
                        ))
                        chunk_idx += 1
                        # Retain overlap from end of buffer
                        buffer = buffer[-overlap_chars:] + " " + p if overlap_chars > 0 else p
                    else:
                        buffer = p
                else:
                    buffer = (buffer + "\n\n" + p).strip() if buffer else p

            if buffer:
                kws = extract_keywords_from_text(buffer)
                chunks.append(ChunkResult(
                    chunk_index=chunk_idx,
                    content=f"[{sec_title}]\n{buffer}",
                    section_title=sec_title,
                    page_number=default_page,
                    keywords=kws,
                    token_count=len(buffer.split())
                ))
                chunk_idx += 1

    return chunks
