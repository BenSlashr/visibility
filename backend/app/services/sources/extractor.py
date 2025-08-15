import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from ...schemas.analysis import AnalysisSourceCreate


class SourceExtractor:
    """Extraction de sources (URLs/citations) depuis un texte IA.

    Stratégies supportées:
      - URLs brutes (http/https)
      - Liens Markdown: [titre](url)
      - Section "Sources:" / "Références:" (heuristique)
      - Labels de citation [1], [2], ... associés à des URLs proches
    """

    URL_PATTERN = re.compile(r"https?://[^\s)\]]+", re.IGNORECASE)
    MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    FOOTNOTE_LABEL_PATTERN = re.compile(r"\[(\d+)\]")

    def extract(self, text: str, max_items: int = 20) -> List[AnalysisSourceCreate]:
        if not text or not text.strip():
            return []

        sources: Dict[str, AnalysisSourceCreate] = {}

        # 1) Liens Markdown
        for match in self.MD_LINK_PATTERN.finditer(text):
            title = match.group(1).strip()
            url = match.group(2).strip()
            position = match.start()
            snippet = self._extract_snippet(text, position)
            domain = self._domain(url)
            sources.setdefault(url, AnalysisSourceCreate(
                url=url, title=title, domain=domain, snippet=snippet, position=position
            ))

        # 2) URLs brutes
        for match in self.URL_PATTERN.finditer(text):
            url = match.group(0).strip().rstrip(').,;')
            if url not in sources:
                position = match.start()
                snippet = self._extract_snippet(text, position)
                domain = self._domain(url)
                sources[url] = AnalysisSourceCreate(url=url, domain=domain, snippet=snippet, position=position)

        # 3) Heuristique "Sources:" -> capter URLs après la section
        for section_label in ("Sources:", "Références:", "References:"):
            idx = text.lower().find(section_label.lower())
            if idx != -1:
                tail = text[idx: idx + 2000]  # fenêtre après la section
                for m in self.URL_PATTERN.finditer(tail):
                    url = m.group(0).strip().rstrip(').,;')
                    if url not in sources:
                        pos = idx + m.start()
                        snippet = self._extract_snippet(text, pos)
                        sources[url] = AnalysisSourceCreate(url=url, domain=self._domain(url), snippet=snippet, position=pos)

        # 4) Labels de citation [1], [2] proches d’URL
        for m in self.FOOTNOTE_LABEL_PATTERN.finditer(text):
            label = f"[{m.group(1)}]"
            window_start = max(0, m.start() - 200)
            window_end = min(len(text), m.end() + 400)
            window = text[window_start:window_end]
            url_match = self.URL_PATTERN.search(window)
            if url_match:
                url = url_match.group(0).strip().rstrip(').,;')
                if url not in sources:
                    pos = window_start + url_match.start()
                    snippet = self._extract_snippet(text, pos)
                    sources[url] = AnalysisSourceCreate(url=url, domain=self._domain(url), snippet=snippet, position=pos, citation_label=label)

        # Limiter, préserver ordre d’apparition
        ordered = sorted(sources.values(), key=lambda s: (s.position or 0))[:max_items]
        return ordered

    @staticmethod
    def _domain(url: str) -> str:
        try:
            netloc = urlparse(url).netloc.lower()
            return netloc[4:] if netloc.startswith('www.') else netloc
        except Exception:
            return ''

    @staticmethod
    def _extract_snippet(text: str, pos: int, radius: int = 80) -> str:
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        return text[start:end].strip()


source_extractor = SourceExtractor()



