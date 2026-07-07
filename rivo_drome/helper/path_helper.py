import os
import re
from rivo_drome.model.track_info import TrackInfo

def clean_filename(text: str) -> str:
    if not text:
        return ""
    # Replace characters that are invalid in filesystems with underscores
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", text)
    # Strip leading/trailing whitespace and dots
    cleaned = cleaned.strip(" .")
    return cleaned

def build_structured_path(download_dir: str, track_info: TrackInfo, ext: str) -> str:
    artist = clean_filename(track_info.artist) or "Unknown Artist"
    album = clean_filename(track_info.album) or "Unknown Album"
    title = clean_filename(track_info.title) or "Unknown Title"
    
    # Ensure extension starts with a dot and has no invalid characters
    ext = ext.strip().lstrip(".")
    ext = clean_filename(ext)
    ext = f".{ext}" if ext else ""
    
    if track_info.track_number is not None:
        try:
            track_num_int = int(track_info.track_number)
            filename = f"{track_num_int:02d} - {title}{ext}"
        except (ValueError, TypeError):
            filename = f"{title}{ext}"
    else:
        filename = f"{title}{ext}"
        
    return os.path.join(download_dir, artist, album, filename)
