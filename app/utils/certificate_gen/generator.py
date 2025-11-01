from __future__ import annotations

from functools import lru_cache
from html import escape
import re
from pathlib import Path
from typing import Any, Final
from uuid import uuid4

_PLACEHOLDER: Final[str] = "ИМЯ ФАМИЛИЯ"
_PDF_PAGE_STYLE: Final[str] = """
    @page {
        size: 3508px 2480px;
        margin: 0;
    }
    body {
        width: 3508px;
        height: 2480px;
        margin: 0;
        padding: 0;
    }
"""


class CertificateGenerationError(RuntimeError):
    """Raised when certificate creation fails."""


class CertificateGenerator:
    """Generate personalised certificates using the bundled HTML template."""

    def __init__(
        self,
        *,
        output_dir: Path | None = None,
        template_path: Path | None = None,
        placeholder: str = _PLACEHOLDER,
    ) -> None:
        base_dir = Path(__file__).resolve().parent
        self.template_path = template_path or base_dir / "certificate.html"
        self.output_dir = output_dir or base_dir / "output"
        self.placeholder = placeholder

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.template_path.exists():
            raise CertificateGenerationError(
                f"Template not found at {self.template_path.as_posix()}"
            )

        try:
            self._template = self.template_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CertificateGenerationError("Failed to read certificate template") from exc

        self._base_url = str(self.template_path.parent.resolve())
        self._html_cls: type | None = None
        self._css_cls: type | None = None
        self._cached_css: Any | None = None

    def generate(self, full_name: str) -> Path:
        """Render a certificate for the provided name and return the saved path."""
        normalized_name = full_name.strip()
        if not normalized_name:
            raise CertificateGenerationError("Full name must not be empty")
        html_markup = self._template.replace(self.placeholder, escape(normalized_name))
        output_path = self._build_output_path(normalized_name)

        try:
            html_cls, css_cls = self._load_weasyprint()
            if self._cached_css is None:
                self._cached_css = css_cls(string=_PDF_PAGE_STYLE)

            html_cls(string=html_markup, base_url=self._base_url).write_pdf(
                output_path.as_posix(),
                stylesheets=[self._cached_css],
            )
        except CertificateGenerationError:
            raise
        except Exception as exc:  # noqa: BLE001 - preserve original error for logging upstream
            raise CertificateGenerationError("Failed to render certificate PDF") from exc

        return output_path

    def _build_output_path(self, full_name: str) -> Path:
        safe_name = re.sub(r"\s+", "_", full_name, flags=re.UNICODE)
        safe_name = re.sub(r"[^\w\-]", "", safe_name, flags=re.UNICODE)
        if not safe_name:
            safe_name = "certificate"
        return self.output_dir / f"certificate_{safe_name}_{uuid4().hex[:8]}.pdf"

    def _load_weasyprint(self) -> tuple[type, type]:
        if self._html_cls and self._css_cls:
            return self._html_cls, self._css_cls

        try:
            from weasyprint import CSS, HTML
        except ImportError as exc:  # Dependency missing from Python env
            raise CertificateGenerationError(
                "WeasyPrint is not installed. Add 'weasyprint' to your project dependencies."
            ) from exc
        except OSError as exc:  # System dependencies missing (Pango, GDK-PixBuf...)
            raise CertificateGenerationError(
                "WeasyPrint system libraries are missing. Install them as documented at "
                "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation"
            ) from exc

        self._html_cls = HTML
        self._css_cls = CSS
        return HTML, CSS


@lru_cache(maxsize=1)
def get_certificate_generator() -> CertificateGenerator:
    """Return a singleton instance to reuse cached template resources."""
    return CertificateGenerator()
