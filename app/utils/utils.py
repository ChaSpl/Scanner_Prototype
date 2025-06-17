# utils.py

def sanitize(text):
    """Convert Unicode characters to safe Latin-1 equivalents for FPDF."""
    if not text:
        return ""
    return (
        text.replace("–", "-")
            .replace("—", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
            .replace("…", "...")
            .replace("•", "-")
            .replace("→", "->")
            .replace("©", "(c)")
            .replace("®", "(R)")
            .replace("™", "(TM)")
            .replace("✓", "v")
    )
