from __future__ import annotations


class DocxRenderError(ValueError):
    def __init__(self, capability: str, detail: str):
        self.capability = capability
        self.detail = detail
        super().__init__(f"DOCX {capability} rendering failed: {detail}")
