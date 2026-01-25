"""
Chat utilities - Helper functions extracted from chat.py
"""
import re

# Estado global del workspace
_current_workspace = None


def clean_ansi(text: str) -> str:
    """Elimina códigos de escape ANSI y secuencias de terminal"""
    if not text:
        return ""
    # Códigos ANSI estándar
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    # Secuencias de terminal como [?2004l, [?2004h
    text = re.sub(r'\[\?[0-9]+[a-z]', '', text)
    # Secuencias @[?...
    text = re.sub(r'@\[\?[0-9]+[a-z]:?', '', text)
    # Caracteres de control
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()


def get_workspace() -> str:
    """Obtiene el workspace actual"""
    global _current_workspace
    return _current_workspace


def set_workspace(path: str) -> None:
    """Establece el workspace actual"""
    global _current_workspace
    _current_workspace = path


def truncate_text(text: str, max_length: int = 500) -> str:
    """Trunca texto a una longitud máxima"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_file_size(size_bytes: int) -> str:
    """Formatea tamaño de archivo en formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
