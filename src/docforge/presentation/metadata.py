from docforge.templates.model import get_metadata_binding_descriptor


def cover_binding_label(path: str) -> str:
    return get_metadata_binding_descriptor(path).label
