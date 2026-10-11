import os
import json
import glob
from tinytag import TinyTag

# === НАСТРОЙКИ ===
MUSIC_FOLDER = "C:\\Users\\legion\\Music"  # ← ЗАМЕНИ на свою папку
OUTPUT_FILE = "playlist.json"

# === СБОР ПЕСЕН ===
playlist = []

for songpath in glob.glob(os.path.join(MUSIC_FOLDER, "*.mp3")):
    tag = TinyTag.get(songpath, image=False)

    song = {
        "path": songpath,
        "name": tag.title if tag.title else os.path.basename(songpath),
        "artist": tag.artist,
        "duration": tag.duration,
    }

    playlist.append(song)
    print(f"✓ {song['name']}")

# === ЗАПИСЬ В JSON ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(playlist, f, ensure_ascii=False, indent=4)

print(f"\nГотово! {len(playlist)} песен записано в {OUTPUT_FILE}")