from .diagnostics import localized_issue_message

__all__ = ["localized_issue_message", "map_preview_result"]


def __getattr__(name: str):
    if name == "map_preview_result":
        from .preview import map_preview_result

        return map_preview_result
    raise AttributeError(name)
