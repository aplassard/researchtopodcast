"""Document loading utilities."""

from pathlib import Path
import aiofiles

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class DocumentLoader:
    """Loads content from various document formats."""
    
    async def load(self, path: Path) -> str:
        """Load content from a document."""
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            return await self._load_pdf(path)
        elif suffix in [".md", ".txt"]:
            return await self._load_text(path)
        elif suffix in [".html", ".htm"]:
            return await self._load_html(path)
        else:
            # Try to load as text
            return await self._load_text(path)
    
    async def _load_pdf(self, path: Path) -> str:
        """Load content from PDF."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required for PDF support")
        
        # Run PDF extraction in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_pdf_text, path)
    
    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF (sync)."""
        with open(path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    async def _load_text(self, path: Path) -> str:
        """Load content from text file."""
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def _load_html(self, path: Path) -> str:
        """Load content from HTML file."""
        # For now, just load as text
        # In a full implementation, would use BeautifulSoup to extract text
        return await self._load_text(path)
