
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import chess
import chess.pgn
import chess.engine
from PIL import Image, ImageTk
import os
import sys
import json
import traceback
import shutil
import subprocess
import threading
import urllib.request
import urllib.parse
import io
import time
import winsound
import wave
import math
import random
import struct
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# GameCoach 22 palette — graphite / emerald / amber
GC_ACCENT = "#2FA36B"
GC_ACCENT_HOVER = "#267F56"
GC_AMBER = "#D89B3C"
GC_PANEL = "#171A1F"
GC_PANEL_2 = "#1D2228"
GC_TEXT_MUTED = "#9AA3AD"

APP_NAME = "GameCoach 1.0 • Welcome Edition"
APP_VERSION = "1.0"
APP_PUBLISHER = "GameCoach"

def _user_data_dir():
    base = os.environ.get("LOCALAPPDATA")
    if base:
        path = os.path.join(base, "GameCoach")
    else:
        path = os.path.join(os.path.expanduser("~"), ".gamecoach")
    os.makedirs(path, exist_ok=True)
    return path

APP_DATA_DIR = _user_data_dir()
HISTORY_FILE = os.path.join(APP_DATA_DIR, "gamecoach_history.json")
PROFILE_FILE = os.path.join(APP_DATA_DIR, "gamecoach_profile.json")
TRAINING_FILE = os.path.join(APP_DATA_DIR, "gamecoach_training.json")
LEARNING_FILE = os.path.join(APP_DATA_DIR, "gamecoach_learning.json")
SAVED_PUZZLES_FILE = os.path.join(APP_DATA_DIR, "gamecoach_saved_puzzles.json")
REPERTOIRE_FILE = os.path.join(APP_DATA_DIR, "gamecoach_repertoire.json")
ENDGAME_FILE = os.path.join(APP_DATA_DIR, "gamecoach_endgames.json")
DATABASE_FILE = os.path.join(APP_DATA_DIR, "gamecoach_data.db")
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "gamecoach_settings.json")
PIECES_FOLDER = os.path.join(APP_DATA_DIR, "pieces")
LOG_FILE = os.path.join(APP_DATA_DIR, "gamecoach_error.log")
PIECE_BASE_URL = "https://cdn.jsdelivr.net/gh/oakmac/chessboardjs/website/img/chesspieces/wikipedia/"

def _program_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()

def migrate_legacy_user_files():
    """Move/copy old GameCoach data from the launch folder into AppData once."""
    legacy_names = [
        "gamecoach_history.json","gamecoach_profile.json","gamecoach_training.json",
        "gamecoach_learning.json","gamecoach_saved_puzzles.json",
        "gamecoach_repertoire.json","gamecoach_endgames.json",
        "gamecoach_data.db","gamecoach_settings.json"
    ]
    roots=[]
    for candidate in (os.getcwd(), _program_dir()):
        try:
            ap=os.path.abspath(candidate)
            if ap not in roots:
                roots.append(ap)
        except Exception:
            pass
    for name in legacy_names:
        dst=os.path.join(APP_DATA_DIR,name)
        if os.path.exists(dst):
            continue
        for root_dir in roots:
            old_path=os.path.join(root_dir,name)
            if os.path.isfile(old_path) and os.path.abspath(old_path) != os.path.abspath(dst):
                try:
                    shutil.copy2(old_path,dst)
                    break
                except Exception:
                    pass

def log_unhandled_exception(exc_type, exc_value, exc_tb):
    try:
        with open(LOG_FILE,"a",encoding="utf-8") as f:
            f.write("\n"+"="*72+"\n")
            f.write(datetime.now().isoformat(timespec="seconds")+"\n")
            traceback.print_exception(exc_type,exc_value,exc_tb,file=f)
    except Exception:
        pass

BOARD_SIZE = 520
SQ = BOARD_SIZE / 8
EVAL_BAR_W = 34

LIGHT_SQUARE = "#EEEED2"
DARK_SQUARE = "#769656"
LAST_MOVE_LIGHT = "#F5F682"
LAST_MOVE_DARK = "#BBCB45"
LEGAL_DOT = "#334A3C"
SELECT_BORDER = "#38A7FF"
PLAYED_MOVE_COLOR = "#E74755"
BEST_MOVE_COLOR = "#2ECC71"
BOARD_BORDER = "#24282E"

BOARD_THEMES = {
    "Classic Green": {
        "light": "#EEEED2", "dark": "#769656",
        "last_light": "#F6F669", "last_dark": "#BACA44",
        "legal": "#35533D", "select": "#38A7FF", "border": "#24282E"
    },
    "Warm Brown": {
        "light": "#F0D9B5", "dark": "#B58863",
        "last_light": "#F3E58A", "last_dark": "#D6B95E",
        "legal": "#604C3B", "select": "#4DA3FF", "border": "#30251E"
    },
    "Soft Brown": {
        "light": "#E8D0AA", "dark": "#A87954",
        "last_light": "#E9D66B", "last_dark": "#C1A84E",
        "legal": "#5C4939", "select": "#55A7FF", "border": "#29221D"
    },
    "Ocean Blue": {
        "light": "#D9E4E8", "dark": "#668FA3",
        "last_light": "#E6E982", "last_dark": "#AEBB58",
        "legal": "#345766", "select": "#42B7FF", "border": "#1F3038"
    },
    "Deep Blue": {
        "light": "#C9D6E4", "dark": "#4B6584",
        "last_light": "#D9DB74", "last_dark": "#87974E",
        "legal": "#30455B", "select": "#5EC5FF", "border": "#17202B"
    },
    "Slate": {
        "light": "#D8D9DB", "dark": "#777C83",
        "last_light": "#E4DC80", "last_dark": "#AAA454",
        "legal": "#4B5056", "select": "#50B6FF", "border": "#202327"
    },
    "Tournament": {
        "light": "#E9E2D0", "dark": "#6D8A6B",
        "last_light": "#F0E47C", "last_dark": "#A9B653",
        "legal": "#3F5941", "select": "#3DA9FC", "border": "#252B25"
    },
    "Walnut": {
        "light": "#D7B98E", "dark": "#7A5236",
        "last_light": "#E7D56D", "last_dark": "#AD9142",
        "legal": "#4B3326", "select": "#55B5FF", "border": "#251A14"
    },
    "Coffee": {
        "light": "#D9C3A5", "dark": "#80624A",
        "last_light": "#E4D27A", "last_dark": "#AA9853",
        "legal": "#4C3A2F", "select": "#5DB4FF", "border": "#2B211B"
    },
    "Purple": {
        "light": "#E2D7E8", "dark": "#806B8F",
        "last_light": "#ECE37E", "last_dark": "#B4A95D",
        "legal": "#574660", "select": "#5BC0FF", "border": "#2A2330"
    },
    "Rose": {
        "light": "#F0D9D9", "dark": "#B87878",
        "last_light": "#F0E17C", "last_dark": "#D0B65B",
        "legal": "#704949", "select": "#4EB5FF", "border": "#382424"
    },
    "Mint": {
        "light": "#DDF0E3", "dark": "#6E9D84",
        "last_light": "#EBE579", "last_dark": "#B5BE58",
        "legal": "#426352", "select": "#43B7FF", "border": "#203229"
    },
    "Sand": {
        "light": "#F1E2BD", "dark": "#C19A6B",
        "last_light": "#F2DC73", "last_dark": "#D1AD55",
        "legal": "#765C3F", "select": "#48ACFF", "border": "#3A2D20"
    },
    "Night": {
        "light": "#8A929B", "dark": "#3D4650",
        "last_light": "#B5B866", "last_dark": "#737B42",
        "legal": "#252C33", "select": "#56C3FF", "border": "#11161B"
    },
    "Monochrome": {
        "light": "#E4E4E4", "dark": "#8A8A8A",
        "last_light": "#D7D790", "last_dark": "#A7A75D",
        "legal": "#555555", "select": "#2F9FE8", "border": "#222222"
    },
    "Forest": {"light":"#D8E2C4","dark":"#58734A","last_light":"#E7DB72","last_dark":"#9E9D43","legal":"#34472E","select":"#E6B84A","border":"#172016"},
    "Emerald": {"light":"#D9E7D8","dark":"#3F8067","last_light":"#E8DF76","last_dark":"#8FA84E","legal":"#285443","select":"#F0B94A","border":"#17352B"},
    "Olive": {"light":"#E5E1BD","dark":"#7B8150","last_light":"#F0D96B","last_dark":"#A79A46","legal":"#4D5133","select":"#E0A83B","border":"#292B1D"},
    "Bamboo": {"light":"#E7D8AE","dark":"#8C9A62","last_light":"#F2DC70","last_dark":"#B5A64E","legal":"#56613C","select":"#D88935","border":"#303722"},
    "Ivory": {"light":"#F4EBD7","dark":"#A99C83","last_light":"#F2D875","last_dark":"#C0A85B","legal":"#6C6354","select":"#B87936","border":"#38332C"},
    "Terracotta": {"light":"#EBCFB4","dark":"#A65F46","last_light":"#F0D272","last_dark":"#C28D4C","legal":"#653A2D","select":"#E6B04A","border":"#3B211A"},
    "Mahogany": {"light":"#D7B99C","dark":"#6F3F35","last_light":"#E7CF69","last_dark":"#A47D43","legal":"#472821","select":"#D8A33B","border":"#241513"},
    "Cherry": {"light":"#E6C7B8","dark":"#8C4D52","last_light":"#EDD16E","last_dark":"#B7844B","legal":"#593136","select":"#E1AA3C","border":"#2D181B"},
    "Lavender": {"light":"#E8E0EC","dark":"#8B789A","last_light":"#EEE37A","last_dark":"#B4A75C","legal":"#594D63","select":"#D4A84B","border":"#2C2631"},
    "Plum": {"light":"#DCCFD9","dark":"#704F68","last_light":"#E6D66C","last_dark":"#9E844B","legal":"#493343","select":"#D7A13A","border":"#241A22"},
    "Arctic": {"light":"#E8EEF0","dark":"#82989C","last_light":"#E9DF79","last_dark":"#ABB45A","legal":"#536467","select":"#D6A83F","border":"#273033"},
    "Steel": {"light":"#CDD1D3","dark":"#626B70","last_light":"#DBD16E","last_dark":"#92994E","legal":"#3D4448","select":"#D5A23A","border":"#1F2427"},
    "Charcoal": {"light":"#AEB3AF","dark":"#424A45","last_light":"#C8C66B","last_dark":"#737A48","legal":"#29302C","select":"#D8A642","border":"#111512"},
    "Amber": {"light":"#F0D8A8","dark":"#B47A3C","last_light":"#F3E079","last_dark":"#D0A34E","legal":"#704A27","select":"#7D5B2A","border":"#3B2715"},
    "Retro": {"light":"#E6D6A8","dark":"#6F7B5B","last_light":"#EAD66D","last_dark":"#9EA04B","legal":"#454D39","select":"#C77B36","border":"#252B20"},
}

PIECE_STYLES = [
    "Wikipedia", "Classic", "Modern", "Tournament",
    "Elegant", "Bold", "Minimal", "Sharp",
    "Compact", "Grand", "Soft", "Crisp",
    "Shadow", "Ink", "Lightweight", "Heavy"
]


def current_board_theme():
    name = app_settings.get("board_theme", "Classic Green")
    return BOARD_THEMES.get(name, BOARD_THEMES["Classic Green"])


stockfish_path = ""
pgn_path = ""
player_color_global = chess.WHITE

piece_images = {}
game_moves = []
analysed_moves = []
current_ply_index = -1

animation_running = False
autoplay_running = False
autoplay_job = None

multi_game_reports = []
training_positions = []
saved_training_positions = []
training_index = 0
training_active = False
training_selected_square = None
training_dragging = False
training_drag_id = None
training_drag_from = None
training_drag_board = None
training_stats = {}
learning_profile = {
    "xp": 0,
    "streak": 0,
    "last_training_day": "",
    "daily_correct": 0,
    "daily_wrong": 0,
    "xp_awards": {}
}

training_session_correct = 0
training_session_wrong = 0
training_mode_only_due = False

app_settings = {
    "engine_depth_single": 10,
    "engine_depth_profile": 8,
    "sound": True,
    "animation_ms": 420,
    "recent_games": 20,
    "stockfish_path": "",
    "text_mode": "Обычный",
    "board_theme": "Classic Green",
    "piece_style": "Wikipedia"
}

visual_line_moves = []
visual_line_index = 0
visual_line_board = None

PIECE_FILES = [
    "wK", "wQ", "wR", "wB", "wN", "wP",
    "bK", "bQ", "bR", "bB", "bN", "bP"
]

PIECE_MAP = {
    "P": "wP", "N": "wN", "B": "wB", "R": "wR", "Q": "wQ", "K": "wK",
    "p": "bP", "n": "bN", "bB": "bB"
}

# correct map overwrite
PIECE_MAP = {
    "P": "wP", "N": "wN", "B": "wB", "R": "wR", "Q": "wQ", "K": "wK",
    "p": "bP", "n": "bN", "b": "bB", "r": "bR", "q": "bQ", "k": "bK"
}

UNICODE_PIECES = {
    "K":"♔","Q":"♕","R":"♖","B":"♗","N":"♘","P":"♙",
    "k":"♚","q":"♛","r":"♜","b":"♝","n":"♞","p":"♟",
}

OPENING_FAMILIES = [
    (["e4", "c5"], "Sicilian Defense"),
    (["e4", "e5", "Nf3", "Nc6", "Bb5"], "Ruy Lopez"),
    (["e4", "e5", "Nf3", "Nc6", "Bc4"], "Italian Game"),
    (["e4", "e5", "Nf3", "Nf6"], "Petrov's Defense"),
    (["e4", "e6"], "French Defense"),
    (["e4", "c6"], "Caro-Kann Defense"),
    (["e4", "d5"], "Scandinavian Defense"),
    (["d4", "d5", "c4"], "Queen's Gambit"),
    (["d4", "Nf6", "c4", "g6"], "King's Indian Defense"),
    (["d4", "Nf6", "c4", "e6"], "Indian Game"),
    (["d4", "d5"], "Queen's Pawn Game"),
    (["Nf3"], "Réti Opening"),
    (["c4"], "English Opening"),
]


# ============================================================
# UTILITIES
# ============================================================

def _sound_folder():
    folder = os.path.join(os.path.expanduser("~"), ".gamecoach", "sounds")
    os.makedirs(folder, exist_ok=True)
    return folder


def _make_click_wave(path, kind):
    """Create short local WAV effects once. No external audio files required."""
    sample_rate = 44100

    presets = {
        "move":      (0.105, 1350, 0.42),
        "capture":   (0.145, 820, 0.62),
        "check":     (0.180, 1650, 0.58),
        "castle":    (0.190, 1050, 0.55),
        "promotion": (0.260, 1450, 0.58),
        "correct":   (0.240, 1250, 0.50),
        "wrong":     (0.190, 430, 0.58),
    }
    duration, freq, volume = presets.get(kind, presets["move"])
    n = int(sample_rate * duration)

    frames = bytearray()
    for i in range(n):
        t = i / sample_rate
        x = i / max(1, n - 1)

        # Strong attack and quick decay: closer to a board/app click than a sine beep.
        envelope = (1.0 - x) ** 3
        attack = min(1.0, i / max(1, int(sample_rate * 0.004)))
        envelope *= attack

        # Mix a couple of frequencies plus a tiny noise transient.
        signal = (
            0.72 * math.sin(2 * math.pi * freq * t) +
            0.22 * math.sin(2 * math.pi * (freq * 1.73) * t)
        )

        if i < int(sample_rate * 0.018):
            signal += random.uniform(-0.55, 0.55) * (1 - i / (sample_rate * 0.018))

        # Give different effects a little character.
        if kind == "capture":
            signal += 0.25 * math.sin(2 * math.pi * 310 * t)
        elif kind == "check":
            signal += 0.20 * math.sin(2 * math.pi * 2100 * t)
        elif kind == "castle":
            signal += 0.18 * math.sin(2 * math.pi * 620 * t)
        elif kind == "promotion":
            signal += 0.18 * math.sin(2 * math.pi * (freq + 500 * x) * t)
        elif kind == "correct":
            signal += 0.20 * math.sin(2 * math.pi * (freq + 650 * x) * t)

        value = max(-1.0, min(1.0, signal * envelope * volume))
        frames.extend(struct.pack("<h", int(value * 32767)))

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)


def ensure_sound_files():
    folder = _sound_folder()
    result = {}
    for kind in ("move", "capture", "check", "castle", "promotion", "correct", "wrong"):
        path = os.path.join(folder, f"{kind}.wav")
        if not os.path.exists(path):
            try:
                _make_click_wave(path, kind)
            except Exception:
                pass
        if os.path.exists(path):
            result[kind] = path
    return result


def safe_beep(kind):
    if not app_settings.get("sound", True):
        return

    def worker():
        try:
            sounds = ensure_sound_files()
            path = sounds.get(kind) or sounds.get("move")
            if path and os.path.exists(path):
                # Filename-based WAV playback is more reliable than Beep on many PCs.
                winsound.PlaySound(
                    path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                )
                return
        except Exception:
            pass

        # Fallback if WAV playback is unavailable.
        try:
            fallback = {
                "move": 700,
                "capture": 520,
                "check": 1050,
                "castle": 820,
                "promotion": 1200,
                "correct": 980,
                "wrong": 360,
            }
            winsound.Beep(fallback.get(kind, 700), 120)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()


def test_gamecoach_sound():
    old = app_settings.get("sound", True)
    app_settings["sound"] = True
    safe_beep("move")
    root.after(230, lambda: safe_beep("capture"))
    root.after(480, lambda: safe_beep("check"))
    root.after(800, lambda: app_settings.__setitem__("sound", old))


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def ensure_piece_folder():
    os.makedirs(PIECES_FOLDER, exist_ok=True)


def _piece_file_ok(path):
    try:
        return os.path.exists(path) and os.path.getsize(path) > 500
    except Exception:
        return False


def download_piece_images():
    """Download any missing piece PNGs individually.

    GameCoach can still draw Unicode pieces if the internet/CDN is unavailable.
    """
    ensure_piece_folder()
    all_ok=True
    for name in PIECE_FILES:
        path=os.path.join(PIECES_FOLDER,name+".png")
        if _piece_file_ok(path):
            continue
        try:
            req=urllib.request.Request(
                PIECE_BASE_URL+name+".png",
                headers={"User-Agent":"GameCoach/30.1"}
            )
            with urllib.request.urlopen(req,timeout=10) as response:
                data=response.read()
            if len(data) < 500:
                raise ValueError("piece image is unexpectedly small")
            tmp=path+".tmp"
            with open(tmp,"wb") as f:
                f.write(data)
            os.replace(tmp,path)
        except Exception:
            all_ok=False
            try:
                tmp=path+".tmp"
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
    return all_ok



def _styled_piece_image(image, style_name):
    image = image.convert("RGBA")

    if style_name == "Wikipedia":
        return image

    # All variants are derived locally from the open base set.
    if style_name == "Classic":
        return image

    if style_name == "Modern":
        # Slightly cleaner/smaller silhouette.
        canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
        resized = image.resize(
            (max(1, int(image.width * .94)), max(1, int(image.height * .94))),
            Image.Resampling.LANCZOS
        )
        canvas.alpha_composite(resized, ((image.width-resized.width)//2, (image.height-resized.height)//2))
        return canvas

    if style_name == "Tournament":
        # Slightly larger pieces.
        canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
        crop = image.getbbox()
        if crop:
            part = image.crop(crop)
            part.thumbnail((int(image.width*.98), int(image.height*.98)), Image.Resampling.LANCZOS)
            canvas.alpha_composite(part, ((image.width-part.width)//2, (image.height-part.height)//2))
            return canvas
        return image

    if style_name == "Elegant":
        # Softer alpha edges.
        alpha = image.getchannel("A")
        alpha = alpha.point(lambda a: int(a * .92))
        image.putalpha(alpha)
        return image

    if style_name == "Bold":
        # Make opaque pixels a touch stronger by expanding alpha locally.
        alpha = image.getchannel("A")
        try:
            from PIL import ImageFilter
            alpha = alpha.filter(ImageFilter.MaxFilter(3))
            image.putalpha(alpha)
        except Exception:
            pass
        return image

    if style_name == "Minimal":
        # Smaller, airy set.
        canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
        resized = image.resize(
            (max(1, int(image.width*.86)), max(1, int(image.height*.86))),
            Image.Resampling.LANCZOS
        )
        canvas.alpha_composite(resized, ((image.width-resized.width)//2, (image.height-resized.height)//2))
        return canvas

    if style_name == "Sharp":
        try:
            from PIL import ImageEnhance
            return ImageEnhance.Sharpness(image).enhance(1.8)
        except Exception:
            return image

    if style_name in ("Compact", "Grand", "Lightweight", "Heavy"):
        scale={"Compact":.80,"Grand":1.00,"Lightweight":.88,"Heavy":.97}[style_name]
        canvas=Image.new("RGBA",image.size,(0,0,0,0))
        box=image.getbbox()
        part=image.crop(box) if box else image
        maxw=max(1,int(image.width*scale)); maxh=max(1,int(image.height*scale))
        part.thumbnail((maxw,maxh),Image.Resampling.LANCZOS)
        if style_name=="Heavy":
            try:
                from PIL import ImageFilter
                a=part.getchannel("A").filter(ImageFilter.MaxFilter(5));part.putalpha(a)
            except Exception: pass
        canvas.alpha_composite(part,((image.width-part.width)//2,(image.height-part.height)//2))
        return canvas

    if style_name in ("Soft", "Crisp"):
        try:
            from PIL import ImageEnhance, ImageFilter
            if style_name=="Soft":
                return image.filter(ImageFilter.GaussianBlur(.35))
            return ImageEnhance.Sharpness(ImageEnhance.Contrast(image).enhance(1.08)).enhance(2.4)
        except Exception:return image

    if style_name=="Shadow":
        try:
            from PIL import ImageFilter
            alpha=image.getchannel("A")
            shadow=Image.new("RGBA",image.size,(0,0,0,0))
            sh=Image.new("RGBA",image.size,(0,0,0,0));sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(2)))
            shadow.alpha_composite(sh,(2,3))
            shadow.alpha_composite(image)
            return shadow
        except Exception:return image

    if style_name=="Ink":
        try:
            from PIL import ImageEnhance
            return ImageEnhance.Contrast(ImageEnhance.Sharpness(image).enhance(2.0)).enhance(1.22)
        except Exception:return image

    return image


def load_piece_images():
    global piece_images
    piece_images = {}
    size = int(SQ * 0.92)
    style_name = app_settings.get("piece_style", "Wikipedia")

    for symbol, filename in PIECE_MAP.items():
        path = os.path.join(PIECES_FOLDER, filename + ".png")
        if not _piece_file_ok(path):
            continue
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((size, size), Image.Resampling.LANCZOS)

            cell = Image.new("RGBA", (int(SQ), int(SQ)), (0, 0, 0, 0))
            x = (int(SQ) - image.width) // 2
            y = (int(SQ) - image.height) // 2
            cell.alpha_composite(image, (x, y))
            cell = _styled_piece_image(cell, style_name)
            piece_images[symbol] = ImageTk.PhotoImage(cell)
        except Exception:
            # A broken PNG should never make the board lose all pieces.
            continue



def apply_visual_theme():
    load_piece_images()
    save_app_settings()
    try:
        if analysed_moves or game_moves:
            show_current_position()
        else:
            draw_board(chess.Board())
    except Exception:
        pass


# ============================================================
# CHESS HELPERS
# ============================================================

def get_phase(board):
    if board.fullmove_number <= 10:
        return "Дебют"
    if len(board.piece_map()) <= 12:
        return "Эндшпиль"
    return "Миттельшпиль"


def pov_score_cp(info, color):
    score = info["score"].pov(color)
    mate = score.mate()
    if mate is not None:
        return 100000 if mate > 0 else -100000
    value = score.score()
    return value if value is not None else 0


def score_to_text(cp):
    if cp >= 90000:
        return "M+"
    if cp <= -90000:
        return "M-"
    return f"{cp / 100:+.2f}"


def get_quality(loss, move, best_move):
    if best_move is not None and move == best_move:
        return "⭐ ЛУЧШИЙ", "best"
    if loss >= 300:
        return "🔴 ЗЕВОК", "blunder"
    if loss >= 150:
        return "🟠 ОШИБКА", "mistake"
    if loss >= 70:
        return "🟡 НЕТОЧНОСТЬ", "inaccuracy"
    if loss >= 30:
        return "⚪ ДОПУСТИМЫЙ", "okay"
    if loss >= 10:
        return "🟢 ХОРОШИЙ", "good"
    return "💎 ОТЛИЧНЫЙ", "excellent"


def pv_to_san(board, pv, max_plies=8):
    temp = board.copy()
    out = []
    for move in pv[:max_plies]:
        if move not in temp.legal_moves:
            break
        out.append(temp.san(move))
        temp.push(move)
    return " ".join(out) if out else "—"


def detect_opening_from_sans(sans):
    for sequence, name in sorted(OPENING_FAMILIES, key=lambda x: len(x[0]), reverse=True):
        if len(sans) >= len(sequence) and sans[:len(sequence)] == sequence:
            return name
    return "Неопределённый дебют"


def detect_tactical_motif(before, move, after_pv):
    """Small, explainable heuristic layer. It does not replace Stockfish."""
    # Some callers pass one chess.Move instead of a PV list.
    # Normalize here so the detector is safe everywhere.
    if isinstance(after_pv, chess.Move):
        after_pv = [after_pv]
    elif after_pv is None:
        after_pv = []
    elif not isinstance(after_pv, (list, tuple)):
        try:
            after_pv = list(after_pv)
        except Exception:
            after_pv = []

    after = before.copy()
    moving_piece = before.piece_at(move.from_square)
    after.push(move)

    notes = []
    highlight = []

    # Check / capture / hanging moved piece
    if after.is_check():
        notes.append("Ход даёт шах.")
        highlight.append(move.to_square)

    if before.is_capture(move):
        notes.append("Произошёл размен или взятие — проверь материальный итог всей последовательности.")

    moved_after = after.piece_at(move.to_square)
    if moved_after:
        attackers = list(after.attackers(not moved_after.color, move.to_square))
        defenders = list(after.attackers(moved_after.color, move.to_square))
        if attackers and not defenders:
            notes.append(
                f"Фигура на {chess.square_name(move.to_square)} после хода остаётся под ударом без прямой защиты."
            )
            highlight.append(move.to_square)

    # Opponent's first engine reply: detect capture/check/fork-like attack.
    if after_pv:
        reply = after_pv[0]
        if reply in after.legal_moves:
            reply_piece = after.piece_at(reply.from_square)
            reply_is_capture = after.is_capture(reply)
            temp = after.copy()
            temp.push(reply)

            if temp.is_check():
                notes.append(
                    f"Сильный ответ соперника {after.san(reply)} даёт шах — это форсированный темп."
                )
                highlight.extend([reply.from_square, reply.to_square])

            if reply_is_capture:
                notes.append(
                    f"Соперник может сразу сыграть {after.san(reply)} и забрать материал."
                )
                highlight.extend([reply.from_square, reply.to_square])

            # Fork heuristic: moved piece attacks 2+ valuable enemy pieces.
            if reply_piece:
                attacked = []
                for sq, pc in temp.piece_map().items():
                    if pc.color != reply_piece.color and pc.piece_type != chess.PAWN:
                        if temp.is_attacked_by(reply_piece.color, sq):
                            attacked.append((sq, pc))
                if len(attacked) >= 2:
                    names = {
                        chess.KNIGHT: "конь", chess.BISHOP: "слон",
                        chess.ROOK: "ладья", chess.QUEEN: "ферзь",
                        chess.KING: "король"
                    }
                    targets = ", ".join(
                        f"{names.get(pc.piece_type, 'фигура')} {chess.square_name(sq)}"
                        for sq, pc in attacked[:3]
                    )
                    notes.append(
                        f"Похоже на двойной удар: после {after.san(reply)} фигура одновременно давит на {targets}."
                    )
                    highlight.extend([sq for sq, _ in attacked[:3]])

    if not notes:
        notes.append(
            "Явный простой тактический мотив эвристика не нашла. Смотри линию Stockfish и сравни активность фигур."
        )

    return notes, list(dict.fromkeys(highlight))


def material_score(board, color):
    values = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
    }
    return sum(
        values[p.piece_type]
        for p in board.piece_map().values()
        if p.color == color
    )


def count_hanging_pieces(board, color):
    values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100
    }
    hanging = []
    for sq, piece in board.piece_map().items():
        if piece.color != color or piece.piece_type == chess.KING:
            continue
        attackers = list(board.attackers(not color, sq))
        defenders = list(board.attackers(color, sq))
        if attackers and not defenders:
            hanging.append((sq, piece, values[piece.piece_type]))
    return hanging


def king_safety_notes(board, color):
    king_sq = board.king(color)
    if king_sq is None:
        return []
    notes = []
    rank = chess.square_rank(king_sq)
    file = chess.square_file(king_sq)
    if color == chess.WHITE and rank >= 1:
        notes.append("Белый король остаётся далеко от первой горизонтали.")
    if color == chess.BLACK and rank <= 6:
        notes.append("Чёрный король остаётся далеко от восьмой горизонтали.")
    nearby_enemy_attacks = 0
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            nf, nr = file + df, rank + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                sq = chess.square(nf, nr)
                if board.is_attacked_by(not color, sq):
                    nearby_enemy_attacks += 1
    if nearby_enemy_attacks >= 3:
        notes.append("Вокруг короля несколько полей контролируются фигурами соперника.")
    return notes


def explain_best_move_difference(before, played, best_move, mover_color):
    """Human-readable structural comparison; heuristic, not a replacement for engine eval."""
    if best_move is None or played == best_move:
        return []

    notes = []
    played_board = before.copy()
    best_board = before.copy()

    try:
        played_san = before.san(played)
        best_san = before.san(best_move)
    except Exception:
        played_san, best_san = str(played), str(best_move)

    played_capture = before.is_capture(played)
    best_capture = before.is_capture(best_move)
    played_check = before.gives_check(played)
    best_check = before.gives_check(best_move)

    played_board.push(played)
    best_board.push(best_move)

    if best_check and not played_check:
        notes.append(f"{best_san} играет с темпом: соперник обязан отвечать на шах.")
    if best_capture and not played_capture:
        notes.append(f"{best_san} сразу использует возможность взятия.")
    if before.is_castling(best_move) and not before.is_castling(played):
        notes.append(f"{best_san} улучшает безопасность короля и одновременно активирует ладью.")

    hp = count_hanging_pieces(played_board, mover_color)
    hb = count_hanging_pieces(best_board, mover_color)
    if len(hp) > len(hb):
        sq, pc, val = sorted(hp, key=lambda x: x[2], reverse=True)[0]
        names = {
            chess.PAWN: "пешка", chess.KNIGHT: "конь", chess.BISHOP: "слон",
            chess.ROOK: "ладья", chess.QUEEN: "ферзь"
        }
        notes.append(
            f"После {played_san} у тебя появляется уязвимая фигура: "
            f"{names.get(pc.piece_type, 'фигура')} на {chess.square_name(sq)}. "
            f"После {best_san} таких прямых проблем меньше."
        )

    played_king = king_safety_notes(played_board, mover_color)
    best_king = king_safety_notes(best_board, mover_color)
    if played_king and len(best_king) < len(played_king):
        notes.append(f"{best_san} оставляет короля в более спокойной позиции.")

    # Development heuristic in opening.
    if get_phase(before) == "Дебют":
        best_piece = before.piece_at(best_move.from_square)
        played_piece = before.piece_at(played.from_square)
        if best_piece and best_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            start_squares = (
                chess.B1, chess.G1, chess.C1, chess.F1,
                chess.B8, chess.G8, chess.C8, chess.F8
            )
            if best_move.from_square in start_squares:
                notes.append(f"{best_san} развивает новую фигуру — это особенно ценно в дебюте.")
        if played_piece and played_piece.piece_type == chess.QUEEN and before.fullmove_number <= 8:
            notes.append(f"{played_san} рано двигает ферзя; соперник может получить темп, атакуя его.")

    if not notes:
        notes.append(
            f"Главное преимущество {best_san} видно в продолжении Stockfish: "
            "он лучше сохраняет оценку позиции. Сравни первые ответы соперника после двух ходов."
        )

    return notes[:4]


def explain_move(before, move, best_move, loss, after_pv, mover_color):
    san = before.san(move)
    side = "Белые" if mover_color == chess.WHITE else "Чёрные"
    phase = get_phase(before)
    moved_piece = before.piece_at(move.from_square)

    names = {
        chess.PAWN: "пешка",
        chess.KNIGHT: "конь",
        chess.BISHOP: "слон",
        chess.ROOK: "ладья",
        chess.QUEEN: "ферзь",
        chess.KING: "король"
    }
    piece_word = names.get(moved_piece.piece_type, "фигура") if moved_piece else "фигура"

    after = before.copy()
    is_capture = before.is_capture(move)
    is_castle = before.is_castling(move)
    after.push(move)

    blocks = []

    # Compact headline
    blocks.append(
        f"ХОД\n"
        f"{side}:  {san}\n"
        f"{piece_word.capitalize()} • {phase}"
    )

    # Human-friendly idea
    idea = []
    if is_castle:
        idea.append("Ты спрятал короля и подключил ладью — полезная практическая идея.")
    if is_capture:
        idea.append("Это взятие. После него особенно важно проверить ответное взятие и контратаку.")
    if after.is_check():
        idea.append("Ход даёт шах, поэтому соперник обязан сразу реагировать.")
    if phase == "Дебют" and moved_piece:
        if moved_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            idea.append("Фигура выходит в игру и помогает развитию.")
        elif moved_piece.piece_type == chess.QUEEN and before.fullmove_number <= 7:
            idea.append("Ферзь выходит рано. Соперник может выиграть темп, атакуя его развивающейся фигурой.")
    if not idea:
        idea.append("После хода проверь ответ соперника: шахи, взятия и прямые угрозы.")

    blocks.append("💡 ИДЕЯ\n" + "\n".join(idea))

    motif_notes, _ = detect_tactical_motif(before, move, after_pv)
    blocks.append("🔎 ЧТО ВАЖНО ЗАМЕТИТЬ\n" + "\n".join("• " + x for x in motif_notes))

    # Verdict card
    if loss < 10:
        verdict = "Очень точно"
        detail = "Оценка позиции почти не изменилась."
    elif loss < 30:
        verdict = "Хороший ход"
        detail = "Есть более точный вариант, но разница небольшая."
    elif loss < 70:
        verdict = "Можно точнее"
        detail = "Позиция остаётся играбельной, но лучший ход был сильнее."
    elif loss < 150:
        verdict = "Неточность"
        detail = "После этого хода сопернику становится немного легче."
    elif loss < 300:
        verdict = "Ошибка"
        detail = "Позиция заметно ухудшается. Здесь стоило потратить больше времени на расчёт."
    else:
        verdict = "Зевок"
        detail = "Позиция резко ухудшается. Эту позицию стоит обязательно повторить в тренировке."

    blocks.append(
        f"📊 ВЕРДИКТ\n"
        f"{verdict}\n"
        f"{detail}"
    )

    # Best move comparison
    if best_move is not None:
        best_san = before.san(best_move)
        if move == best_move:
            comparison = (
                f"✓ {san} — первый выбор Stockfish.\n"
                "Ты нашёл сильнейшее продолжение в этой позиции."
            )
        else:
            comparison = (
                f"Твой ход     {san}\n"
                f"Лучше        {best_san}\n"
                f"Разница      ≈ {loss/100:.2f}"
            )
        blocks.append("⭐ СРАВНЕНИЕ\n" + comparison)

        if move != best_move:
            difference_notes = explain_best_move_difference(before, move, best_move, mover_color)
            blocks.append(
                "🧩 ПОЧЕМУ ЛУЧШИЙ ХОД СИЛЬНЕЕ\n" +
                "\n".join("• " + note for note in difference_notes)
            )

    # Opponent response
    if after_pv:
        try:
            reply = after.san(after_pv[0]) if after_pv[0] in after.legal_moves else str(after_pv[0])
        except Exception:
            reply = str(after_pv[0])

        line = pv_to_san(after, after_pv, 6)
        blocks.append(
            "⚔ ОТВЕТ СОПЕРНИКА\n"
            f"Сильный ответ:  {reply}\n\n"
            f"{line}\n\n"
            "Смотри прежде всего на идею первого ответа, а не пытайся запомнить всю линию."
        )

    # Phase-specific checklist
    if phase == "Дебют":
        plan = (
            "□ Король в безопасности?\n"
            "□ Лёгкие фигуры развиты?\n"
            "□ Центр под контролем?\n"
            "□ Не двигаю одну фигуру без необходимости?"
        )
    elif phase == "Миттельшпиль":
        plan = (
            "□ Есть шах?\n"
            "□ Есть выгодное взятие?\n"
            "□ Что угрожает соперник?\n"
            "□ Какая моя фигура играет хуже остальных?"
        )
    else:
        plan = (
            "□ Можно активизировать короля?\n"
            "□ Есть проходная пешка?\n"
            "□ Выгоден ли размен?\n"
            "□ Что останется после размена?"
        )

    blocks.append("🧭 ПЕРЕД СЛЕДУЮЩИМ ХОДОМ\n" + plan)

    if loss >= 70 and best_move is not None and move != best_move:
        blocks.append(
            "🎓 ПОПРОБУЙ ЕЩЁ РАЗ\n"
            "Вернись на один ход назад и найди лучший вариант сам.\n\n"
            "Подсказка: сначала проверь шахи → взятия → угрозы."
        )

    return "\n\n━━━━━━━━━━━━━━━━━━━━\n\n".join(blocks)

# ============================================================
# BOARD
# ============================================================

def square_to_position(square, flipped=False):
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    return (7 - file, rank) if flipped else (file, 7 - rank)


def square_to_canvas(square, flipped=False):
    col, row = square_to_position(square, flipped)
    return col * SQ + SQ / 2, row * SQ + SQ / 2


def canvas_to_square(x, y, flipped=False):
    col = int(x // SQ)
    row = int(y // SQ)
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    if flipped:
        file = 7 - col
        rank = row
    else:
        file = col
        rank = 7 - row
    return chess.square(file, rank)


def draw_arrow(move, color, flipped=False, width=7):
    if move is None:
        return

    x1, y1 = square_to_canvas(move.from_square, flipped)
    x2, y2 = square_to_canvas(move.to_square, flipped)

    dx = x2 - x1
    dy = y2 - y1
    dist = max(1, (dx * dx + dy * dy) ** 0.5)

    x1 += dx / dist * 8
    y1 += dy / dist * 8
    x2 -= dx / dist * 22
    y2 -= dy / dist * 22

    board_canvas.create_line(
        x1, y1, x2, y2,
        fill=color, width=width,
        arrow=tk.LAST,
        arrowshape=(20, 24, 10),
        capstyle=tk.ROUND,
        smooth=True
    )


def draw_board(board, last_move=None, best_move=None, hidden_square=None,
               selected_square=None, legal_squares=None, extra_arrows=None):
    board_canvas.delete("all")
    flipped = player_color_global == chess.BLACK
    legal_squares = set(legal_squares or [])

    for row in range(8):
        for col in range(8):
            if flipped:
                file = 7 - col
                rank = row
            else:
                file = col
                rank = 7 - row

            square = chess.square(file, rank)
            light = (file + rank) % 2 == 1
            theme = current_board_theme()
            color = theme["light"] if light else theme["dark"]

            if last_move is not None and square in (last_move.from_square, last_move.to_square):
                color = theme["last_light"] if light else theme["last_dark"]

            x1, y1 = col * SQ, row * SQ
            x2, y2 = x1 + SQ, y1 + SQ
            board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

            if selected_square == square:
                board_canvas.create_rectangle(
                    x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                    outline=current_board_theme()["select"], width=5
                )

            if square in legal_squares:
                cx, cy = x1 + SQ / 2, y1 + SQ / 2
                if board.piece_at(square):
                    board_canvas.create_oval(
                        cx-25, cy-25, cx+25, cy+25,
                        outline=current_board_theme()["legal"], width=5
                    )
                else:
                    board_canvas.create_oval(
                        cx-8, cy-8, cx+8, cy+8,
                        fill=current_board_theme()["legal"], outline=""
                    )

            coord_color = current_board_theme()["dark"] if light else current_board_theme()["light"]
            if col == 0:
                board_canvas.create_text(
                    x1 + 5, y1 + 4, text=str(rank + 1),
                    anchor="nw", fill=coord_color,
                    font=("Segoe UI", 10, "bold")
                )
            if row == 7:
                board_canvas.create_text(
                    x2 - 5, y2 - 4, text=chr(ord("a") + file),
                    anchor="se", fill=coord_color,
                    font=("Segoe UI", 10, "bold")
                )

    if best_move is not None:
        draw_arrow(best_move, BEST_MOVE_COLOR, flipped, 8)

    for arrow_data in (extra_arrows or []):
        try:
            move, color, width = arrow_data
            draw_arrow(move, color, flipped, width)
        except Exception:
            pass

    for square, piece in board.piece_map().items():
        if square == hidden_square:
            continue
        col, row = square_to_position(square, flipped)
        x = col * SQ + SQ / 2
        y = row * SQ + SQ / 2
        img = piece_images.get(piece.symbol())
        if img:
            board_canvas.create_image(x, y, image=img)
        else:
            # Guaranteed fallback: the review board must never be empty just
            # because PNG assets are missing or the CDN was unavailable.
            glyph = UNICODE_PIECES.get(piece.symbol(), piece.symbol())
            board_canvas.create_text(
                x, y, text=glyph,
                font=("Segoe UI Symbol", int(SQ * 0.72), "normal"),
                fill="#F4F4F4" if piece.color == chess.WHITE else "#171717"
            )

    board_canvas.create_rectangle(
        1, 1, BOARD_SIZE - 1, BOARD_SIZE - 1,
        outline=current_board_theme()["border"], width=2
    )


eval_bar_current_cp = 0.0
eval_bar_job = None


def _paint_eval_bar(cp):
    eval_canvas.delete("all")
    h = BOARD_SIZE

    if cp >= 90000:
        white_ratio = 1.0
    elif cp <= -90000:
        white_ratio = 0.0
    else:
        # Softer nonlinear-looking range around equality.
        clipped = max(-1000, min(1000, cp))
        white_ratio = 0.5 + clipped / 2000

    black_h = h * (1 - white_ratio)
    eval_canvas.create_rectangle(
        0, 0, EVAL_BAR_W, black_h, fill="#171717", outline=""
    )
    eval_canvas.create_rectangle(
        0, black_h, EVAL_BAR_W, h, fill="#F2F2F2", outline=""
    )

    text = score_to_text(int(cp))
    if white_ratio >= 0.55:
        y, color = h - 17, "#111111"
    else:
        y, color = 17, "#FFFFFF"

    eval_canvas.create_text(
        EVAL_BAR_W / 2, y, text=text,
        fill=color, font=("Segoe UI", 9, "bold")
    )


def draw_eval_bar(cp, animate=True):
    """Animate the evaluation instead of jumping instantly."""
    global eval_bar_current_cp, eval_bar_job

    try:
        target = float(cp)
    except Exception:
        target = 0.0

    if not animate:
        eval_bar_current_cp = target
        _paint_eval_bar(target)
        return

    if eval_bar_job is not None:
        try:
            root.after_cancel(eval_bar_job)
        except Exception:
            pass
        eval_bar_job = None

    start_cp = float(eval_bar_current_cp)
    steps = 18
    frame_ms = 18

    def frame(i=0):
        global eval_bar_current_cp, eval_bar_job
        t = min(1.0, i / steps)
        eased = 3 * t * t - 2 * t * t * t
        value = start_cp + (target - start_cp) * eased
        eval_bar_current_cp = value
        _paint_eval_bar(value)

        if i < steps:
            eval_bar_job = root.after(frame_ms, lambda: frame(i + 1))
        else:
            eval_bar_current_cp = target
            eval_bar_job = None
            _paint_eval_bar(target)

    frame()


# ============================================================
# SINGLE GAME ANALYSIS
# ============================================================

def choose_stockfish():
    global stockfish_path
    path = filedialog.askopenfilename(
        title="Выбери Stockfish",
        filetypes=[("Stockfish", "*.exe"), ("Все файлы", "*.*")]
    )
    if path:
        stockfish_path = path
        app_settings["stockfish_path"] = path
        save_app_settings()
        stockfish_status.configure(text="✅ " + os.path.basename(path))


def choose_pgn():
    global pgn_path
    path = filedialog.askopenfilename(
        title="Выбери PGN",
        filetypes=[("PGN", "*.pgn"), ("Все файлы", "*.*")]
    )
    if path:
        pgn_path = path
        pgn_status.configure(text="✅ " + os.path.basename(path))


def fetch_latest_game():
    global pgn_path
    username = username_entry.get().strip()

    if not username:
        messagebox.showwarning("GameCoach", "Введи ник Chess.com.")
        return

    chesscom_button.configure(state="disabled", text="⏳ Загружаю...")
    threading.Thread(target=_fetch_latest_game_worker, args=(username,), daemon=True).start()


def _fetch_latest_game_worker(username):
    global pgn_path
    try:
        games = fetch_recent_chesscom_games(username, 1)
        if not games:
            raise Exception("Партии не найдены.")

        safe = "".join(c for c in username if c.isalnum() or c in "_-")
        filename = os.path.abspath(f"chesscom_{safe}_latest.pgn")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(games[-1]["pgn"])

        pgn_path = filename
        root.after(0, lambda: pgn_status.configure(text="✅ " + os.path.basename(filename)))
        root.after(0, lambda: status_label.configure(text="✅ Последняя партия загружена"))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Chess.com", str(e)))
    finally:
        root.after(0, lambda: chesscom_button.configure(state="normal", text="🌐 Последняя"))


def start_single_analysis():
    username = username_entry.get().strip()
    if not stockfish_path:
        messagebox.showwarning("GameCoach", "Выбери Stockfish.")
        return
    if not pgn_path:
        messagebox.showwarning("GameCoach", "Выбери PGN или загрузи последнюю партию.")
        return

    analyse_button.configure(state="disabled", text="⏳ Анализ...")
    progress_bar.set(0)
    threading.Thread(target=_single_analysis_worker, args=(username,), daemon=True).start()


def _single_analysis_worker(username):
    global game_moves, analysed_moves, player_color_global, current_ply_index
    engine = None

    try:
        engine = open_engine()
        if engine is None:
            return

        with open(pgn_path, "r", encoding="utf-8") as f:
            game = chess.pgn.read_game(f)

        if game is None:
            raise Exception("Не удалось прочитать PGN.")

        white = game.headers.get("White", "White")
        black = game.headers.get("Black", "Black")

        if username and white.lower() == username.lower():
            player_color_global = chess.WHITE
        elif username and black.lower() == username.lower():
            player_color_global = chess.BLACK
        else:
            player_color_global = chess.WHITE

        board = game.board()
        raw_moves = list(game.mainline_moves())
        game_moves = []
        analysed_moves = []

        sans_sequence = []

        for i, move in enumerate(raw_moves):
            before = board.copy()
            mover = before.turn
            san = before.san(move)
            sans_sequence.append(san)

            before_info = engine.analyse(before, chess.engine.Limit(depth=int(app_settings.get("engine_depth_single", 10))))
            before_cp = pov_score_cp(before_info, chess.WHITE)
            pv = before_info.get("pv", [])
            best_move = pv[0] if pv else None
            best_san = before.san(best_move) if best_move else "—"

            board.push(move)
            after = board.copy()

            after_info = engine.analyse(after, chess.engine.Limit(depth=int(app_settings.get("engine_depth_single", 10))))
            after_cp = pov_score_cp(after_info, chess.WHITE)
            after_pv = after_info.get("pv", [])

            raw_loss = before_cp - after_cp if mover == chess.WHITE else after_cp - before_cp
            loss = max(0, raw_loss)
            if abs(before_cp) >= 90000 or abs(after_cp) >= 90000:
                loss = min(loss, 1000)

            quality, move_type = get_quality(loss, move, best_move)

            move_label = f"{before.fullmove_number}." if mover == chess.WHITE else f"{before.fullmove_number}..."

            item = {
                "move": move,
                "san": san,
                "move_label": move_label,
                "mover_color": mover,
                "before_cp": before_cp,
                "after_cp": after_cp,
                "before_eval": score_to_text(before_cp),
                "after_eval": score_to_text(after_cp),
                "best_move": best_move,
                "best_san": best_san,
                "variation": pv_to_san(before, pv, 8),
                "pv_uci": [m.uci() for m in pv[:6]],
                "after_pv_uci": [m.uci() for m in after_pv[:6]],
                "loss": loss,
                "quality": quality,
                "type": move_type,
                "phase": get_phase(before),
                "fen": before.fen(),
                "explanation": explain_move(before, move, best_move, loss, after_pv, mover),
            }

            game_moves.append(item)
            analysed_moves.append(item)

            root.after(0, lambda p=(i+1)/max(1,len(raw_moves)): progress_bar.set(p))
            root.after(0, lambda a=i+1,t=len(raw_moves): status_label.configure(text=f"Анализировано {a}/{t}"))

        opening = detect_opening_from_sans(sans_sequence[:8])
        opening_label.configure(text="Дебют: " + opening)

        current_ply_index = -1
        root.after(0, finish_single_analysis)

    except Exception as e:
        root.after(0, lambda text=str(e): analysis_failed(text))
    finally:
        if engine:
            try:
                engine.quit()
            except Exception:
                pass

def finish_single_analysis():
    analyse_button.configure(state="normal", text="🚀 Анализировать")
    progress_bar.set(1)
    status_label.configure(text="✅ Готово • открой ключевые моменты или график")
    update_move_list()
    show_current_position()


def analysis_failed(error):
    analyse_button.configure(state="normal", text="🚀 Анализировать")
    progress_bar.set(0)
    status_label.configure(text="❌ Ошибка")
    messagebox.showerror("GameCoach", error)


# ============================================================
# MOVE NAVIGATION
# ============================================================

def board_at_ply(index):
    board = chess.Board()
    for i, item in enumerate(game_moves):
        if i > index:
            break
        board.push(item["move"])
    return board


def update_move_list():
    moves_box.configure(state="normal")
    moves_box.delete("1.0", "end")
    line = ""

    for i, item in enumerate(game_moves):
        if i % 2 == 0:
            if line:
                moves_box.insert("end", line + "\n")
            line = f"{i//2+1}. {item['san']}"
        else:
            line += f" {item['san']}"

    if line:
        moves_box.insert("end", line)

    moves_box.configure(state="disabled")


def render_coach_text(widget, text):
    """Render coach text with hierarchy instead of a wall of plain text."""
    mode = app_settings.get("text_mode", "Обычный")
    blocks = [b.strip() for b in text.split("━━━━━━━━━━━━━━━━━━━━") if b.strip()]

    if mode == "Коротко":
        blocks = blocks[:4]
    elif mode == "Подробно":
        pass

    widget.configure(state="normal")
    widget.delete("1.0", "end")

    # CTkTextbox deliberately forbids changing font through tag_config(),
    # because tag fonts conflict with CustomTkinter DPI/widget scaling.
    # Keep the textbox's own scalable font and use safe tag properties only.
    widget.tag_config("section", foreground="#F2F4F3", spacing1=8, spacing3=5)
    widget.tag_config("body", foreground="#D9DEDB", spacing1=2, spacing3=4)
    widget.tag_config("muted", foreground="#9AA4B2", spacing1=2, spacing3=4)
    widget.tag_config("best", foreground="#78D9A7", spacing1=2, spacing3=4)
    widget.tag_config("lesson", foreground="#E8B15B", spacing1=2, spacing3=4)

    for bi, block in enumerate(blocks):
        lines = block.splitlines()
        if not lines:
            continue

        heading = lines[0].strip()
        widget.insert("end", heading + "\n", "section")

        for line in lines[1:]:
            stripped = line.strip()
            tag = "body"
            if stripped.startswith(("Лучше", "✓", "Твой ход")):
                tag = "best"
            elif stripped.startswith(("□", "•")):
                tag = "body"
            elif "запомни" in stripped.lower() or "практический урок" in stripped.lower():
                tag = "lesson"
            widget.insert("end", line + "\n", tag)

        if bi < len(blocks) - 1:
            widget.insert("end", "\n", "muted")

    widget.configure(state="disabled")


def show_current_position():
    if current_ply_index < 0:
        board = chess.Board()
        draw_board(board)
        draw_eval_bar(0)
        move_counter_label.configure(text="Старт")
        analysis_title.configure(text="Начальная позиция")
        analysis_text.configure(state="normal")
        analysis_text.delete("1.0", "end")
        analysis_text.insert("1.0", "Выбери ход из списка или используй кнопки навигации.")
        analysis_text.configure(state="disabled")
        return

    data = analysed_moves[current_ply_index]
    board = board_at_ply(current_ply_index)

    draw_board(board, last_move=data["move"])
    draw_eval_bar(data["after_cp"])

    move_counter_label.configure(text=f"{current_ply_index+1}/{len(game_moves)}")
    analysis_title.configure(text=f"{data['move_label']} {data['san']}   {data['quality']}")
    eval_label.configure(text=f"Оценка: {data['before_eval']} → {data['after_eval']}")
    best_label.configure(text="Лучший ход: " + data["best_san"])
    variation_label.configure(text="Линия Stockfish:\n" + data["variation"])

    render_coach_text(analysis_text, data["explanation"])


def go_to_ply(index):
    global current_ply_index
    stop_autoplay()
    if not game_moves:
        return
    current_ply_index = max(-1, min(len(game_moves)-1, index))
    show_current_position()


def go_start():
    go_to_ply(-1)


def play_sound_for_ply(index):
    if index < 0 or index >= len(game_moves):
        return
    try:
        before = board_at_ply(index - 1)
        move = game_moves[index]["move"]
        after = before.copy()
        is_capture = before.is_capture(move)
        is_castle = before.is_castling(move)
        after.push(move)

        if move.promotion:
            safe_beep("promotion")
        elif is_castle:
            safe_beep("castle")
        elif after.is_check():
            safe_beep("check")
        elif is_capture:
            safe_beep("capture")
        else:
            safe_beep("move")
    except Exception:
        safe_beep("move")


def go_prev():
    target = current_ply_index - 1
    go_to_ply(target)
    if target >= 0:
        play_sound_for_ply(target)


def go_next():
    target = current_ply_index + 1
    if target < len(game_moves):
        go_to_ply(target)
        play_sound_for_ply(target)


def go_end():
    if game_moves:
        target = len(game_moves) - 1
        go_to_ply(target)
        play_sound_for_ply(target)


def on_move_list_click(event):
    if not game_moves:
        return

    idx = moves_box.index(f"@{event.x},{event.y}")
    line_no = int(idx.split(".")[0]) - 1
    col = int(idx.split(".")[1])

    base = line_no * 2
    text = moves_box.get(f"{line_no+1}.0", f"{line_no+1}.end")
    spaces = [i for i,c in enumerate(text) if c == " "]

    if len(spaces) < 2:
        target = base
    else:
        target = base if col <= spaces[1] else base + 1

    if target < len(game_moves):
        go_to_ply(target)



# ============================================================
# GAMECOACH 16.1 — KEY MOMENTS / EVAL GRAPH / CALCULATION
# ============================================================

def get_key_moments(limit=8):
    """Critical Moments 2.0: combine loss, eval swing, tactics and game phase."""
    if not analysed_moves:return []
    candidates=[]
    for i,d in enumerate(analysed_moves):
        loss=float(d.get("loss",0) or 0)
        swing=abs(float(d.get("after_cp",0) or 0)-float(d.get("before_cp",0) or 0))
        tactical=0
        try:
            b=chess.Board(d["fen"]);m=d["move"];a=b.copy();a.push(m)
            if b.is_capture(m):tactical+=22
            if a.is_check():tactical+=28
            if b.legal_moves.count()<=12:tactical+=18
        except Exception:pass
        phase_bonus=15 if str(d.get("phase","")).lower() in ("миттельшпиль","эндшпиль") else 5
        score=loss*1.0+swing*.42+tactical+phase_bonus
        if loss>=50 or swing>=100 or tactical>=40:
            label="Критический момент" if score>=180 else "Важное решение"
            candidates.append((score,i,label))
    if not candidates:
        candidates=[(1,max(range(len(analysed_moves)),key=lambda j:abs(float(analysed_moves[j].get("after_cp",0))-float(analysed_moves[j].get("before_cp",0)))),"Перелом")]
    picked=[]
    for score,idx,label in sorted(candidates,reverse=True):
        if all(abs(idx-p[1])>=2 for p in picked):
            picked.append((score,idx,label))
        if len(picked)>=limit:break
    return sorted(picked,key=lambda x:x[1])



def open_key_moments():
    if not analysed_moves:
        messagebox.showinfo("GameCoach", "Сначала проанализируй партию.")
        return

    moments = get_key_moments()
    win = ctk.CTkToplevel(root)
    win.title("Ключевые моменты")
    win.geometry("660x620")

    ctk.CTkLabel(
        win, text="🎯 Ключевые моменты партии",
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
    ).pack(anchor="w", padx=20, pady=(18,4))
    ctk.CTkLabel(
        win,
        text="GameCoach выбрал позиции, которые сильнее всего повлияли на ход партии.",
        text_color="#98A3B1"
    ).pack(anchor="w", padx=20, pady=(0,12))

    scroll=ctk.CTkScrollableFrame(win, corner_radius=14)
    scroll.pack(fill="both", expand=True, padx=18, pady=(0,18))

    for n,(_,idx,label) in enumerate(moments,1):
        d=analysed_moves[idx]
        card=ctk.CTkFrame(scroll, corner_radius=13)
        card.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(
            card, text=f"{n}. {d['move_label']} {d['san']}  •  {label}",
            font=ctk.CTkFont(size=15,weight="bold")
        ).pack(anchor="w",padx=14,pady=(11,3))
        ctk.CTkLabel(
            card,
            text=f"{d['quality']}  |  потеря ≈ {d['loss']/100:.2f}  |  {d['phase']}",
            text_color="#AAB3BF"
        ).pack(anchor="w",padx=14,pady=(0,8))

        row=ctk.CTkFrame(card,fg_color="transparent")
        row.pack(fill="x",padx=14,pady=(0,11))
        ctk.CTkButton(
            row,text="Открыть",width=100,
            command=lambda j=idx,w=win:(go_to_ply(j),w.destroy())
        ).pack(side="left",padx=(0,6))
        ctk.CTkButton(
            row,text="🧠 Решить",width=110,
            command=lambda j=idx,w=win:(go_to_ply(j),w.destroy(),root.after(80,think_first_current_position))
        ).pack(side="left",padx=6)
        ctk.CTkButton(
            row,text="🧩 Линия",width=105,
            command=lambda j=idx,w=win:(go_to_ply(j),w.destroy(),root.after(80,start_calculation_challenge))
        ).pack(side="left",padx=6)


def open_eval_graph():
    if not analysed_moves:
        messagebox.showinfo("GameCoach", "Сначала проанализируй партию.")
        return

    win=ctk.CTkToplevel(root)
    win.title("График оценки")
    win.geometry("920x520")

    ctk.CTkLabel(
        win,text="📈 График оценки партии",
        font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold")
    ).pack(anchor="w",padx=20,pady=(16,2))
    hint=ctk.CTkLabel(win,text="Нажми на точку графика, чтобы перейти к позиции.",text_color="#98A3B1")
    hint.pack(anchor="w",padx=20,pady=(0,8))

    W,H=870,390
    cv=tk.Canvas(win,width=W,height=H,highlightthickness=0,bg="#11161D")
    cv.pack(padx=20,pady=(4,18))

    vals=[0]+[max(-1000,min(1000,float(d.get("after_cp",0)))) for d in analysed_moves]
    n=max(1,len(vals)-1)
    left,top,right,bottom=42,22,W-20,H-34
    mid=(top+bottom)/2

    cv.create_line(left,mid,right,mid,fill="#59616C",width=1)
    cv.create_text(10,mid,text="0",fill="#AAB3BF",anchor="w")
    cv.create_text(8,top,text="+10",fill="#AAB3BF",anchor="w")
    cv.create_text(8,bottom,text="-10",fill="#AAB3BF",anchor="w")

    def point(i,cp):
        x=left+(right-left)*(i/n)
        y=mid-(cp/1000)*(bottom-top)/2
        return x,max(top,min(bottom,y))

    pts=[]
    for i,v in enumerate(vals):
        pts.extend(point(i,v))
    if len(pts)>=4:
        cv.create_line(*pts,fill="#D7DCE3",width=3,smooth=True)

    # Important moments become clickable dots.
    important={idx for _,idx,_ in get_key_moments(10)}
    for idx,d in enumerate(analysed_moves):
        x,y=point(idx+1,vals[idx+1])
        r=7 if idx in important else 4
        color="#EF6461" if d.get("loss",0)>=150 else ("#E9B949" if d.get("loss",0)>=70 else "#7F8A98")
        tag=f"p{idx}"
        cv.create_oval(x-r,y-r,x+r,y+r,fill=color,outline="",tags=(tag,))
        cv.tag_bind(tag,"<Button-1>",lambda e,j=idx:(go_to_ply(j),win.destroy()))
        cv.tag_bind(tag,"<Enter>",lambda e,j=idx:hint.configure(
            text=f"{analysed_moves[j]['move_label']} {analysed_moves[j]['san']} • {analysed_moves[j]['quality']} • потеря {analysed_moves[j]['loss']/100:.2f}"
        ))


def start_calculation_challenge():
    """Multi-ply memory/calculation exercise from Stockfish's saved PV."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери проанализированный ход.")
        return

    data=analysed_moves[current_ply_index]
    pv=data.get("pv_uci") or []
    if len(pv)<2:
        messagebox.showinfo("GameCoach","Для этой позиции нет достаточно длинного варианта.")
        return

    win=ctk.CTkToplevel(root)
    win.title("Тренировка расчёта")
    win.geometry("760x700")
    state={"board":chess.Board(data["fen"]),"step":0,"selected":None,"failed":False}
    target=[chess.Move.from_uci(x) for x in pv[:min(6,len(pv))]]

    ctk.CTkLabel(
        win,text="🧩 Рассчитай вариант",
        font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold")
    ).pack(anchor="w",padx=18,pady=(14,2))
    info=ctk.CTkLabel(
        win,text="Найди лучший ход. После твоего правильного хода соперник ответит автоматически.",
        text_color="#AAB3BF"
    )
    info.pack(anchor="w",padx=18,pady=(0,8))

    size=560;sq=size/8
    cv=tk.Canvas(win,width=size,height=size,highlightthickness=0)
    cv.pack(pady=6)
    refs=[]

    def redraw():
        cv.delete("all");refs.clear()
        b=state["board"];theme=current_board_theme()
        for row in range(8):
            for col in range(8):
                f=col;r=7-row;q=chess.square(f,r)
                light=(f+r)%2==1
                fill=theme["light"] if light else theme["dark"]
                if q==state["selected"]: fill=theme["last_light"] if light else theme["last_dark"]
                cv.create_rectangle(col*sq,row*sq,(col+1)*sq,(row+1)*sq,fill=fill,outline="")
        for q,pc in b.piece_map().items():
            f=chess.square_file(q);r=chess.square_rank(q)
            fn=PIECE_MAP.get(pc.symbol());path=os.path.join(PIECES_FOLDER,(fn or "")+".png")
            if os.path.exists(path):
                im=Image.open(path).convert("RGBA")
                im.thumbnail((int(sq*.88),int(sq*.88)),Image.Resampling.LANCZOS)
                ph=ImageTk.PhotoImage(im);refs.append(ph)
                cv.create_image(f*sq+sq/2,(7-r)*sq+sq/2,image=ph)

    def sq_at(e):
        f=int(e.x//sq); row=int(e.y//sq)
        if 0<=f<8 and 0<=row<8:return chess.square(f,7-row)
        return None

    def opponent_reply():
        if state["step"]>=len(target):
            info.configure(text="✅ Вариант найден полностью!")
            safe_beep("correct"); return
        mv=target[state["step"]]
        if mv not in state["board"].legal_moves:
            info.configure(text="Вариант завершён.")
            return
        state["board"].push(mv);state["step"]+=1
        redraw()
        if state["step"]>=len(target):
            info.configure(text="✅ Отлично. Ты дошёл до конца линии.")
            safe_beep("correct")
        else:
            info.configure(text=f"Ход {state['step']//2+1}: теперь снова найди лучший ход.")

    def click(e):
        if state["step"]>=len(target):return
        # User plays even plies; engine auto-plays odd plies.
        if state["step"]%2==1:return
        q=sq_at(e)
        if q is None:return
        b=state["board"]
        if state["selected"] is None:
            pc=b.piece_at(q)
            if pc and pc.color==b.turn:
                state["selected"]=q;redraw()
            return
        fr=state["selected"];pc=b.piece_at(fr)
        mv=chess.Move(fr,q)
        if pc and pc.piece_type==chess.PAWN and chess.square_rank(q) in (0,7):
            mv=chess.Move(fr,q,promotion=chess.QUEEN)
        state["selected"]=None
        if mv not in b.legal_moves:
            redraw();return
        expected=target[state["step"]]
        if mv!=expected:
            safe_beep("wrong")
            info.configure(text="❌ Не этот ход. Вариант скрыт — попробуй ещё раз.")
            redraw();return
        b.push(mv);state["step"]+=1;safe_beep("correct");redraw()
        if state["step"]<len(target):
            win.after(450,opponent_reply)
        else:
            info.configure(text="✅ Вариант найден полностью!")

    cv.bind("<Button-1>",click)
    redraw()


# ============================================================
# AUTOPLAY
# ============================================================

def animate_to_ply(target, callback=None):
    global animation_running, current_ply_index

    if target < 0 or target >= len(game_moves) or animation_running:
        if callback:
            callback()
        return

    before = board_at_ply(target-1)
    move = game_moves[target]["move"]
    piece = before.piece_at(move.from_square)

    if piece is None or piece.symbol() not in piece_images:
        current_ply_index = target
        show_current_position()
        if callback:
            callback()
        return

    animation_running = True
    flipped = player_color_global == chess.BLACK
    draw_board(before, hidden_square=move.from_square)

    x1, y1 = square_to_canvas(move.from_square, flipped)
    x2, y2 = square_to_canvas(move.to_square, flipped)
    moving_id = board_canvas.create_image(x1, y1, image=piece_images[piece.symbol()])

    total_ms = max(150, int(app_settings.get("animation_ms", 420)))
    steps = 24
    frame_ms = max(8, total_ms // steps)
    count = 0

    def step():
        nonlocal count
        global animation_running, current_ply_index

        if count < steps:
            count += 1
            t = count / steps
            eased = 3 * t * t - 2 * t * t * t
            board_canvas.coords(
                moving_id,
                x1 + (x2 - x1) * eased,
                y1 + (y2 - y1) * eased
            )
            root.after(frame_ms, step)
        else:
            animation_running = False
            current_ply_index = target
            show_current_position()

            after = board_at_ply(target)
            if move.promotion:
                safe_beep("promotion")
            elif before.is_castling(move):
                safe_beep("castle")
            elif after.is_check():
                safe_beep("check")
            elif before.is_capture(move):
                safe_beep("capture")
            else:
                safe_beep("move")

            if callback:
                callback()

    step()


def autoplay_step():
    if not autoplay_running:
        return

    next_index = current_ply_index + 1
    if next_index >= len(game_moves):
        stop_autoplay()
        return

    animate_to_ply(next_index, callback=schedule_next_autoplay)


def schedule_next_autoplay():
    global autoplay_job
    if autoplay_running:
        autoplay_job = root.after(500, autoplay_step)


def toggle_autoplay():
    global autoplay_running
    if not game_moves:
        return

    if autoplay_running:
        stop_autoplay()
    else:
        autoplay_running = True
        autoplay_button.configure(text="⏸ Стоп")
        autoplay_step()


def stop_autoplay():
    global autoplay_running, autoplay_job
    autoplay_running = False
    autoplay_button.configure(text="▶ Авто")
    if autoplay_job is not None:
        try:
            root.after_cancel(autoplay_job)
        except Exception:
            pass
        autoplay_job = None


# ============================================================
# CHESS.COM MULTI-GAME
# ============================================================

def fetch_recent_chesscom_games(username, limit=int(app_settings.get("recent_games", 20))):
    headers = {"User-Agent": "GameCoach/30.0"}
    archives_url = f"https://api.chess.com/pub/player/{urllib.parse.quote(username)}/games/archives"

    req = urllib.request.Request(archives_url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        archives = json.loads(r.read().decode("utf-8"))

    urls = archives.get("archives", [])
    if not urls:
        return []

    result = []

    for archive_url in reversed(urls):
        req = urllib.request.Request(archive_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))

        games = sorted(data.get("games", []), key=lambda g: g.get("end_time", 0), reverse=True)

        for g in games:
            if g.get("pgn"):
                result.append(g)
                if len(result) >= limit:
                    return list(reversed(result))

    return list(reversed(result))


def start_profile_analysis():
    username = username_entry.get().strip()
    if not username:
        messagebox.showwarning("GameCoach", "Введи ник Chess.com.")
        return
    if not stockfish_path:
        messagebox.showwarning("GameCoach", "Выбери Stockfish.")
        return

    profile_button.configure(state="disabled", text="⏳ 20 партий...")
    status_label.configure(text="🌐 Загружаю последние партии Chess.com...")
    threading.Thread(target=_profile_worker, args=(username,), daemon=True).start()


def _profile_worker(username):
    global multi_game_reports, training_positions
    engine = None

    try:
        games = fetch_recent_chesscom_games(username, int(app_settings.get("recent_games", 20)))
        if not games:
            raise Exception("Не найдено партий Chess.com.")

        engine = open_engine()
        if engine is None:
            return

        reports = []
        training = []

        for game_index, g in enumerate(games):
            pgn_text = g.get("pgn", "")
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if game is None:
                continue

            white = game.headers.get("White", "")
            black = game.headers.get("Black", "")

            if white.lower() == username.lower():
                user_color = chess.WHITE
            elif black.lower() == username.lower():
                user_color = chess.BLACK
            else:
                continue

            board = game.board()
            raw_moves = list(game.mainline_moves())
            sans = []

            phase_errors = Counter()
            errors = []
            user_moves_count = 0
            blunders = 0
            mistakes = 0
            inaccuracies = 0

            for move in raw_moves:
                before = board.copy()
                san = before.san(move)
                sans.append(san)
                mover = before.turn

                if mover != user_color:
                    board.push(move)
                    continue

                user_moves_count += 1

                info_before = engine.analyse(before, chess.engine.Limit(depth=int(app_settings.get("engine_depth_profile", 8))))
                before_cp = pov_score_cp(info_before, user_color)
                pv = info_before.get("pv", [])
                best_move = pv[0] if pv else None

                board.push(move)
                after = board.copy()

                info_after = engine.analyse(after, chess.engine.Limit(depth=int(app_settings.get("engine_depth_profile", 8))))
                after_cp = pov_score_cp(info_after, user_color)

                loss = max(0, before_cp - after_cp)
                if abs(before_cp) >= 90000 or abs(after_cp) >= 90000:
                    loss = min(loss, 1000)

                quality, move_type = get_quality(loss, move, best_move)
                phase = get_phase(before)

                if move_type in ("blunder", "mistake", "inaccuracy"):
                    phase_errors[phase] += 1
                    errors.append({
                        "move_no": before.fullmove_number,
                        "san": san,
                        "loss": loss,
                        "type": move_type,
                        "phase": phase
                    })

                if move_type == "blunder":
                    blunders += 1
                elif move_type == "mistake":
                    mistakes += 1
                elif move_type == "inaccuracy":
                    inaccuracies += 1

                if move_type in ("blunder", "mistake") and best_move is not None:
                    training.append({
                        "fen": before.fen(),
                        "best_move": best_move.uci(),
                        "played_move": move.uci(),
                        "played_san": san,
                        "best_san": before.san(best_move),
                        "loss": loss,
                        "phase": phase,
                        "game_index": game_index + 1
                    })

            opening = detect_opening_from_sans(sans[:8])

            reports.append({
                "date": game.headers.get("Date", "?"),
                "white": white,
                "black": black,
                "result": game.headers.get("Result", "?"),
                "user_color": "White" if user_color == chess.WHITE else "Black",
                "opening": opening,
                "user_moves": user_moves_count,
                "blunders": blunders,
                "mistakes": mistakes,
                "inaccuracies": inaccuracies,
                "errors": errors,
                "phase_errors": dict(phase_errors)
            })

            root.after(
                0,
                lambda a=game_index+1, t=len(games):
                status_label.configure(text=f"Профиль: обработано {a}/{t} партий")
            )

        multi_game_reports = reports
        training_positions = training

        profile = build_profile_summary(username, reports)
        save_json(PROFILE_FILE, profile)
        db_store_profile_games(reports)
        db_save_progress_snapshot(profile)

        root.after(0, lambda: finish_profile(profile))

    except Exception as e:
        root.after(0, lambda text=str(e): profile_failed(text))

    finally:
        if engine:
            try:
                engine.quit()
            except Exception:
                pass

def build_profile_summary(username, reports):
    phase_counter = Counter()
    opening_counter = Counter()
    opening_errors = Counter()

    total_blunders = 0
    total_mistakes = 0
    total_inaccuracies = 0
    white_games = 0
    black_games = 0
    white_errors = 0
    black_errors = 0

    move_buckets = Counter()

    for r in reports:
        opening_counter[r["opening"]] += 1

        total_blunders += r["blunders"]
        total_mistakes += r["mistakes"]
        total_inaccuracies += r["inaccuracies"]

        game_errors = r["blunders"] + r["mistakes"] + r["inaccuracies"]
        opening_errors[r["opening"]] += game_errors

        if r["user_color"] == "White":
            white_games += 1
            white_errors += game_errors
        else:
            black_games += 1
            black_errors += game_errors

        for phase, count in r["phase_errors"].items():
            phase_counter[phase] += count

        for err in r["errors"]:
            n = err["move_no"]
            if n <= 10:
                move_buckets["1–10"] += 1
            elif n <= 20:
                move_buckets["11–20"] += 1
            elif n <= 30:
                move_buckets["21–30"] += 1
            else:
                move_buckets["31+"] += 1

    weakness = phase_counter.most_common(1)[0][0] if phase_counter else "Нет явной"
    worst_opening = opening_errors.most_common(1)[0][0] if opening_errors else "Нет данных"
    common_openings = opening_counter.most_common(5)

    return {
        "username": username,
        "games": len(reports),
        "blunders": total_blunders,
        "mistakes": total_mistakes,
        "inaccuracies": total_inaccuracies,
        "weak_phase": weakness,
        "worst_opening": worst_opening,
        "common_openings": common_openings,
        "phase_errors": dict(phase_counter),
        "move_buckets": dict(move_buckets),
        "white_games": white_games,
        "black_games": black_games,
        "white_errors": white_errors,
        "black_errors": black_errors,
        "training_positions": len(training_positions),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


def finish_profile(profile):
    profile_button.configure(state="normal", text="🧠 Мой шахматный профиль")
    status_label.configure(text="✅ Профиль последних партий готов")
    show_profile_window(profile)
    try:
        refresh_dashboard()
    except Exception:
        pass


def profile_failed(error):
    profile_button.configure(state="normal", text="🧠 Мой шахматный профиль")
    status_label.configure(text="❌ Ошибка профиля")
    messagebox.showerror("GameCoach", error)


def show_profile_window(profile=None):
    if profile is None:
        profile = load_json(PROFILE_FILE, {})
    if not profile:
        messagebox.showinfo("GameCoach", "Сначала нажми «Мои слабости».")
        return

    window = ctk.CTkToplevel(root)
    window.title("GameCoach — Мои слабости")
    window.geometry("850x720")

    box = ctk.CTkTextbox(window, wrap="word", font=ctk.CTkFont(size=15))
    box.pack(fill="both", expand=True, padx=20, pady=20)

    common_openings = profile.get("common_openings", [])
    opening_text = "\n".join(
        f"• {name}: {count} партий"
        for name, count in common_openings
    ) or "• Нет данных"

    phase_errors = profile.get("phase_errors", {})
    phase_text = "\n".join(
        f"• {phase}: {count} ошибок"
        for phase, count in phase_errors.items()
    ) or "• Нет данных"

    move_buckets = profile.get("move_buckets", {})
    bucket_text = "\n".join(
        f"• ходы {bucket}: {count} ошибок"
        for bucket, count in move_buckets.items()
    ) or "• Нет данных"

    wg = profile.get("white_games", 0)
    bg = profile.get("black_games", 0)
    we = profile.get("white_errors", 0)
    be = profile.get("black_errors", 0)
    white_rate = we / wg if wg else 0
    black_rate = be / bg if bg else 0

    color_weakness = "примерно одинаково"
    if wg and bg:
        if white_rate > black_rate * 1.15:
            color_weakness = "чаще ошибаешься белыми"
        elif black_rate > white_rate * 1.15:
            color_weakness = "чаще ошибаешься чёрными"

    text = f"""
🧠 ШАХМАТНЫЙ ПРОФИЛЬ — {profile.get('username', '')}

Проанализировано партий: {profile.get('games', 0)}
Обновлено: {profile.get('updated', '')}

🔴 Зевки: {profile.get('blunders', 0)}
🟠 Ошибки: {profile.get('mistakes', 0)}
🟡 Неточности: {profile.get('inaccuracies', 0)}

🎯 Главная слабая стадия:
{profile.get('weak_phase', '—')}

🎨 Цвет:
{color_weakness}

📍 Когда чаще возникают ошибки:
{bucket_text}

♟ Ошибки по стадиям:
{phase_text}

📚 Самые частые дебюты:
{opening_text}

⚠️ Дебют с наибольшим количеством ошибок:
{profile.get('worst_opening', '—')}

🎓 Позиций для тренировки:
{profile.get('training_positions', 0)}

РЕКОМЕНДАЦИЯ
1. Начни с позиций из своих зевков и ошибок.
2. Перед каждым ходом делай проверку: шахи → взятия → угрозы.
3. В слабой стадии партии трать больше времени на проверку ответа соперника.
4. Если один дебют часто даёт ошибки, изучи первые 8–12 ходов и типовые планы.
""".strip()

    box.insert("1.0", text)
    box.configure(state="disabled")


# ============================================================
# TRAINING
# ============================================================

def start_training():
    sort_training_positions()
    global training_active, training_index, training_selected_square

    if not training_positions:
        messagebox.showinfo("GameCoach", "Сначала создай шахматный профиль кнопкой «Мой профиль».")
        return

    training_active = True
    training_index = 0
    training_selected_square = None
    show_training_position()


def show_training_position():
    global training_selected_square

    if not training_positions:
        return

    data = training_positions[training_index]
    board = chess.Board(data["fen"])

    training_selected_square = None
    draw_board(board)
    training_status.configure(
        text=(
            f"🎓 Позиция {training_index+1}/{len(training_positions)} | "
            f"{data['phase']} | твой прошлый ход: {data['played_san']}\n"
            f"Перетащи фигуру и найди лучший ход."
        )
    )


def next_training_position():
    global training_index
    if not training_positions:
        return
    training_index = (training_index + 1) % len(training_positions)
    show_training_position()


def reveal_training_answer():
    if not training_positions:
        return
    data = training_positions[training_index]
    data["_hint_used"] = True
    board = chess.Board(data["fen"])
    best = chess.Move.from_uci(data["best_move"])
    draw_board(board, best_move=best)
    training_status.configure(text="💡 Лучший ход: " + data["best_san"])


def training_try_move(from_sq, to_sq):
    global training_session_correct,training_session_wrong
    if not training_positions:return
    data=training_positions[training_index];board=chess.Board(data["fen"])
    piece=board.piece_at(from_sq)
    if piece is None:return
    candidate=chess.Move(from_sq,to_sq)
    if piece.piece_type==chess.PAWN and chess.square_rank(to_sq) in (0,7):
        candidate=chess.Move(from_sq,to_sq,promotion=chess.QUEEN)
    if candidate not in board.legal_moves:
        draw_board(board);return
    best=chess.Move.from_uci(data["best_move"])
    elapsed=time.time()-float(data.get("_timer_started",time.time()))
    first_try=bool(data.get("_first_try",True))
    key=training_key(data)

    if candidate==best:
        loss=0;acceptable=True;quality="лучший ход"
    else:
        # Fairness: a different move can still be excellent. Evaluate asynchronously would be ideal;
        # here use Stockfish synchronously only for a deliberate puzzle submission.
        result=candidate_engine_loss(board,candidate,board.turn)
        loss=result[0] if result else 99999
        acceptable=loss<=50
        quality=f"очень сильный ход (потеря {loss/100:.2f})" if acceptable else f"потеря {loss/100:.2f}"

    if acceptable:
        safe_beep("correct");training_session_correct+=1
        pts=award_smart_xp(key,True,bool(data.get("_hint_used",False)),first_try)
        mark_training_result(data,True)
        training_status.configure(text=f"✅ {quality}. Время: {elapsed:.1f} сек • +{pts} XP")
        draw_board(board,best_move=best)
        if data.get("think_first"):_reveal_think_first_result(data,True)
    else:
        safe_beep("wrong");training_session_wrong+=1;data["_first_try"]=False
        try:san=board.san(candidate)
        except Exception:san=candidate.uci()
        training_status.configure(text=f"❌ {san}: {quality}. Время: {elapsed:.1f} сек.\nПопробуй ещё раз — ответ скрыт.")
        draw_board(board)
        if data.get("think_first"):_reveal_think_first_result(data,False)



def on_board_press(event):
    global training_dragging, training_drag_id, training_drag_from, training_drag_board

    if not training_active or not training_positions or animation_running:
        return

    data = training_positions[training_index]
    board = chess.Board(data["fen"])
    flipped = player_color_global == chess.BLACK

    sq = canvas_to_square(event.x, event.y, flipped)
    if sq is None:
        return

    piece = board.piece_at(sq)
    if piece is None or piece.color != board.turn:
        return

    legal = [m.to_square for m in board.legal_moves if m.from_square == sq]
    if not legal:
        return

    draw_board(board, hidden_square=sq, selected_square=sq, legal_squares=legal)

    img = piece_images.get(piece.symbol())
    if not img:
        return

    training_dragging = True
    training_drag_from = sq
    training_drag_board = board
    training_drag_id = board_canvas.create_image(event.x, event.y, image=img)


def on_board_motion(event):
    if training_dragging and training_drag_id is not None:
        board_canvas.coords(training_drag_id, event.x, event.y)


def on_board_release(event):
    global training_dragging, training_drag_id, training_drag_from

    if not training_dragging:
        return

    flipped = player_color_global == chess.BLACK
    to_sq = canvas_to_square(event.x, event.y, flipped)
    from_sq = training_drag_from

    training_dragging = False
    training_drag_id = None
    training_drag_from = None

    if to_sq is None or from_sq is None:
        show_training_position()
        return

    training_try_move(from_sq, to_sq)



# ============================================================
# SMART TRAINER / SPACED REPETITION
# ============================================================

def training_key(item):
    fen = item.get("fen","")
    mv = item.get("best_move","")
    try:
        mv = mv.uci()
    except Exception:
        mv = str(mv or "")
    return f"{fen}|{mv}"



def load_learning_profile():
    global learning_profile
    try:
        if os.path.exists(LEARNING_FILE):
            with open(LEARNING_FILE, "r", encoding="utf-8") as f:
                d=json.load(f)
                if isinstance(d,dict):
                    learning_profile.update(d)
    except Exception:
        pass


def save_learning_profile():
    try:
        with open(LEARNING_FILE,"w",encoding="utf-8") as f:
            json.dump(learning_profile,f,ensure_ascii=False,indent=2)
    except Exception:
        pass


def learning_level():
    xp=int(learning_profile.get("xp",0))
    return 1 + xp//250


def award_smart_xp(key, correct=True, hint_used=False, first_try=True):
    """Anti-farm XP: one meaningful award per puzzle per day."""
    today=datetime.now().strftime("%Y-%m-%d")
    awards=learning_profile.setdefault("xp_awards",{})
    token=f"{today}|{key}"
    if token in awards:
        return 0
    if not correct:
        return 0
    points=15 if first_try and not hint_used else (8 if first_try else 5)
    if hint_used: points=min(points,4)
    learning_profile["xp"]=int(learning_profile.get("xp",0))+points
    awards[token]=points
    # prune old award tokens
    if len(awards)>500:
        for k in list(awards)[:-350]: awards.pop(k,None)
    save_learning_profile()
    return points


def candidate_engine_loss(board, move, color, depth=None):
    """Evaluate a candidate from the same root using Stockfish root_moves."""
    if not stockfish_path or move not in board.legal_moves:
        return None
    eng=None
    try:
        eng=launch_stockfish_engine()
        dep=depth or max(8,min(13,int(app_settings.get("engine_depth_profile",8))+2))
        root_info=eng.analyse(board,chess.engine.Limit(depth=dep))
        root_cp=score_cp_for_color(root_info,color)
        cand_info=eng.analyse(board,chess.engine.Limit(depth=dep),root_moves=[move])
        cand_cp=score_cp_for_color(cand_info,color)
        return max(0,root_cp-cand_cp),cand_cp
    except Exception:
        return None
    finally:
        if eng:
            try:eng.quit()
            except Exception:pass



def award_learning_xp(correct):
    today=datetime.now().strftime("%Y-%m-%d")
    last=learning_profile.get("last_training_day","")
    if last != today:
        # Maintain streak only if previous session was yesterday.
        try:
            prev=datetime.strptime(last,"%Y-%m-%d").date() if last else None
            delta=(datetime.now().date()-prev).days if prev else 999
        except Exception:
            delta=999
        learning_profile["streak"] = int(learning_profile.get("streak",0))+1 if delta==1 else 1
        learning_profile["daily_correct"]=0
        learning_profile["daily_wrong"]=0
        learning_profile["last_training_day"]=today
    if correct:
        learning_profile["xp"]=int(learning_profile.get("xp",0))+12
        learning_profile["daily_correct"]=int(learning_profile.get("daily_correct",0))+1
    else:
        learning_profile["daily_wrong"]=int(learning_profile.get("daily_wrong",0))+1
    save_learning_profile()


def daily_training_plan():
    due=due_training_count() if training_positions else 0
    total=min(12,max(5,due if due else min(8,len(training_positions))))
    return {
        "repeat": min(5,due),
        "mistakes": min(5,total),
        "calculation": 2 if analysed_moves else 0,
        "minutes": 12 + total
    }


def open_today_training():
    """Compatibility entry point for the new guided daily session."""
    open_daily_session()


def open_find_mistake():
    """Replay a fragment; user decides which move is the serious mistake."""
    if not analysed_moves:
        messagebox.showinfo("GameCoach","Сначала проанализируй партию.")
        return
    candidates=[i for i,d in enumerate(analysed_moves) if d.get("loss",0)>=150]
    if not candidates:
        candidates=[max(range(len(analysed_moves)),key=lambda i:analysed_moves[i].get("loss",0))]
    target=candidates[0]
    start=max(0,target-4)
    end=min(len(analysed_moves)-1,target+2)

    win=ctk.CTkToplevel(root);win.title("Найди ошибку");win.geometry("720x690")
    state={"idx":start}
    ctk.CTkLabel(win,text="🕵 Найди ошибку",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=18,pady=(16,2))
    hint=ctk.CTkLabel(win,text="Смотри ходы без оценки. Останови партию там, где заметишь серьёзную ошибку.",
                      text_color="#AAB3BF")
    hint.pack(anchor="w",padx=18,pady=(0,8))
    size=540;sq=size/8
    cv=tk.Canvas(win,width=size,height=size,highlightthickness=0);cv.pack(pady=6)
    refs=[]

    def draw():
        cv.delete("all");refs.clear();b=board_at_ply(state["idx"]);theme=current_board_theme()
        for row in range(8):
            for col in range(8):
                f=col;r=7-row;light=(f+r)%2==1
                cv.create_rectangle(col*sq,row*sq,(col+1)*sq,(row+1)*sq,
                                    fill=theme["light"] if light else theme["dark"],outline="")
        for q,pc in b.piece_map().items():
            fn=PIECE_MAP.get(pc.symbol());path=os.path.join(PIECES_FOLDER,(fn or "")+".png")
            if os.path.exists(path):
                im=Image.open(path).convert("RGBA");im.thumbnail((int(sq*.88),int(sq*.88)),Image.Resampling.LANCZOS)
                ph=ImageTk.PhotoImage(im);refs.append(ph)
                cv.create_image(chess.square_file(q)*sq+sq/2,(7-chess.square_rank(q))*sq+sq/2,image=ph)
        d=analysed_moves[state["idx"]]
        hint.configure(text=f"Ход {d['move_label']} {d['san']} • Где ошибка?")

    def nxt():
        if state["idx"]<end:
            state["idx"]+=1;draw()

    def mark():
        if state["idx"]==target:
            safe_beep("correct");award_learning_xp(True)
            hint.configure(text="✅ Точно! Ты нашёл ключевую ошибку. +12 XP")
        else:
            safe_beep("wrong");award_learning_xp(False)
            hint.configure(text="❌ Не здесь. Посмотри, что изменилось после этого хода, и продолжай.")

    row=ctk.CTkFrame(win,fg_color="transparent");row.pack(pady=10)
    ctk.CTkButton(row,text="▶ Следующий ход",command=nxt,width=160).pack(side="left",padx=5)
    ctk.CTkButton(row,text="⚠ Ошибка здесь!",command=mark,width=160).pack(side="left",padx=5)
    ctk.CTkButton(row,text="Открыть разбор",command=lambda:(go_to_ply(target),win.destroy()),width=150).pack(side="left",padx=5)
    draw()


def open_progress_center():
    attempts=sum(int(r.get("attempts",0)) for r in training_stats.values() if isinstance(r,dict))
    correct=sum(int(r.get("correct",0)) for r in training_stats.values() if isinstance(r,dict))
    accuracy=(100*correct/attempts) if attempts else 0
    m=dashboard_metrics()
    win=ctk.CTkToplevel(root);win.title("Прогресс");win.geometry("820x570")
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="📊 Центр прогресса",
                 font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    xp=int(learning_profile.get("xp",0));lvl=learning_level();streak=int(learning_profile.get("streak",0))
    ctk.CTkLabel(shell,text=f"🏆 Level {lvl}   •   {xp} XP   •   🔥 серия {streak} дн.",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=22,pady=(0,16))
    cards=ctk.CTkFrame(shell,fg_color="transparent");cards.pack(fill="x",padx=16)
    for c,(t,v) in enumerate([
        ("ПАРТИЙ",m["games"]),("ОШИБОК / ПАРТИЮ",f'{m["errors_per_game"]:.1f}'),
        ("ТОЧНОСТЬ ЗАДАЧ",f"{accuracy:.0f}%"),("НА ПОВТОРЕНИЕ",m["due"])
    ]):
        cards.grid_columnconfigure(c,weight=1);fr=ctk.CTkFrame(cards,corner_radius=13)
        fr.grid(row=0,column=c,sticky="nsew",padx=5)
        ctk.CTkLabel(fr,text=t,text_color="#8F9AAA",font=ctk.CTkFont(size=11)).pack(pady=(13,3))
        ctk.CTkLabel(fr,text=str(v),font=ctk.CTkFont(size=23,weight="bold")).pack(pady=(0,13))
    ctk.CTkLabel(shell,text="Текущий фокус",font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=22,pady=(22,5))
    ctk.CTkLabel(shell,text=f"Слабая фаза: {m['weak_phase']}   •   Дебют для внимания: {m['worst_opening']}",
                 text_color="#AAB3BF").pack(anchor="w",padx=22)
    p=ctk.CTkProgressBar(shell);p.pack(fill="x",padx=22,pady=(22,5))
    p.set((xp%250)/250)
    ctk.CTkLabel(shell,text=f"До Level {lvl+1}: {250-(xp%250)} XP",text_color="#98A3B1").pack(anchor="w",padx=22)


def open_gamecoach_home():
    """GameCoach 30: home lives inside the main window instead of a separate popup."""
    try:
        show_home_page()
    except Exception:
        # Safe fallback during very early startup.
        messagebox.showinfo("GameCoach 30","Главная страница ещё загружается.")





def _move_to_text(value):
    try:
        return value.uci()
    except Exception:
        return str(value or "")


def _serializable_training_item(item):
    """Keep only portable fields needed to rebuild a personal puzzle."""
    keep = ("fen","best_move","played_move","played_san","best_san","loss","phase",
            "game_index","user_color","source","note","created")
    out={}
    for k in keep:
        if k not in item:
            continue
        v=item[k]
        if isinstance(v,chess.Move):
            v=v.uci()
        if isinstance(v,(str,int,float,bool)) or v is None:
            out[k]=v
    return out


def load_saved_training_positions():
    global saved_training_positions, training_positions
    try:
        if os.path.exists(SAVED_PUZZLES_FILE):
            with open(SAVED_PUZZLES_FILE,"r",encoding="utf-8") as f:
                data=json.load(f)
            saved_training_positions=data if isinstance(data,list) else []
        else:
            saved_training_positions=[]
    except Exception:
        saved_training_positions=[]

    existing={training_key(x) for x in training_positions}
    for item in saved_training_positions:
        try:
            k=training_key(item)
            if k not in existing:
                training_positions.append(item)
                existing.add(k)
        except Exception:
            pass


def save_saved_training_positions():
    try:
        with open(SAVED_PUZZLES_FILE,"w",encoding="utf-8") as f:
            json.dump([_serializable_training_item(x) for x in saved_training_positions],
                      f,ensure_ascii=False,indent=2)
    except Exception:
        pass


def persist_training_item(item, source="analysis"):
    global saved_training_positions
    portable=_serializable_training_item(item)
    portable["source"]=source
    portable.setdefault("created",datetime.now().isoformat(timespec="seconds"))
    key=training_key(portable)
    for old in saved_training_positions:
        try:
            if training_key(old)==key:
                return False
        except Exception:
            pass
    saved_training_positions.append(portable)
    save_saved_training_positions()
    db_save_puzzle(portable)
    return True


def open_puzzle_library():
    load_saved_training_positions()
    win=ctk.CTkToplevel(root);win.title("Моя библиотека задач");win.geometry("780x650")
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🗂 Моя библиотека задач",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=22,pady=(20,3))
    ctk.CTkLabel(shell,text=f"Сохранено: {len(saved_training_positions)} • позиции остаются после перезапуска GameCoach",
                 text_color="#98A3B1").pack(anchor="w",padx=22,pady=(0,12))
    scroll=ctk.CTkScrollableFrame(shell,corner_radius=12);scroll.pack(fill="both",expand=True,padx=20,pady=(0,18))
    if not saved_training_positions:
        ctk.CTkLabel(scroll,text="Пока пусто. Сохрани ошибку кнопкой «🔁 Повторить».",
                     text_color="#AAB3BF").pack(pady=30)
    for n,item in enumerate(reversed(saved_training_positions),1):
        card=ctk.CTkFrame(scroll,corner_radius=11);card.pack(fill="x",padx=6,pady=5)
        title=f"{n}. {item.get('played_san','позиция')} → лучше {item.get('best_san','?')}"
        ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=14,weight="bold")).pack(anchor="w",padx=13,pady=(10,2))
        ctk.CTkLabel(card,text=f"{item.get('phase','—')} • потеря ≈ {float(item.get('loss',0))/100:.2f}",
                     text_color="#AAB3BF").pack(anchor="w",padx=13,pady=(0,10))



# ============================================================
# GAMECOACH 21 — QUALITY DATA LAYER
# ============================================================

def db_connect():
    conn = sqlite3.connect(DATABASE_FILE, timeout=4)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """Create a durable local store while keeping JSON files backward-compatible."""
    try:
        with db_connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS training_attempts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    puzzle_key TEXT NOT NULL,
                    ts INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    phase TEXT,
                    loss REAL,
                    source TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_attempts_ts ON training_attempts(ts);
                CREATE INDEX IF NOT EXISTS idx_attempts_key ON training_attempts(puzzle_key);

                CREATE TABLE IF NOT EXISTS sessions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_ts INTEGER NOT NULL,
                    ended_ts INTEGER NOT NULL,
                    planned INTEGER NOT NULL,
                    completed INTEGER NOT NULL,
                    correct INTEGER NOT NULL DEFAULT 0,
                    wrong INTEGER NOT NULL DEFAULT 0,
                    note TEXT
                );

                CREATE TABLE IF NOT EXISTS saved_puzzles(
                    puzzle_key TEXT PRIMARY KEY,
                    fen TEXT NOT NULL,
                    best_move TEXT,
                    played_move TEXT,
                    played_san TEXT,
                    best_san TEXT,
                    loss REAL,
                    phase TEXT,
                    source TEXT,
                    created TEXT
                );

                CREATE TABLE IF NOT EXISTS profile_games(
                    game_key TEXT PRIMARY KEY,
                    ts INTEGER NOT NULL,
                    game_date TEXT,
                    white TEXT,
                    black TEXT,
                    result TEXT,
                    user_color TEXT,
                    opening TEXT,
                    user_moves INTEGER,
                    blunders INTEGER,
                    mistakes INTEGER,
                    inaccuracies INTEGER,
                    total_errors INTEGER,
                    phase_errors_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_profile_games_ts ON profile_games(ts);

                CREATE TABLE IF NOT EXISTS progress_snapshots(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    games INTEGER,
                    blunders INTEGER,
                    mistakes INTEGER,
                    inaccuracies INTEGER,
                    weak_phase TEXT,
                    worst_opening TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_progress_snapshots_ts ON progress_snapshots(ts);
            """)
    except Exception:
        pass


def db_save_puzzle(item):
    try:
        p = _serializable_training_item(item)
        key = training_key(p)
        with db_connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO saved_puzzles
                (puzzle_key, fen, best_move, played_move, played_san, best_san,
                 loss, phase, source, created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key, p.get("fen",""), p.get("best_move"), p.get("played_move"),
                p.get("played_san"), p.get("best_san"), float(p.get("loss",0) or 0),
                p.get("phase"), p.get("source"), p.get("created")
            ))
    except Exception:
        pass


def db_log_training_attempt(item, correct):
    try:
        with db_connect() as conn:
            conn.execute("""
                INSERT INTO training_attempts
                (puzzle_key, ts, correct, phase, loss, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                training_key(item), int(time.time()), 1 if correct else 0,
                item.get("phase"), float(item.get("loss",0) or 0), item.get("source","training")
            ))
    except Exception:
        pass


def db_log_session(started_ts, planned, completed, correct=0, wrong=0, note="daily"):
    try:
        with db_connect() as conn:
            conn.execute("""
                INSERT INTO sessions
                (started_ts, ended_ts, planned, completed, correct, wrong, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                int(started_ts), int(time.time()), int(planned), int(completed),
                int(correct), int(wrong), str(note)
            ))
    except Exception:
        pass


def db_recent_progress(days=30):
    """Return durable recent training metrics for progress views."""
    cutoff = int(time.time()) - int(days) * 86400
    out = {"attempts":0, "correct":0, "sessions":0}
    try:
        with db_connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(correct),0) FROM training_attempts WHERE ts>=?",
                (cutoff,)
            ).fetchone()
            out["attempts"] = int(row[0] or 0)
            out["correct"] = int(row[1] or 0)
            row = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE ended_ts>=?", (cutoff,)
            ).fetchone()
            out["sessions"] = int(row[0] or 0)
    except Exception:
        pass
    return out



def db_store_profile_games(reports):
    """Persist aggregated per-game profile rows without storing full PGNs."""
    try:
        now=int(time.time())
        with db_connect() as conn:
            for r in reports:
                total=int(r.get("blunders",0))+int(r.get("mistakes",0))+int(r.get("inaccuracies",0))
                key="|".join([
                    str(r.get("date","?")),str(r.get("white","")),str(r.get("black","")),
                    str(r.get("result","?")),str(r.get("user_color","")),
                    str(r.get("opening","")),str(r.get("user_moves",0)),
                    str(r.get("blunders",0)),str(r.get("mistakes",0)),str(r.get("inaccuracies",0))
                ])
                conn.execute("""
                    INSERT OR REPLACE INTO profile_games
                    (game_key,ts,game_date,white,black,result,user_color,opening,user_moves,
                     blunders,mistakes,inaccuracies,total_errors,phase_errors_json)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,(
                    key,now,r.get("date","?"),r.get("white",""),r.get("black",""),
                    r.get("result","?"),r.get("user_color",""),r.get("opening",""),
                    int(r.get("user_moves",0)),int(r.get("blunders",0)),
                    int(r.get("mistakes",0)),int(r.get("inaccuracies",0)),total,
                    json.dumps(r.get("phase_errors",{}),ensure_ascii=False)
                ))
    except Exception:
        pass


def db_save_progress_snapshot(profile):
    try:
        with db_connect() as conn:
            conn.execute("""
                INSERT INTO progress_snapshots
                (ts,games,blunders,mistakes,inaccuracies,weak_phase,worst_opening)
                VALUES(?,?,?,?,?,?,?)
            """,(
                int(time.time()),int(profile.get("games",0)),int(profile.get("blunders",0)),
                int(profile.get("mistakes",0)),int(profile.get("inaccuracies",0)),
                profile.get("weak_phase",""),profile.get("worst_opening","")
            ))
    except Exception:
        pass


def db_game_progress(limit=60):
    out=[]
    try:
        with db_connect() as conn:
            rows=conn.execute("""
                SELECT game_date,white,black,result,user_color,opening,user_moves,
                       blunders,mistakes,inaccuracies,total_errors,phase_errors_json,ts
                FROM profile_games ORDER BY ts DESC,rowid DESC LIMIT ?
            """,(int(limit),)).fetchall()
        for row in rows:
            try: phases=json.loads(row[11] or "{}")
            except Exception: phases={}
            out.append({
                "date":row[0],"white":row[1],"black":row[2],"result":row[3],
                "user_color":row[4],"opening":row[5],"user_moves":int(row[6] or 0),
                "blunders":int(row[7] or 0),"mistakes":int(row[8] or 0),
                "inaccuracies":int(row[9] or 0),"errors":int(row[10] or 0),
                "phase_errors":phases,"ts":int(row[12] or 0)
            })
    except Exception:
        pass
    return out


def progress_window_metrics(games):
    n=len(games)
    if not n:return {"games":0,"errors_pg":0,"blunders_pg":0,"mistakes_pg":0,"inacc_pg":0}
    return {
        "games":n,
        "errors_pg":sum(g["errors"] for g in games)/n,
        "blunders_pg":sum(g["blunders"] for g in games)/n,
        "mistakes_pg":sum(g["mistakes"] for g in games)/n,
        "inacc_pg":sum(g["inaccuracies"] for g in games)/n,
    }


def progress_trend_summary():
    games=db_game_progress(60)
    recent=games[:10]
    previous=games[10:20]
    a=progress_window_metrics(recent)
    b=progress_window_metrics(previous)
    if not previous:
        direction="Недостаточно старых партий для сравнения двух периодов."
        delta=None
    else:
        delta=a["errors_pg"]-b["errors_pg"]
        if delta<=-0.5: direction="📈 Ошибок на партию стало заметно меньше."
        elif delta<0: direction="↗ Есть небольшое улучшение."
        elif delta>=0.5: direction="📉 Ошибок на партию стало заметно больше."
        else: direction="➡ Уровень ошибок примерно стабилен."
    return {"games":games,"recent":a,"previous":b,"delta":delta,"direction":direction}


def weekly_coach_report_text():
    trend=progress_trend_summary()
    games=trend["games"]
    recent=games[:10]
    train7=db_recent_progress(7)
    train30=db_recent_progress(30)

    phase=Counter()
    openings=Counter()
    for g in recent:
        phase.update(g.get("phase_errors",{}))
        if g.get("opening"):openings[g["opening"]]+=g.get("errors",0)

    weak=phase.most_common(1)[0][0] if phase else "пока не определена"
    worst=openings.most_common(1)[0][0] if openings else "пока не определён"
    acc7=100*train7["correct"]/train7["attempts"] if train7["attempts"] else 0

    rec=trend["recent"]; prev=trend["previous"]
    lines=[
        "📅 WEEKLY COACH REPORT",
        "",
        f"Последний блок: {rec['games']} партий",
        f"Ошибок на партию: {rec['errors_pg']:.2f}",
        f"Зевков на партию: {rec['blunders_pg']:.2f}",
    ]
    if prev["games"]:
        lines += [
            f"Предыдущий блок: {prev['games']} партий",
            f"Раньше ошибок на партию: {prev['errors_pg']:.2f}",
            trend["direction"],
        ]
    else:
        lines.append(trend["direction"])

    lines += [
        "",
        f"Слабая фаза сейчас: {weak}",
        f"Дебют с наибольшим числом ошибок: {worst}",
        "",
        f"Тренировки за 7 дней: {train7['attempts']} попыток • точность {acc7:.0f}% • сессий {train7['sessions']}",
        f"Тренировки за 30 дней: {train30['attempts']} попыток • сессий {train30['sessions']}",
        "",
    ]

    if phase:
        lines.append("🎯 Цель следующего блока:")
        if weak.lower().startswith("деб"):
            lines.append("Повтори проблемные дебютные позиции и Repertoire Drill.")
        elif "энд" in weak.lower():
            lines.append("Сыграй 3–5 позиций в Endgame Coach Pro.")
        else:
            lines.append(f"Перед каждым ходом уделяй отдельную проверку фазе «{weak}» и повтори ошибки из Puzzle Lab.")
    else:
        lines.append("🎯 Цель: накопить ещё несколько проанализированных партий для устойчивого вывода.")

    lines += ["","Метрики GameCoach — тренировочные показатели, а не Elo или Chess.com Accuracy."]
    return "\n".join(lines)



def fair_candidate_label(loss_cp):
    """GameCoach candidate quality bands; not Chess.com labels."""
    loss_cp = max(0, float(loss_cp))
    if loss_cp <= 20: return "⭐ практически лучший"
    if loss_cp <= 50: return "✅ очень хороший"
    if loss_cp <= 100: return "👍 играбельный"
    if loss_cp <= 200: return "⚠ заметно слабее"
    return "❌ серьёзно уступает"


def score_cp_for_color(info, color):
    try:
        return int(info["score"].pov(color).score(mate_score=100000) or 0)
    except Exception:
        return 0


def load_training_stats():
    global training_stats
    try:
        if os.path.exists(TRAINING_FILE):
            with open(TRAINING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                training_stats = data if isinstance(data, dict) else {}
        else:
            training_stats = {}
    except Exception:
        training_stats = {}


def save_training_stats():
    try:
        with open(TRAINING_FILE, "w", encoding="utf-8") as f:
            json.dump(training_stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_training_record(item):
    key = training_key(item)
    rec = training_stats.get(key)
    if not isinstance(rec, dict):
        rec = {
            "attempts": 0,
            "correct": 0,
            "wrong": 0,
            "streak": 0,
            "last_seen": 0,
            "next_due": 0
        }
        training_stats[key] = rec
    return rec


def mark_training_result(item, correct):
    db_log_training_attempt(item, correct)
    rec = get_training_record(item)
    now = int(time.time())
    rec["attempts"] = int(rec.get("attempts", 0)) + 1
    rec["last_seen"] = now

    if correct:
        rec["correct"] = int(rec.get("correct", 0)) + 1
        rec["streak"] = int(rec.get("streak", 0)) + 1
        # 10 min -> 1 day -> 3 days -> 7 days -> 14 days
        intervals = [600, 86400, 259200, 604800, 1209600]
        interval = intervals[min(rec["streak"] - 1, len(intervals) - 1)]
        rec["next_due"] = now + interval
    else:
        rec["wrong"] = int(rec.get("wrong", 0)) + 1
        rec["streak"] = 0
        rec["next_due"] = now + 300

    save_training_stats()
    try:
        refresh_dashboard()
    except Exception:
        pass


def training_priority(item):
    rec = get_training_record(item)
    now = int(time.time())
    due = int(rec.get("next_due", 0)) <= now
    wrong = int(rec.get("wrong", 0))
    attempts = int(rec.get("attempts", 0))
    streak = int(rec.get("streak", 0))
    # Due first, then troublesome/new positions.
    return (0 if due else 1, -wrong, attempts, streak)


def sort_training_positions():
    global training_positions
    training_positions.sort(key=training_priority)


def due_training_count():
    now = int(time.time())
    return sum(
        1 for item in training_positions
        if int(get_training_record(item).get("next_due", 0)) <= now
    )


def training_progress_text(item=None):
    total = len(training_positions)
    due = due_training_count() if total else 0
    if item is None:
        return f"На повторение: {due} • Всего задач: {total}"
    rec = get_training_record(item)
    return (
        f"Повторение: {due}/{total}   •   "
        f"Серия: {rec.get('streak', 0)}   •   "
        f"Верно: {rec.get('correct', 0)}/{rec.get('attempts', 0)}"
    )


def exit_training():
    global training_active, training_selected_square, training_dragging
    training_active = False
    training_selected_square = None
    training_dragging = False
    training_status.configure(text="Тренировка завершена. Можно вернуться к разбору партии.")
    if analysed_moves:
        show_current_position()


def start_due_training():
    global training_active, training_index, training_session_correct, training_session_wrong
    if not training_positions:
        messagebox.showinfo("GameCoach", "Сначала создай профиль по последним партиям.")
        return

    sort_training_positions()
    now = int(time.time())
    due_indexes = [
        i for i, item in enumerate(training_positions)
        if int(get_training_record(item).get("next_due", 0)) <= now
    ]
    training_index = due_indexes[0] if due_indexes else 0
    training_session_correct = 0
    training_session_wrong = 0
    training_active = True
    show_training_position()



# ============================================================
# VISUAL COACH
# ============================================================

def show_threat():
    """Show the opponent's strongest first reply after the selected move."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return

    data = analysed_moves[current_ply_index]
    before = chess.Board(data["fen"])
    played = data["move"]
    after = before.copy()
    after.push(played)

    # We only stored the SAN variation from before in older data,
    # so re-use the best move as a useful green reference and the played move as context.
    draw_board(before, last_move=None, best_move=data["best_move"])

    motif_notes, squares = detect_tactical_motif(before, played, [])
    training_status.configure(
        text="👁 На доске зелёной стрелкой показан лучший ход из позиции перед ошибкой."
    )


def show_best_move_visual():
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return
    data = analysed_moves[current_ply_index]
    before = chess.Board(data["fen"])
    draw_board(before, best_move=data["best_move"])
    training_status.configure(
        text=f"⭐ Лучший ход: {data['best_san']}. Попробуй понять идею до просмотра линии."
    )



def _coach_piece_name(piece):
    if not piece:
        return "фигура"
    return {
        chess.PAWN: "пешка",
        chess.KNIGHT: "конь",
        chess.BISHOP: "слон",
        chess.ROOK: "ладья",
        chess.QUEEN: "ферзь",
        chess.KING: "король",
    }.get(piece.piece_type, "фигура")


def _best_reply_from_pv(data):
    pv = data.get("pv_uci") or []
    if len(pv) < 2:
        return None
    try:
        before = chess.Board(data["fen"])
        first = chess.Move.from_uci(pv[0])
        if first not in before.legal_moves:
            return None
        before.push(first)
        reply = chess.Move.from_uci(pv[1])
        return reply if reply in before.legal_moves else None
    except Exception:
        return None


def show_tactical_map():
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach", "Сначала выбери проанализированный ход.")
        return

    data = analysed_moves[current_ply_index]
    before = chess.Board(data["fen"])
    arrows = []

    if data.get("move"):
        arrows.append((data["move"], "#E65A5A", 5))

    if data.get("best_move"):
        arrows.append((data["best_move"], "#35C878", 8))

    reply = _best_reply_from_pv(data)
    if reply:
        arrows.append((reply, "#F0A64A", 5))

    draw_board(before, extra_arrows=arrows)

    legend = (
        "🗺 Карта позиции:  🟢 лучший ход   🔴 твой ход"
        + ("   🟠 сильный ответ соперника" if reply else "")
    )
    training_status.configure(text=legend)

    analysis_text.configure(state="normal")
    analysis_text.delete("1.0", "end")
    map_text = (
        "🗺 КАРТА ПОЗИЦИИ\n\n"
        "Зелёная стрелка показывает лучший ход.\n"
        "Красная — ход, сыгранный в партии.\n"
    )
    if reply:
        map_text += "Оранжевая — сильный ответ соперника в главной линии Stockfish.\n"
    map_text += (
        "\nСначала сравни направления стрелок глазами. "
        "Попробуй понять, какая фигура активируется, что защищается "
        "и какую угрозу создаёт лучший ход."
    )
    analysis_text.insert("1.0", map_text)
    analysis_text.configure(state="disabled")



def detect_position_lessons(before, played, best_move, mover_color):
    """Short coach tags for a position. Heuristic labels, not engine-certified motifs."""
    lessons = []
    try:
        after = before.copy()
        after.push(played)
        moved = after.piece_at(played.to_square)

        if moved:
            enemy_attackers = list(after.attackers(not mover_color, played.to_square))
            own_defenders = list(after.attackers(mover_color, played.to_square))
            if enemy_attackers and not own_defenders:
                lessons.append("незащищённая фигура")

        if before.gives_check(played):
            lessons.append("форсированный шах")
        if before.is_capture(played):
            lessons.append("расчёт размена")

        if best_move is not None:
            if before.gives_check(best_move) and not before.gives_check(played):
                lessons.append("пропущенный шах")
            if before.is_capture(best_move) and not before.is_capture(played):
                lessons.append("пропущенное взятие")

            best_board = before.copy()
            best_board.push(best_move)
            # Simple fork heuristic: moved piece attacks 2+ valuable enemy pieces.
            pc = best_board.piece_at(best_move.to_square)
            if pc:
                valuable = 0
                for sq in best_board.attacks(best_move.to_square):
                    target = best_board.piece_at(sq)
                    if target and target.color != mover_color and target.piece_type in (
                        chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING
                    ):
                        valuable += 1
                if valuable >= 2:
                    lessons.append("двойное нападение / вилка")

        if get_phase(before) == "Дебют":
            piece = before.piece_at(played.from_square)
            if piece and piece.piece_type == chess.QUEEN and before.fullmove_number <= 8:
                lessons.append("ранний выход ферзя")
    except Exception:
        pass

    return lessons[:3] or ["проверка ответа соперника"]


def add_current_error_to_repetition():
    """Save the current analysed mistake into the spaced-repetition pool."""
    global training_positions
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return
    data = analysed_moves[current_ply_index]
    if not data.get("best_move"):
        return

    item = {
        "fen": data["fen"],
        "best_move": data["best_move"].uci(),
        "played_move": data["move"].uci(),
        "played_san": data["san"],
        "best_san": data["best_san"],
        "loss": data["loss"],
        "phase": data["phase"],
        "user_color": "white" if data["mover_color"] == chess.WHITE else "black",
        "game_index": 1,
    }

    key = training_key(item)
    if not any(training_key(x) == key for x in training_positions):
        training_positions.append(item)
    persist_training_item(item, "manual-repeat")
    rec = get_training_record(item)
    rec["next_due"] = int(time.time()) + 300
    save_training_stats()
    training_status.configure(text="🔁 Позиция добавлена в повторение. Вернёмся к ней позже.")


def think_first_current_position():
    global training_active, training_positions, training_index, player_color_global

    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach", "Сначала выбери ход, который хочешь переиграть.")
        return

    data = analysed_moves[current_ply_index]
    if data.get("best_move") is None:
        return

    training_positions = [{
        "fen": data["fen"],
        "best_move": data["best_move"].uci(),
        "played_move": data["move"].uci(),
        "played_san": data["san"],
        "best_san": data["best_san"],
        "loss": data["loss"],
        "phase": data["phase"],
        "user_color": "white" if data["mover_color"] == chess.WHITE else "black",
        "game_index": 1,
        "think_first": True,
        "original_index": current_ply_index,
    }]
    training_index = 0
    training_active = True
    player_color_global = data["mover_color"]

    eval_label.configure(text="Оценка: скрыта — сначала реши позицию")
    best_label.configure(text="Лучший ход: скрыт")
    variation_label.configure(text="Линия Stockfish:\nскрыта")

    analysis_title.configure(text=f"🧠 Подумай сам • {data['phase']}")
    analysis_text.configure(state="normal")
    analysis_text.delete("1.0", "end")
    analysis_text.insert(
        "1.0",
        "🧠 СНАЧАЛА ПОДУМАЙ САМ\n\n"
        "Позиция возвращена к моменту перед твоим ходом.\n\n"
        "1. Найди шахи.\n"
        "2. Проверь взятия.\n"
        "3. Посмотри, какие фигуры висят.\n"
        "4. Найди самый неприятный ответ соперника.\n"
        "5. Только после этого сделай свой ход на доске.\n\n"
        "Stockfish и лучший вариант пока скрыты."
    )
    analysis_text.configure(state="disabled")

    board = chess.Board(data["fen"])
    draw_board(board)
    training_status.configure(
        text="🧠 Твой ход. Перетащи фигуру. Подсказка не показывается до попытки."
    )


def _reveal_think_first_result(item, correct):
    idx = item.get("original_index")
    if idx is None or idx < 0 or idx >= len(analysed_moves):
        return
    data = analysed_moves[idx]

    if not correct:
        analysis_title.configure(text="🧠 Ещё одна попытка")
        return

    eval_label.configure(text=f"Оценка: {data['before_eval']} → {data['after_eval']}")
    best_label.configure(text="Лучший ход: " + data["best_san"])
    variation_label.configure(text="Линия Stockfish:\n" + data["variation"])
    analysis_title.configure(text="✅ Ты нашёл лучший ход")

    reasons = explain_best_move_difference(
        chess.Board(data["fen"]), data["move"], data["best_move"], data["mover_color"]
    )

    text = (
        "✅ РЕЗУЛЬТАТ\n\n"
        f"Ты выбрал {data['best_san']} — тот же ход, который Stockfish ставит первым.\n\n"
        "💡 ПОЧЕМУ ЭТО ВАЖНО\n\n"
    )
    if reasons:
        text += "\n".join("• " + r for r in reasons)
    else:
        text += "• Лучший ход лучше сохраняет оценку и ограничивает ответ соперника."
    text += (
        "\n\n🎯 ЗАПОМНИ\n\n"
        "Перед критическим ходом сравни хотя бы два кандидата, "
        "а затем проверь лучший ответ соперника."
    )
    lessons = detect_position_lessons(
        chess.Board(data["fen"]), data["move"], data["best_move"], data["mover_color"]
    )
    text += "\n\n🧩 ТЕМА ПОЗИЦИИ\n\n" + " • ".join(lessons)
    render_coach_text(analysis_text, text)
    add_current_error_to_repetition()


def enhanced_why_current_move():
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach", "Сначала выбери проанализированный ход.")
        return

    data = analysed_moves[current_ply_index]
    before = chess.Board(data["fen"])
    played = data["move"]
    best = data.get("best_move")
    after = before.copy()
    after.push(played)

    reasons = explain_best_move_difference(before, played, best, data["mover_color"]) if best else []
    motif_pv = data.get("pv") or ([best] if best else [])
    motif_notes, _motif_squares = detect_tactical_motif(before, played, motif_pv)

    played_piece = before.piece_at(played.from_square)
    attacked_after = list(after.attackers(not data["mover_color"], played.to_square))
    defended_after = list(after.attackers(data["mover_color"], played.to_square))

    verdict = (
        "Этот ход совпадает с первым выбором Stockfish."
        if played == best else
        f"Stockfish предпочитает {data['best_san']}. Потеря оценки около {data['loss']/100:.2f}."
    )

    observations = []
    if before.gives_check(played):
        observations.append("Твой ход даёт шах и заставляет соперника реагировать.")
    if before.is_capture(played):
        observations.append("Это взятие, поэтому важно досчитать всю цепочку разменов.")
    if attacked_after and not defended_after:
        observations.append(
            f"{_coach_piece_name(played_piece).capitalize()} после хода оказывается под ударом без прямой защиты."
        )
    if not observations:
        observations.append(
            "Главный вопрос здесь — не только куда идёт фигура, а что меняется после хода: "
            "защита, активность и возможный ответ соперника."
        )

    win = ctk.CTkToplevel(root)
    win.title("Почему этот ход?")
    win.geometry("650x640")
    win.transient(root)

    shell = ctk.CTkScrollableFrame(win, corner_radius=18)
    shell.pack(fill="both", expand=True, padx=14, pady=14)

    ctk.CTkLabel(
        shell, text=f"❓ Почему {data['best_san']} лучше?",
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
    ).pack(anchor="w", padx=10, pady=(10, 4))

    ctk.CTkLabel(
        shell,
        text=f"Позиция перед {data['move_label']} {data['san']} • {data['phase']}",
        text_color="#98A3B1"
    ).pack(anchor="w", padx=10, pady=(0, 14))

    def card(title, body):
        f = ctk.CTkFrame(shell, corner_radius=14, fg_color="#171D25")
        f.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(
            f, text=title,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 5))
        ctk.CTkLabel(
            f, text=body, justify="left", wraplength=560,
            font=ctk.CTkFont(size=14), text_color="#D6DCE4"
        ).pack(anchor="w", padx=14, pady=(0, 13))

    card("📊 Вердикт", verdict)
    card("🔎 Что произошло", "\n".join("• " + x for x in observations))

    if reasons:
        card("⭐ Почему лучший ход сильнее", "\n".join("• " + x for x in reasons))
    else:
        card(
            "⭐ Идея лучшего хода",
            "Лучший ход сохраняет больше возможностей и лучше выдерживает "
            "сильнейший ответ соперника."
        )

    reply = _best_reply_from_pv(data)
    if reply and best:
        b = before.copy()
        try:
            b.push(best)
            reply_san = b.san(reply)
        except Exception:
            reply_san = reply.uci()
        card(
            "⚔ Что ответит соперник",
            f"В главной линии после {data['best_san']} Stockfish рассматривает {reply_san}. "
            "Именно такие ответы нужно проверять перед выбором хода."
        )

    if motif_notes:
        card("🧩 Тактическая тема", "\n".join("• " + x for x in motif_notes))

    card(
        "🎯 Запомни",
        "Перед ходом задай себе три вопроса: что угрожает соперник, "
        "какие у меня есть форсированные ходы и что изменится в защите фигур после моего хода."
    )

    ctk.CTkButton(
        shell, text="🗺 Показать на доске",
        command=lambda: (win.destroy(), show_tactical_map()),
        height=40
    ).pack(fill="x", padx=8, pady=(10, 6))

    ctk.CTkButton(
        shell, text="🧠 Решить самому",
        command=lambda: (win.destroy(), think_first_current_position()),
        height=40
    ).pack(fill="x", padx=8, pady=(0, 14))


def solve_current_position():
    global training_active, training_positions, training_index
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return

    data = analysed_moves[current_ply_index]
    if data["best_move"] is None:
        return

    training_positions = [{
        "fen": data["fen"],
        "best_move": data["best_move"].uci(),
        "played_move": data["move"].uci(),
        "played_san": data["san"],
        "best_san": data["best_san"],
        "loss": data["loss"],
        "phase": data["phase"],
        "user_color": "white" if data["mover_color"] == chess.WHITE else "black",
        "game_index": 1
    }]
    training_index = 0
    training_active = True
    show_training_position()


def why_current_move():
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach", "Сначала выбери проанализированный ход.")
        return

    data = analysed_moves[current_ply_index]
    before = chess.Board(data["fen"])
    after = before.copy()
    after.push(data["move"])

    msg = []
    if data["move"] == data["best_move"]:
        msg.append("Этот ход совпадает с первым выбором Stockfish.")
    else:
        msg.append(
            f"Stockfish предпочитает {data['best_san']}; разница оценки примерно {data['loss']/100:.2f}."
        )

    if before.is_capture(data["move"]):
        msg.append("Это взятие: важно считать не первое взятие, а всю цепочку ответов.")
    if after.is_check():
        msg.append("Ход даёт шах и поэтому ограничивает ответы соперника.")

    moved = after.piece_at(data["move"].to_square)
    if moved:
        attackers = list(after.attackers(not moved.color, data["move"].to_square))
        defenders = list(after.attackers(moved.color, data["move"].to_square))
        if attackers and not defenders:
            msg.append(
                f"После хода фигура на {chess.square_name(data['move'].to_square)} находится под ударом и не имеет прямой защиты."
            )

    if data["best_move"] is not None and data["move"] != data["best_move"]:
        reasons = explain_best_move_difference(
            before, data["move"], data["best_move"], data["mover_color"]
        )
        if reasons:
            msg.append("Почему лучший ход сильнее:\n• " + "\n• ".join(reasons))

    if data["loss"] >= 70:
        msg.append(
            "Практический урок: перед ходом отдельно проверь лучший форсированный ответ соперника."
        )
    else:
        msg.append(
            "Практический урок: сравни свой план с лучшим ходом и найди, какая фигура становится активнее."
        )

    messagebox.showinfo("Почему этот ход?", "\n\n".join(msg))




# ============================================================
# SETTINGS / STARTUP
# ============================================================

def load_app_settings():
    global app_settings, stockfish_path
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                app_settings.update(data)
    except Exception:
        pass

    saved = str(app_settings.get("stockfish_path", "") or "")
    if saved and os.path.exists(saved):
        stockfish_path = saved


def save_app_settings():
    try:
        app_settings["stockfish_path"] = stockfish_path
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(app_settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def find_stockfish_automatically():
    candidates = []
    base = _program_dir()
    runtime_base = getattr(sys, "_MEIPASS", base)

    names = [
        "stockfish.exe",
        "stockfish-windows-x86-64-avx2.exe",
        "stockfish-windows-x86-64.exe",
        "stockfish_17_x64_avx2.exe",
        "stockfish_17_x64.exe",
        "stockfish-windows-x86-64-sse41-popcnt.exe",
    ]

    for name in names:
        candidates.extend([
            os.path.join(base, name),
            os.path.join(base, "stockfish", name),
            os.path.join(base, "engine", name),
            os.path.join(runtime_base, name),
            os.path.join(runtime_base, "stockfish", name),
            os.path.join(runtime_base, "engine", name),
        ])

    home = os.path.expanduser("~")
    for folder in ("Downloads", "Desktop", "Documents"):
        root_dir = os.path.join(home, folder)
        if os.path.isdir(root_dir):
            try:
                for root_dir2, dirs, files in os.walk(root_dir):
                    if os.path.relpath(root_dir2, root_dir).count(os.sep) > 3:
                        dirs[:] = []
                        continue
                    for fn in files:
                        low = fn.lower()
                        if low.startswith("stockfish") and low.endswith(".exe"):
                            candidates.append(os.path.join(root_dir2, fn))
            except Exception:
                pass

    for cmd in ("stockfish", "stockfish.exe"):
        p = shutil.which(cmd)
        if p:
            candidates.append(p)

    seen = set()
    for path in candidates:
        if not path:
            continue
        ap = os.path.abspath(path)
        key = os.path.normcase(ap)
        if key in seen:
            continue
        seen.add(key)
        if os.path.isfile(ap):
            return ap
    return ""


def ensure_stockfish_path(show_message=True):
    global stockfish_path
    if stockfish_path and os.path.exists(stockfish_path):
        return True

    found = find_stockfish_automatically()
    if found:
        stockfish_path = found
        app_settings["stockfish_path"] = found
        save_app_settings()
        try:
            stockfish_button.configure(text="✓ Stockfish найден")
        except Exception:
            pass
        return True

    if show_message:
        messagebox.showinfo(
            "Stockfish",
            "GameCoach не нашёл Stockfish автоматически.\n\n"
            "Нажми кнопку Stockfish и выбери файл .exe один раз. "
            "Путь будет сохранён."
        )
    return False


def launch_stockfish_engine():
    """Start Stockfish without flashing a console window on Windows."""
    kwargs = {}
    if os.name == "nt":
        try:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        except Exception:
            pass
    return chess.engine.SimpleEngine.popen_uci(stockfish_path, **kwargs)


def open_engine():
    if not ensure_stockfish_path():
        return None
    try:
        engine = launch_stockfish_engine()
        try:
            engine.configure({"Threads": 2, "Hash": 128})
        except Exception:
            pass
        return engine
    except Exception as exc:
        messagebox.showerror(
            "Stockfish",
            f"Не удалось запустить Stockfish.\n\n{exc}\n\n"
            "Выбери другой файл Stockfish .exe."
        )
        return None



def open_about_window():
    win=ctk.CTkToplevel(root)
    win.title("О GameCoach")
    win.geometry("560x480")
    win.transient(root)
    wrap=ctk.CTkFrame(win,corner_radius=18)
    wrap.pack(fill="both",expand=True,padx=18,pady=18)

    ctk.CTkLabel(
        wrap,text="♟ GameCoach",
        font=ctk.CTkFont(family="Segoe UI",size=29,weight="bold")
    ).pack(anchor="w",padx=22,pady=(22,2))
    ctk.CTkLabel(
        wrap,text=f"Public Release {APP_VERSION}",
        text_color=GC_ACCENT,font=ctk.CTkFont(size=15,weight="bold")
    ).pack(anchor="w",padx=22,pady=(0,14))

    text=(
        "Персональный шахматный тренер для анализа собственных партий, "
        "повторения ошибок и адаптивной тренировки.\\n\\n"
        "Оценки качества ходов и тренировочные показатели GameCoach являются "
        "собственными метриками приложения и не являются Chess.com Accuracy или рейтингом Elo.\\n\\n"
        "GameCoach может использовать Stockfish, установленный вместе с программой, "
        "или выбранный пользователем вручную. Stockfish — отдельный GPLv3-компонент.\\n\\n"
        f"Данные пользователя:\\n{APP_DATA_DIR}"
    )
    ctk.CTkLabel(
        wrap,text=text,wraplength=490,justify="left",
        text_color="#B8C0BC",font=ctk.CTkFont(size=13)
    ).pack(anchor="w",padx=22,pady=(0,18))

    ctk.CTkButton(
        wrap,text="📁 Открыть папку данных",
        command=lambda: os.startfile(APP_DATA_DIR) if os.name=="nt" else None,
        height=40
    ).pack(fill="x",padx=22,pady=4)
    ctk.CTkButton(
        wrap,text="Закрыть",command=win.destroy,
        fg_color="#3D4540",height=38
    ).pack(fill="x",padx=22,pady=(4,18))


def show_settings_window():
    win = ctk.CTkToplevel(root)
    win.title("Настройки GameCoach")
    win.geometry("520x560")
    win.transient(root)
    win.grab_set()

    wrap = ctk.CTkFrame(win, corner_radius=16)
    wrap.pack(fill="both", expand=True, padx=18, pady=18)

    ctk.CTkLabel(
        wrap, text="Настройки",
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
    ).pack(anchor="w", padx=18, pady=(18, 4))

    ctk.CTkLabel(
        wrap,
        text="Настрой скорость анализа и интерфейс под себя.",
        text_color="#9AA4B2"
    ).pack(anchor="w", padx=18, pady=(0, 16))

    def make_slider(title, from_, to, key, steps):
        ctk.CTkLabel(wrap, text=title).pack(anchor="w", padx=18, pady=(10, 4))
        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", padx=18)
        value_label = ctk.CTkLabel(row, text=str(app_settings[key]), width=50)
        value_label.pack(side="right")

        def changed(v):
            iv = int(round(float(v)))
            app_settings[key] = iv
            value_label.configure(text=str(iv))

        slider = ctk.CTkSlider(
            row, from_=from_, to=to, number_of_steps=steps, command=changed
        )
        slider.set(app_settings[key])
        slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

    make_slider("Глубина анализа партии", 6, 18, "engine_depth_single", 12)
    make_slider("Глубина анализа профиля", 5, 14, "engine_depth_profile", 9)
    make_slider("Последних партий для профиля", 5, 40, "recent_games", 35)
    make_slider("Скорость анимации, мс", 150, 1000, "animation_ms", 17)

    ctk.CTkLabel(wrap, text="Объём объяснений").pack(anchor="w", padx=18, pady=(14, 4))
    text_mode_menu = ctk.CTkOptionMenu(
        wrap,
        values=["Коротко", "Обычный", "Подробно"],
        command=lambda value: app_settings.__setitem__("text_mode", value)
    )
    text_mode_menu.set(app_settings.get("text_mode", "Обычный"))
    text_mode_menu.pack(fill="x", padx=18, pady=(0, 4))

    sound_var = tk.BooleanVar(value=bool(app_settings.get("sound", True)))
    ctk.CTkCheckBox(
        wrap, text="Звуки", variable=sound_var,
        command=lambda: app_settings.__setitem__("sound", bool(sound_var.get()))
    ).pack(anchor="w", padx=18, pady=(16, 8))

    ctk.CTkButton(
        wrap, text="🔊 Проверить звук",
        command=test_gamecoach_sound,
        height=36
    ).pack(fill="x", padx=18, pady=(0, 10))

    stock_label = ctk.CTkLabel(
        wrap,
        text=("Stockfish: " + (stockfish_path if stockfish_path else "не выбран")),
        wraplength=450, justify="left", text_color="#AAB4C2"
    )
    stock_label.pack(anchor="w", padx=18, pady=(8, 10))

    def choose_here():
        choose_stockfish()
        stock_label.configure(
            text=("Stockfish: " + (stockfish_path if stockfish_path else "не выбран"))
        )

    ctk.CTkButton(
        wrap, text="Выбрать Stockfish", command=choose_here, height=38
    ).pack(fill="x", padx=18, pady=(0, 8))

    def auto_find():
        ensure_stockfish_path()
        stock_label.configure(
            text=("Stockfish: " + (stockfish_path if stockfish_path else "не найден"))
        )

    ctk.CTkButton(
        wrap, text="Найти Stockfish автоматически", command=auto_find, height=38
    ).pack(fill="x", padx=18, pady=(0, 12))

    def save_close():
        save_app_settings()
        win.destroy()

    ctk.CTkButton(
        wrap, text="Сохранить", command=save_close, height=42
    ).pack(fill="x", padx=18, pady=(8, 18))



# ============================================================
# DASHBOARD
# ============================================================

def load_profile_data():
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def dashboard_metrics():
    profile = load_profile_data()

    games = int(profile.get("games", 0) or 0)
    blunders = int(profile.get("blunders", 0) or 0)
    mistakes = int(profile.get("mistakes", 0) or 0)
    inaccuracies = int(profile.get("inaccuracies", 0) or 0)

    total_errors = blunders + mistakes + inaccuracies
    errors_per_game = (total_errors / games) if games else 0.0

    phase = profile.get("weak_phase", "—") or "—"
    opening = profile.get("worst_opening", "—") or "—"

    due = due_training_count() if training_positions else 0

    return {
        "games": games,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "errors_per_game": errors_per_game,
        "weak_phase": phase,
        "worst_opening": opening,
        "due": due
    }


def refresh_dashboard():
    m = dashboard_metrics()

    dash_games_value.configure(text=str(m["games"]))
    dash_errors_value.configure(text=f'{m["errors_per_game"]:.1f}')
    dash_blunders_value.configure(text=str(m["blunders"]))
    dash_due_value.configure(text=str(m["due"]))

    dash_weak_value.configure(text=str(m["weak_phase"]))
    dash_opening_value.configure(text=str(m["worst_opening"]))

    # Simple progress bar proxy: fewer errors/game => fuller bar.
    score = max(0.0, min(1.0, 1.0 - m["errors_per_game"] / 8.0))
    dash_progress.set(score)
    dash_progress_label.configure(text=f"GameCoach форма: {round(score * 100)}%")

    # Small training summary
    if training_positions:
        dash_training_text.configure(
            text=f"На повторение: {m['due']}   •   Всего задач: {len(training_positions)}"
        )
    else:
        dash_training_text.configure(
            text="Создай профиль по последним партиям, чтобы появились персональные тренировки."
        )


def show_dashboard():
    dashboard_frame.tkraise()
    refresh_dashboard()


def show_workspace():
    workspace_frame.tkraise()



def open_dashboard_window():
    m = dashboard_metrics()

    win = ctk.CTkToplevel(root)
    win.title("Обзор GameCoach")
    win.geometry("820x520")
    win.transient(root)

    shell = ctk.CTkFrame(win, corner_radius=18, fg_color="#11161C")
    shell.pack(fill="both", expand=True, padx=16, pady=16)

    ctk.CTkLabel(
        shell, text="Твой шахматный обзор",
        font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
    ).pack(anchor="w", padx=22, pady=(22, 4))

    ctk.CTkLabel(
        shell,
        text="Последние партии, слабые места и задачи на повторение.",
        text_color="#98A3B1",
        font=ctk.CTkFont(family="Segoe UI", size=13)
    ).pack(anchor="w", padx=22, pady=(0, 18))

    cards = ctk.CTkFrame(shell, fg_color="transparent")
    cards.pack(fill="x", padx=16)

    for i in range(4):
        cards.grid_columnconfigure(i, weight=1)

    def card(col, title, value):
        frame = ctk.CTkFrame(cards, corner_radius=14, fg_color="#1A2028")
        frame.grid(row=0, column=col, sticky="nsew", padx=6)
        ctk.CTkLabel(
            frame, text=title, text_color="#8F9AAA",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkLabel(
            frame, text=str(value),
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", padx=14, pady=(0, 14))

    card(0, "ПАРТИЙ", m["games"])
    card(1, "ОШИБОК / ПАРТИЮ", f'{m["errors_per_game"]:.1f}')
    card(2, "ЗЕВКОВ", m["blunders"])
    card(3, "НА ПОВТОРЕНИЕ", m["due"])

    body = ctk.CTkFrame(shell, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=22, pady=18)
    body.grid_columnconfigure((0, 1), weight=1)

    weak = ctk.CTkFrame(body, corner_radius=14, fg_color="#1A2028")
    weak.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

    ctk.CTkLabel(
        weak, text="Что улучшать",
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(anchor="w", padx=16, pady=(16, 10))

    ctk.CTkLabel(
        weak, text="Слабая фаза", text_color="#8F9AAA"
    ).pack(anchor="w", padx=16)
    ctk.CTkLabel(
        weak, text=str(m["weak_phase"]),
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(anchor="w", padx=16, pady=(2, 12))

    ctk.CTkLabel(
        weak, text="Проблемный дебют", text_color="#8F9AAA"
    ).pack(anchor="w", padx=16)
    ctk.CTkLabel(
        weak, text=str(m["worst_opening"]), wraplength=320,
        justify="left", font=ctk.CTkFont(size=15, weight="bold")
    ).pack(anchor="w", padx=16, pady=(2, 16))

    train = ctk.CTkFrame(body, corner_radius=14, fg_color="#1A2028")
    train.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    ctk.CTkLabel(
        train, text="Тренировка",
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(anchor="w", padx=16, pady=(16, 8))

    ctk.CTkLabel(
        train,
        text=f"На повторение сейчас: {m['due']}\nВсего задач: {len(training_positions)}",
        justify="left", text_color="#B4BDC8"
    ).pack(anchor="w", padx=16, pady=(0, 14))

    ctk.CTkButton(
        train, text="Начать повторение",
        command=lambda: (win.destroy(), start_due_training()),
        height=40
    ).pack(fill="x", padx=16, pady=(0, 8))

    ctk.CTkButton(
        train, text="Обновить профиль",
        command=lambda: (win.destroy(), start_profile_analysis()),
        height=40
    ).pack(fill="x", padx=16, pady=(0, 16))



# ============================================================
# SELF ANALYSIS
# ============================================================


def open_play_vs_stockfish():
    """Play a real game against Stockfish with optional coach tools."""
    if not ensure_stockfish_path():
        return

    win = ctk.CTkToplevel(root)
    win.title("Играть против Stockfish • GameCoach")
    win.geometry("1180x790")
    win.minsize(1050, 700)

    state = {
        "board": chess.Board(),
        "selected": None,
        "human": chess.WHITE,
        "engine": None,
        "thinking": False,
        "last_move": None,
        "last_human_move": None,
        "last_human_before": None,
        "coach_used": False,
        "pending_retry": False,
        "pending_before": None,
        "pending_move": None,
        "pending_loss": 0,
        "human_move_count": 0,
    }

    top = ctk.CTkFrame(win, fg_color="transparent")
    top.pack(fill="x", padx=18, pady=(14, 6))

    ctk.CTkLabel(
        top, text="⚔️ Игра против Stockfish",
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
    ).pack(side="left")

    side_var = tk.StringVar(value="Белыми")
    level_var = tk.StringVar(value="Средний")

    ctk.CTkLabel(top, text="Цвет").pack(side="left", padx=(28, 6))
    side_menu = ctk.CTkOptionMenu(top, values=["Белыми", "Чёрными"], variable=side_var, width=105)
    side_menu.pack(side="left")

    ctk.CTkLabel(top, text="Сила").pack(side="left", padx=(18, 6))
    level_menu = ctk.CTkOptionMenu(
        top, values=["Лёгкий", "Средний", "Сильный", "Очень сильный"],
        variable=level_var, width=135
    )
    level_menu.pack(side="left")

    teaching_var = tk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        top, text="🎓 Учебная партия", variable=teaching_var, width=150
    ).pack(side="left", padx=(18, 4))

    left = ctk.CTkFrame(win, fg_color="transparent")
    left.pack(side="left", fill="both", padx=(18, 8), pady=(8, 18))

    right = ctk.CTkFrame(win, corner_radius=16)
    right.pack(side="right", fill="both", expand=True, padx=(8, 18), pady=(8, 18))

    size = 620
    sqs = size / 8
    canvas = tk.Canvas(left, width=size, height=size, highlightthickness=0)
    canvas.pack()

    status = ctk.CTkLabel(
        left, text="Новая партия", font=ctk.CTkFont(size=14, weight="bold")
    )
    status.pack(pady=(10, 0))

    title = ctk.CTkLabel(
        right, text="Тренер",
        font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
    )
    title.pack(anchor="w", padx=18, pady=(18, 4))

    coach_text = ctk.CTkTextbox(
        right, wrap="word", font=("Segoe UI", 14), corner_radius=12
    )
    coach_text.pack(fill="both", expand=True, padx=18, pady=(6, 10))
    coach_text.insert(
        "1.0",
        "Сыграй партию против Stockfish.\n\n"
        "🔥 «Что угрожает?» анализирует опасности в текущей позиции.\n"
        "🔀 «3 хода» показывает три кандидатных хода с оценкой.\n\n"
        "Совет: сначала думай сам и используй тренера только когда действительно нужен."
    )
    coach_text.configure(state="disabled")

    button_row = ctk.CTkFrame(right, fg_color="transparent")
    button_row.pack(fill="x", padx=18, pady=(0, 8))

    button_row2 = ctk.CTkFrame(right, fg_color="transparent")
    button_row2.pack(fill="x", padx=18, pady=(0, 16))

    preview_refs = []

    def human_flipped():
        return state["human"] == chess.BLACK

    def square_xy(square):
        f = chess.square_file(square)
        r = chess.square_rank(square)
        if human_flipped():
            f = 7 - f
            r = 7 - r
        return f * sqs, (7-r) * sqs

    def event_square(event):
        c = int(event.x // sqs)
        r = int(event.y // sqs)
        if not (0 <= c < 8 and 0 <= r < 8):
            return None
        if human_flipped():
            f = 7-c
            rank = r
        else:
            f = c
            rank = 7-r
        return chess.square(f, rank)

    def set_coach(text):
        coach_text.configure(state="normal")
        coach_text.delete("1.0", "end")
        coach_text.insert("1.0", text)
        coach_text.configure(state="disabled")

    def local_piece_photo(symbol):
        # Shared main-board images are sized for the main board; build local images for 620px board.
        filename = PIECE_MAP.get(symbol)
        if not filename:
            return None
        path = os.path.join(PIECES_FOLDER, filename + ".png")
        if not os.path.exists(path):
            return None
        im = Image.open(path).convert("RGBA")
        im.thumbnail((int(sqs*.90), int(sqs*.90)), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (int(sqs), int(sqs)), (0,0,0,0))
        cell.alpha_composite(im, ((cell.width-im.width)//2, (cell.height-im.height)//2))
        cell = _styled_piece_image(cell, app_settings.get("piece_style", "Wikipedia"))
        photo = ImageTk.PhotoImage(cell)
        preview_refs.append(photo)
        return photo

    def redraw(arrows=None):
        canvas.delete("all")
        preview_refs.clear()
        b = state["board"]
        theme = current_board_theme()
        selected = state["selected"]
        legal_targets = []
        if selected is not None:
            legal_targets = [m.to_square for m in b.legal_moves if m.from_square == selected]

        for row in range(8):
            for col in range(8):
                if human_flipped():
                    f = 7-col
                    rank = row
                else:
                    f = col
                    rank = 7-row
                sq = chess.square(f, rank)
                light = (f+rank)%2 == 1
                fill = theme["light"] if light else theme["dark"]
                if state["last_move"] and sq in (state["last_move"].from_square, state["last_move"].to_square):
                    fill = theme["last_light"] if light else theme["last_dark"]
                x1,y1=col*sqs,row*sqs
                canvas.create_rectangle(x1,y1,x1+sqs,y1+sqs,fill=fill,outline="")
                if sq == selected:
                    canvas.create_rectangle(x1+3,y1+3,x1+sqs-3,y1+sqs-3,
                                            outline=theme["select"],width=4)
                if sq in legal_targets:
                    cx,cy=x1+sqs/2,y1+sqs/2
                    if b.piece_at(sq):
                        canvas.create_oval(cx-28,cy-28,cx+28,cy+28,outline=theme["legal"],width=5)
                    else:
                        canvas.create_oval(cx-8,cy-8,cx+8,cy+8,fill=theme["legal"],outline="")

        # Draw coach arrows before pieces.
        for mv, color, width in (arrows or []):
            x1,y1=square_xy(mv.from_square)
            x2,y2=square_xy(mv.to_square)
            x1+=sqs/2; y1+=sqs/2; x2+=sqs/2; y2+=sqs/2
            canvas.create_line(x1,y1,x2,y2,fill=color,width=width,
                               arrow=tk.LAST,arrowshape=(18,22,9),smooth=True)

        for sq,pc in b.piece_map().items():
            x,y=square_xy(sq)
            photo=local_piece_photo(pc.symbol())
            if photo:
                canvas.create_image(x+sqs/2,y+sqs/2,image=photo)

    def depth_for_level():
        return {"Лёгкий": 5, "Средний": 8, "Сильный": 11, "Очень сильный": 14}.get(level_var.get(), 8)

    def sound_for_move(before, move, after):
        if move.promotion:
            safe_beep("promotion")
        elif before.is_castling(move):
            safe_beep("castle")
        elif after.is_check():
            safe_beep("check")
        elif before.is_capture(move):
            safe_beep("capture")
        else:
            safe_beep("move")

    def game_over_message():
        b=state["board"]
        if not b.is_game_over():
            return False
        result=b.result()
        outcome=b.outcome()
        reason="Партия окончена."
        if outcome:
            term=str(outcome.termination).split(".")[-1].replace("_"," ").title()
            reason=f"Партия окончена: {term}."
        status.configure(text=f"{reason}  Результат {result}")
        set_coach(f"🏁 {reason}\n\nРезультат: {result}\n\nМожно начать новую партию.")
        return True

    def engine_move():
        if game_over_message() or state["board"].turn == state["human"]:
            return
        state["thinking"]=True
        status.configure(text="Stockfish думает…")
        fen=state["board"].fen()
        depth=depth_for_level()

        def worker():
            eng=None
            try:
                eng=launch_stockfish_engine()
                board_copy=chess.Board(fen)
                info=eng.analyse(board_copy,chess.engine.Limit(depth=depth))
                pv=info.get("pv",[])
                mv=pv[0] if pv else None
                def apply():
                    if not win.winfo_exists() or mv is None or state["board"].fen()!=fen:
                        state["thinking"]=False
                        return
                    before=state["board"].copy()
                    state["board"].push(mv)
                    state["last_move"]=mv
                    state["selected"]=None
                    state["thinking"]=False
                    sound_for_move(before,mv,state["board"])
                    redraw()
                    status.configure(text="Твой ход")
                    game_over_message()
                root.after(0,apply)
            except Exception as exc:
                root.after(0,lambda: status.configure(text=f"Ошибка Stockfish: {exc}"))
                state["thinking"]=False
            finally:
                if eng:
                    try: eng.quit()
                    except Exception: pass
        threading.Thread(target=worker,daemon=True).start()

    def accept_pending_move():
        if not state.get("pending_retry"):
            return
        state["pending_retry"] = False
        retry_btn.configure(state="disabled")
        accept_btn.configure(state="disabled")
        status.configure(text="Ход принят • Stockfish думает…")
        if not game_over_message():
            win.after(180, engine_move)

    def retry_pending_move():
        if not state.get("pending_retry") or not state.get("pending_before"):
            return
        try:
            state["board"] = chess.Board(state["pending_before"])
            state["last_move"] = None
            state["selected"] = None
            state["pending_retry"] = False
            retry_btn.configure(state="disabled")
            accept_btn.configure(state="disabled")
            redraw()
            status.configure(text="🧠 Попробуй другой ход")
            set_coach(
                "🧠 ПОДУМАЙ ЕЩЁ РАЗ\n\n"
                "Ход отменён. Лучший ход всё ещё скрыт.\n\n"
                "Проверь:\n"
                "• шахи;\n• взятия;\n• незащищённые фигуры;\n"
                "• самый сильный ответ соперника."
            )
        except Exception:
            pass

    retry_bar = ctk.CTkFrame(right, fg_color="transparent")
    retry_bar.pack(fill="x", padx=18, pady=(0, 8))
    retry_btn = ctk.CTkButton(
        retry_bar, text="↩️ Подумать ещё раз", command=retry_pending_move,
        height=38, state="disabled"
    )
    retry_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
    accept_btn = ctk.CTkButton(
        retry_bar, text="✓ Оставить ход", command=accept_pending_move,
        height=38, state="disabled"
    )
    accept_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

    def after_human_move(before, move):
        state["last_human_before"] = before.fen()
        state["last_human_move"] = move
        state["last_move"] = move
        state["coach_used"] = False
        sound_for_move(before, move, state["board"])
        redraw()

        if game_over_message():
            return

        # Quietly compare the played move with the engine's best move.
        state["thinking"] = True
        status.configure(text="GameCoach проверяет ход…")
        before_fen = before.fen()
        after_fen = state["board"].fen()

        def worker():
            eng = None
            try:
                eng = launch_stockfish_engine()
                b0 = chess.Board(before_fen)
                b1 = chess.Board(after_fen)
                d = max(7, min(11, depth_for_level()))
                info0 = eng.analyse(b0, chess.engine.Limit(depth=d))
                info1 = eng.analyse(b1, chess.engine.Limit(depth=d))
                cp0 = pov_score_cp(info0, state["human"])
                cp1 = pov_score_cp(info1, state["human"])
                loss = max(0, cp0 - cp1)
                best_pv = info0.get("pv", [])
                best = best_pv[0] if best_pv else None

                def apply():
                    state["thinking"] = False
                    if not win.winfo_exists() or state["board"].fen() != after_fen:
                        return

                    # Only interrupt on a meaningful error and when another move exists.
                    if loss >= 120 and best is not None and best != move:
                        state["pending_retry"] = True
                        state["pending_before"] = before_fen
                        state["pending_move"] = move
                        state["pending_loss"] = loss
                        retry_btn.configure(state="normal")
                        accept_btn.configure(state="normal")
                        status.configure(text="⚠️ Здесь есть проблема")
                        set_coach(
                            "⚠️ ЗДЕСЬ ЕСТЬ ПРОБЛЕМА\n\n"
                            "GameCoach заметил заметное ухудшение позиции.\n\n"
                            "Лучший ход намеренно НЕ показывается.\n"
                            "Хочешь подумать ещё раз?\n\n"
                            "Подсказка: найди самый сильный ответ соперника на свой ход."
                        )
                    else:
                        retry_btn.configure(state="disabled")
                        accept_btn.configure(state="disabled")
                        status.configure(text="Ход принят • Stockfish думает…")
                        win.after(160, engine_move)

                root.after(0, apply)
            except Exception:
                state["thinking"] = False
                root.after(0, engine_move)
            finally:
                if eng:
                    try:
                        eng.quit()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    def click(event):
        if state["thinking"] or game_over_message() or state["board"].turn != state["human"]:
            return
        sq=event_square(event)
        if sq is None:
            return
        b=state["board"]
        if state["selected"] is None:
            pc=b.piece_at(sq)
            if pc and pc.color==state["human"]:
                state["selected"]=sq
                redraw()
            return

        from_sq=state["selected"]
        pc=b.piece_at(from_sq)
        candidate=chess.Move(from_sq,sq)
        if pc and pc.piece_type==chess.PAWN and chess.square_rank(sq) in (0,7):
            candidate=chess.Move(from_sq,sq,promotion=chess.QUEEN)

        if candidate in b.legal_moves:
            before=b.copy()

            # Teaching mode: periodically force a thinking checklist before committing.
            if teaching_var.get() and state.get("human_move_count",0) % 4 == 0:
                ok = messagebox.askyesno(
                    "🎓 Учебная партия",
                    "Перед ходом проверь:\n\n"
                    "1. Что угрожает соперник?\n"
                    "2. Какие у тебя шахи и взятия?\n"
                    "3. Какие 2–3 кандидата ты рассмотрел?\n"
                    "4. Какой самый сильный ответ соперника?\n\n"
                    "Ты проверил всё это и хочешь сыграть выбранный ход?",
                    parent=win
                )
                if not ok:
                    state["selected"]=None
                    redraw()
                    status.configure(text="🧠 Хорошо — подумай ещё")
                    return

            b.push(candidate)
            state["human_move_count"]=state.get("human_move_count",0)+1
            state["selected"]=None
            after_human_move(before,candidate)
        else:
            pc2=b.piece_at(sq)
            state["selected"]=sq if pc2 and pc2.color==state["human"] else None
            redraw()

    canvas.bind("<Button-1>",click)

    def analyse_current(mode):
        if state["thinking"]:
            return
        fen=state["board"].fen()
        state["thinking"]=True
        status.configure(text="Тренер анализирует…")

        def worker():
            eng=None
            try:
                eng=launch_stockfish_engine()
                b=chess.Board(fen)
                infos=eng.analyse(
                    b, chess.engine.Limit(depth=max(9,depth_for_level())),
                    multipv=3
                )
                if not isinstance(infos,list):
                    infos=[infos]

                rows=[]
                arrows=[]
                for n,info in enumerate(infos[:3],1):
                    pv=info.get("pv",[])
                    if not pv: continue
                    mv=pv[0]
                    score=info["score"].pov(b.turn)
                    mate=score.mate()
                    cp=score.score()
                    val=(f"M{mate:+d}" if mate is not None else
                         (f"{(cp or 0)/100:+.2f}" if cp is not None else "—"))
                    try: san=b.san(mv)
                    except Exception: san=mv.uci()
                    line=pv_to_san(b,pv,5)
                    rows.append((n,san,val,line,mv))
                    colors=["#35C878","#4CA7FF","#B58AF3"]
                    arrows.append((mv,colors[n-1],7 if n==1 else 5))

                def apply():
                    state["thinking"]=False
                    if not win.winfo_exists() or state["board"].fen()!=fen:
                        return
                    if mode=="candidates":
                        text="🔀 3 КАНДИДАТНЫХ ХОДА\n\n"
                        for n,san,val,line,mv in rows:
                            text+=f"{n}. {san}   оценка {val}\n   {line}\n\n"
                        text+=("Сравни не только цифры. Посмотри, какой ход создаёт темп, "
                               "улучшает худшую фигуру или ограничивает ответ соперника.")
                        set_coach(text)
                        redraw(arrows)
                    else:
                        # Threats: analyse opponent's tactical resources conceptually and visually.
                        bnow=state["board"]
                        danger=[]
                        attacked=[]
                        for sq,pc in bnow.piece_map().items():
                            if pc.color==state["human"]:
                                attackers=list(bnow.attackers(not state["human"],sq))
                                defenders=list(bnow.attackers(state["human"],sq))
                                if attackers and (not defenders or pc.piece_type in (chess.QUEEN,chess.ROOK)):
                                    attacked.append((sq,pc,len(attackers),len(defenders)))
                        checks=[]
                        for mv in bnow.legal_moves:
                            if bnow.gives_check(mv):
                                checks.append(mv)
                        if bnow.turn==state["human"]:
                            danger.append("Сейчас твой ход: проверь, что соперник сможет сделать после твоего решения.")
                        if attacked:
                            names=[]
                            for sq,pc,a,d in attacked[:5]:
                                names.append(f"{_coach_piece_name(pc)} на {chess.square_name(sq)}")
                            danger.append("Под давлением: "+", ".join(names)+".")
                        if checks:
                            danger.append(f"В позиции есть {len(checks)} доступных шаха/шахов для стороны, которая ходит.")
                        if rows:
                            danger.append(f"Самый сильный текущий кандидат движка: {rows[0][1]}.")
                        if not danger:
                            danger.append("Явной немедленной тактической угрозы эвристика не нашла.")
                        set_coach("🔥 ЧТО УГРОЖАЕТ?\n\n"+"\n\n".join("• "+x for x in danger)+
                                  "\n\nВажно: это подсказка тренера, а не гарантия отсутствия тактики.")
                        redraw(arrows[:1] if rows else [])
                    status.configure(text="Твой ход" if state["board"].turn==state["human"] else "Ход Stockfish")
                root.after(0,apply)
            except Exception as exc:
                root.after(0,lambda e=str(exc): status.configure(text=f"Ошибка анализа: {e}"))
                state["thinking"]=False
            finally:
                if eng:
                    try: eng.quit()
                    except Exception: pass
        threading.Thread(target=worker,daemon=True).start()

    def new_game():
        state["board"]=chess.Board()
        state["selected"]=None
        state["last_move"]=None
        state["human"]=chess.WHITE if side_var.get()=="Белыми" else chess.BLACK
        state["thinking"]=False
        state["pending_retry"]=False
        state["pending_before"]=None
        retry_btn.configure(state="disabled")
        accept_btn.configure(state="disabled")
        redraw()
        set_coach(
            "Новая партия началась.\n\n"
            "Играй самостоятельно. Если застрял, используй «Что угрожает?» "
            "или сравни три кандидатных хода."
        )
        status.configure(text="Твой ход" if state["human"]==chess.WHITE else "Stockfish начинает…")
        if state["human"]==chess.BLACK:
            win.after(250,engine_move)

    ctk.CTkButton(
        button_row, text="🔥 Что угрожает?",
        command=lambda: analyse_current("threats"), height=40
    ).pack(side="left", fill="x", expand=True, padx=(0,5))

    ctk.CTkButton(
        button_row, text="🔀 3 хода",
        command=lambda: analyse_current("candidates"), height=40
    ).pack(side="left", fill="x", expand=True, padx=(5,0))

    ctk.CTkButton(
        button_row2, text="🔄 Новая партия",
        command=new_game, height=40
    ).pack(side="left", fill="x", expand=True, padx=(0,5))

    ctk.CTkButton(
        button_row2, text="🏳 Сдаться",
        command=lambda: (
            status.configure(text="Партия завершена"),
            set_coach("🏳 Ты завершил эту тренировочную партию. Нажми «Новая партия», чтобы сыграть ещё.")
        ),
        height=40
    ).pack(side="left", fill="x", expand=True, padx=(5,0))

    def close():
        win.destroy()
    win.protocol("WM_DELETE_WINDOW",close)
    new_game()


def open_self_analysis():
    win = ctk.CTkToplevel(root)
    win.title("Самостоятельный анализ")
    win.geometry("1120x760")

    state = {
        "board": chess.Board(),
        "selected": None,
        "engine": None,
        "show_best": tk.BooleanVar(value=False),
        "thinking": False
    }

    left = ctk.CTkFrame(win, fg_color="transparent")
    left.pack(side="left", fill="both", padx=(18, 8), pady=18)

    right = ctk.CTkFrame(win, width=430, corner_radius=16)
    right.pack(side="right", fill="both", expand=True, padx=(8, 18), pady=18)

    size = 600
    sqs = size / 8
    canvas = tk.Canvas(left, width=size, height=size, highlightthickness=0)
    canvas.pack()

    piece_font = ("Segoe UI Symbol", 47)
    symbols = {
        "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
        "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"
    }

    def xy(square):
        f = chess.square_file(square)
        r = chess.square_rank(square)
        return f * sqs, (7-r) * sqs

    def redraw(best_move=None):
        canvas.delete("all")
        board = state["board"]
        selected = state["selected"]
        legal_targets = []
        if selected is not None:
            legal_targets = [m.to_square for m in board.legal_moves if m.from_square == selected]

        for rank in range(8):
            for file in range(8):
                x1 = file * sqs
                y1 = (7-rank) * sqs
                light = (file + rank) % 2 == 1
                theme = current_board_theme()
                fill = theme["light"] if light else theme["dark"]
                sq = chess.square(file, rank)
                if sq == selected:
                    fill = theme["last_light"] if light else theme["last_dark"]
                canvas.create_rectangle(x1, y1, x1+sqs, y1+sqs, fill=fill, outline="")

                if sq in legal_targets:
                    canvas.create_oval(
                        x1+sqs*.42, y1+sqs*.42, x1+sqs*.58, y1+sqs*.58,
                        fill=current_board_theme()["legal"], outline=""
                    )

                pc = board.piece_at(sq)
                if pc:
                    img = piece_images.get(pc.symbol())
                    if img:
                        canvas.create_image(x1+sqs/2, y1+sqs/2, image=img)
                    else:
                        canvas.create_text(
                            x1+sqs/2, y1+sqs/2,
                            text=symbols[pc.symbol()], font=piece_font
                        )

        if best_move is not None:
            x1, y1 = xy(best_move.from_square)
            x2, y2 = xy(best_move.to_square)
            canvas.create_line(
                x1+sqs/2, y1+sqs/2, x2+sqs/2, y2+sqs/2,
                width=7, arrow=tk.LAST, fill="#4C9A6A"
            )

    title = ctk.CTkLabel(
        right, text="🔬 Самостоятельный анализ",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title.pack(anchor="w", padx=18, pady=(18, 4))

    subtitle = ctk.CTkLabel(
        right,
        text="Сначала думай сам. Stockfish можно открыть только тогда, когда ты готов проверить идею.",
        wraplength=390, justify="left", text_color="#9AA4B2"
    )
    subtitle.pack(anchor="w", padx=18, pady=(0, 14))

    eval_out = ctk.CTkLabel(
        right, text="Оценка скрыта",
        font=ctk.CTkFont(size=19, weight="bold")
    )
    eval_out.pack(anchor="w", padx=18, pady=(6, 8))

    lines_box = ctk.CTkTextbox(
        right, height=230, wrap="word",
        font=ctk.CTkFont(family="Segoe UI", size=14),
        corner_radius=12, fg_color="#12161C"
    )
    lines_box.pack(fill="x", padx=18, pady=(0, 12))
    lines_box.insert("1.0", "Сделай ход на доске, затем нажми «Проверить позицию».")
    lines_box.configure(state="disabled")

    def set_text(text):
        lines_box.configure(state="normal")
        lines_box.delete("1.0", "end")
        lines_box.insert("1.0", text)
        lines_box.configure(state="disabled")

    def square_from_event(event):
        file = int(event.x // sqs)
        display_rank = int(event.y // sqs)
        rank = 7 - display_rank
        if 0 <= file < 8 and 0 <= rank < 8:
            return chess.square(file, rank)
        return None

    def click(event):
        sq = square_from_event(event)
        if sq is None:
            return
        board = state["board"]

        if state["selected"] is None:
            pc = board.piece_at(sq)
            if pc and pc.color == board.turn:
                state["selected"] = sq
                redraw()
            return

        frm = state["selected"]
        candidates = [m for m in board.legal_moves if m.from_square == frm and m.to_square == sq]
        if candidates:
            move = candidates[0]
            # Prefer queen promotion.
            queens = [m for m in candidates if m.promotion == chess.QUEEN]
            if queens:
                move = queens[0]
            is_capture = board.is_capture(move)
            is_castle = board.is_castling(move)
            board.push(move)
            state["selected"] = None
            redraw()
            eval_out.configure(text="Оценка скрыта — сначала оцени позицию сам.")
            set_text("Ход сделан. Что изменилось?\\n\\nПроверь шахи, взятия, угрозы и безопасность короля.")
            if move.promotion:
                safe_beep("promotion")
            elif is_castle:
                safe_beep("castle")
            elif board.is_check():
                safe_beep("check")
            elif is_capture:
                safe_beep("capture")
            else:
                safe_beep("move")
        else:
            pc = board.piece_at(sq)
            state["selected"] = sq if pc and pc.color == board.turn else None
            redraw()

    canvas.bind("<Button-1>", click)

    def analyse():
        if state["thinking"]:
            return
        if not ensure_stockfish_path():
            return
        state["thinking"] = True
        eval_out.configure(text="Stockfish думает…")

        fen = state["board"].fen()

        def worker():
            engine = None
            try:
                engine = launch_stockfish_engine()
                board = chess.Board(fen)
                infos = engine.analyse(
                    board,
                    chess.engine.Limit(depth=int(app_settings.get("engine_depth_single", 10))),
                    multipv=3
                )
                results = []
                best_move = None
                score_text = "—"
                for n, info in enumerate(infos, 1):
                    pv = info.get("pv", [])
                    score = info["score"].pov(chess.WHITE).score(mate_score=100000)
                    if n == 1:
                        best_move = pv[0] if pv else None
                        score_text = score_to_text(score or 0)
                    san_line = pv_to_san(board, pv, 7)
                    results.append(f"{n}.  {san_line}")
                text = "ТРИ ЛУЧШИХ ИДЕИ\\n\\n" + "\\n\\n".join(results)

                def done():
                    state["thinking"] = False
                    eval_out.configure(text=f"Оценка: {score_text}")
                    set_text(text)
                    redraw(best_move if state["show_best"].get() else None)

                win.after(0, done)
            except Exception as exc:
                def fail():
                    state["thinking"] = False
                    eval_out.configure(text="Не удалось выполнить анализ")
                    set_text(str(exc))
                win.after(0, fail)
            finally:
                if engine:
                    try:
                        engine.quit()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    buttons = ctk.CTkFrame(right, fg_color="transparent")
    buttons.pack(fill="x", padx=18, pady=4)
    ctk.CTkButton(buttons, text="🔍 Проверить позицию", command=analyse, height=40).pack(side="left", padx=(0, 6))
    ctk.CTkCheckBox(
        buttons, text="Показать лучший ход",
        variable=state["show_best"],
        command=lambda: redraw()
    ).pack(side="left", padx=6)

    def undo():
        if state["board"].move_stack:
            state["board"].pop()
        state["selected"] = None
        redraw()
        eval_out.configure(text="Оценка скрыта")
        set_text("Ход отменён. Попробуй другой вариант.")

    def reset():
        state["board"] = chess.Board()
        state["selected"] = None
        redraw()
        eval_out.configure(text="Оценка скрыта")
        set_text("Начальная позиция. Построй вариант самостоятельно.")

    fen_row = ctk.CTkFrame(right, fg_color="transparent")
    fen_row.pack(fill="x", padx=18, pady=(12, 4))
    fen_entry = ctk.CTkEntry(fen_row, placeholder_text="Вставь FEN позиции")
    fen_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def load_fen():
        try:
            state["board"] = chess.Board(fen_entry.get().strip())
            state["selected"] = None
            redraw()
            eval_out.configure(text="Оценка скрыта")
            set_text("Позиция загружена. Сначала оцени её самостоятельно.")
        except Exception:
            messagebox.showerror("FEN", "Не удалось прочитать эту FEN-позицию.")

    ctk.CTkButton(fen_row, text="Загрузить", command=load_fen, width=90).pack(side="left")

    lower = ctk.CTkFrame(right, fg_color="transparent")
    lower.pack(fill="x", padx=18, pady=8)
    ctk.CTkButton(lower, text="↶ Отменить", command=undo, width=105).pack(side="left", padx=(0, 6))
    ctk.CTkButton(lower, text="↺ Сначала", command=reset, width=105).pack(side="left", padx=6)

    redraw()



# ============================================================
# APPEARANCE
# ============================================================

def show_appearance_window():
    win = ctk.CTkToplevel(root)
    win.title("Оформление GameCoach")
    win.geometry("820x650")
    win.transient(root)

    shell = ctk.CTkFrame(win, corner_radius=18)
    shell.pack(fill="both", expand=True, padx=16, pady=16)

    ctk.CTkLabel(
        shell, text="🎨 Оформление",
        font=ctk.CTkFont(family="Segoe UI", size=25, weight="bold")
    ).pack(anchor="w", padx=20, pady=(18, 3))

    ctk.CTkLabel(
        shell,
        text="Выбери доску и фигуры. Изменения применяются сразу.",
        text_color="#9AA4B2"
    ).pack(anchor="w", padx=20, pady=(0, 14))

    body = ctk.CTkFrame(shell, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=(0, 12))
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=1)

    controls = ctk.CTkFrame(body, corner_radius=14)
    controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    preview_card = ctk.CTkFrame(body, corner_radius=14)
    preview_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    ctk.CTkLabel(
        controls, text="Доска",
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(anchor="w", padx=16, pady=(16, 6))

    board_menu = ctk.CTkOptionMenu(
        controls, values=list(BOARD_THEMES.keys()), height=38
    )
    board_menu.set(app_settings.get("board_theme", "Classic Green"))
    board_menu.pack(fill="x", padx=16, pady=(0, 14))

    ctk.CTkLabel(
        controls, text="Фигуры",
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(anchor="w", padx=16, pady=(4, 6))

    piece_menu = ctk.CTkOptionMenu(
        controls, values=PIECE_STYLES, height=38
    )
    piece_menu.set(app_settings.get("piece_style", "Wikipedia"))
    piece_menu.pack(fill="x", padx=16, pady=(0, 14))

    ctk.CTkLabel(
        controls,
        text="30 вариантов доски • 16 вариантов фигур",
        text_color="#8F9AAA", font=ctk.CTkFont(size=12)
    ).pack(anchor="w", padx=16, pady=(2, 14))

    ctk.CTkLabel(
        controls,
        text="30 собственных палитр доски и 16 визуальных вариантов фигур. Стили фигур создаются локально из открытого базового набора — это не официальные наборы Chess.com или Lichess.",
        wraplength=330, justify="left", text_color="#AAB3BF"
    ).pack(anchor="w", padx=16, pady=(0, 14))

    ctk.CTkLabel(
        preview_card, text="Предпросмотр",
        font=ctk.CTkFont(size=17, weight="bold")
    ).pack(anchor="w", padx=16, pady=(16, 8))

    preview = tk.Canvas(preview_card, width=320, height=320, highlightthickness=0)
    preview.pack(padx=16, pady=(0, 12))

    preview_refs = []

    def draw_preview():
        preview.delete("all")
        preview_refs.clear()
        theme = BOARD_THEMES.get(board_menu.get(), BOARD_THEMES["Classic Green"])
        cell = 80
        sample = [
            ("r",0,0), ("k",2,0), ("p",1,1),
            ("P",2,2), ("N",1,3), ("K",3,3), ("Q",0,3)
        ]
        for r in range(4):
            for c in range(4):
                light = (c + (3-r)) % 2 == 1
                fill = theme["light"] if light else theme["dark"]
                preview.create_rectangle(c*cell, r*cell, (c+1)*cell, (r+1)*cell, fill=fill, outline="")

        # Use current source PNGs and transform them according to selected style.
        for sym, c, r in sample:
            filename = PIECE_MAP[sym]
            path = os.path.join(PIECES_FOLDER, filename + ".png")
            if os.path.exists(path):
                im = Image.open(path).convert("RGBA")
                im.thumbnail((68,68), Image.Resampling.LANCZOS)
                canvas_im = Image.new("RGBA", (72,72), (0,0,0,0))
                canvas_im.alpha_composite(im, ((72-im.width)//2, (72-im.height)//2))
                canvas_im = _styled_piece_image(canvas_im, piece_menu.get())
                photo = ImageTk.PhotoImage(canvas_im)
                preview_refs.append(photo)
                preview.create_image(c*cell+40, r*cell+40, image=photo)

    def apply_choices(_=None):
        app_settings["board_theme"] = board_menu.get()
        app_settings["piece_style"] = piece_menu.get()
        apply_visual_theme()
        draw_preview()

    board_menu.configure(command=apply_choices)
    piece_menu.configure(command=apply_choices)

    ctk.CTkButton(
        controls, text="↺ Вернуть Classic Green",
        command=lambda: (
            board_menu.set("Classic Green"),
            piece_menu.set("Wikipedia"),
            app_settings.__setitem__("board_theme", "Classic Green"),
            app_settings.__setitem__("piece_style", "Wikipedia"),
            apply_visual_theme(),
            draw_preview()
        ),
        height=38
    ).pack(fill="x", padx=16, pady=(4, 8))

    ctk.CTkButton(
        controls, text="Готово", command=win.destroy, height=40
    ).pack(fill="x", padx=16, pady=(0, 16))

    draw_preview()



# ============================================================
# UI
# ============================================================


# ============================================================
# GAMECOACH 18.0 — PERSONAL COACH
# ============================================================

def build_thinking_profile():
    """Build a learning profile from analysed/saved mistakes.
    Motif names are heuristic coaching categories, not certified tactical labels.
    """
    categories = Counter()
    phases = Counter()
    total = 0

    # Best source: saved training positions from the user's own mistakes.
    for item in training_positions:
        try:
            before = chess.Board(item["fen"])
            played = chess.Move.from_uci(item["played_move"])
            best = chess.Move.from_uci(item["best_move"])
            mover = before.turn
            total += 1
            phases[item.get("phase", get_phase(before))] += 1
            for tag in detect_position_lessons(before, played, best, mover):
                categories[tag] += 1

            # Additional thinking-habit signals.
            after = before.copy()
            after.push(played)
            moved = after.piece_at(played.to_square)
            if moved:
                attackers = list(after.attackers(not mover, played.to_square))
                defenders = list(after.attackers(mover, played.to_square))
                if attackers and not defenders:
                    categories["проверка безопасности фигуры"] += 1

            if before.gives_check(best) and not before.gives_check(played):
                categories["поиск форсирующих ходов"] += 1
            if before.is_capture(best) and not before.is_capture(played):
                categories["проверка взятий"] += 1
        except Exception:
            continue

    # Fall back to current analysed game if there is no profile training pool yet.
    if total == 0:
        for d in analysed_moves:
            if d.get("loss", 0) < 70:
                continue
            try:
                before = chess.Board(d["fen"])
                total += 1
                phases[d.get("phase", get_phase(before))] += 1
                for tag in detect_position_lessons(
                    before, d["move"], d.get("best_move"), d["mover_color"]
                ):
                    categories[tag] += 1
            except Exception:
                pass

    top = categories.most_common(5)
    weak_phase = phases.most_common(1)[0][0] if phases else "—"

    # Convert category names into compact coach habits.
    habit_map = {
        "незащищённая фигура": "После своего хода чаще проверяй: «Моя фигура защищена?»",
        "проверка безопасности фигуры": "Перед завершением хода делай короткую проверку атак и защит.",
        "пропущенный шах": "Сначала просматривай все шахи — свои и соперника.",
        "поиск форсирующих ходов": "Начинай расчёт с шахов, взятий и прямых угроз.",
        "пропущенное взятие": "Перед позиционным ходом проверь доступные взятия.",
        "проверка взятий": "Не переходи к плану, пока не проверил тактические взятия.",
        "двойное нападение / вилка": "Отмечай фигуры, которые стоят на одной тактической вилке.",
        "расчёт размена": "Перед разменом считай конечную материальную позицию.",
        "ранний выход ферзя": "В дебюте сначала развивай лёгкие фигуры и короля.",
        "проверка ответа соперника": "После выбора хода спроси: «Какой самый неприятный ответ?»",
    }
    habits = [habit_map.get(name, f"Потренируй тему: {name}.") for name,_ in top[:3]]

    return {
        "total": total,
        "categories": top,
        "weak_phase": weak_phase,
        "habits": habits or [
            "После каждого кандидата проверяй самый сильный ответ соперника.",
            "Ищи шахи, взятия и угрозы до позиционных ходов.",
            "Не открывай Stockfish, пока не сформулировал собственную идею."
        ]
    }


def current_progressive_hints():
    """Three increasingly specific hints without immediately revealing the answer."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return None

    d=analysed_moves[current_ply_index]
    before=chess.Board(d["fen"])
    best=d.get("best_move")
    if best is None:
        return None

    piece=before.piece_at(best.from_square)
    target=before.piece_at(best.to_square)
    hints=[]

    # Level 1: area/goal.
    if before.gives_check(best):
        hints.append("Посмотри на безопасность короля соперника. Здесь есть форсирующая возможность.")
    elif before.is_capture(best):
        hints.append("Проверь все взятия. Одно из них меняет оценку позиции.")
    else:
        hints.append("Сравни активность своих фигур. Какая фигура сейчас может улучшиться с темпом?")

    # Level 2: piece/type, but not destination.
    pname=_coach_piece_name(piece) if piece else "фигура"
    if before.gives_check(best):
        hints.append(f"Ищи шах ходом фигуры: {pname}.")
    elif target:
        hints.append(f"Ключ связан с ходом фигуры «{pname}» и контактом с фигурой соперника.")
    else:
        hints.append(f"Ключевой кандидат начинается ходом фигуры: {pname}.")

    # Level 3: from-square + tactical character, still hide destination when possible.
    from_name=chess.square_name(best.from_square)
    if before.is_capture(best):
        hints.append(f"Посмотри внимательно на фигуру с {from_name}: у неё есть сильное взятие.")
    elif before.gives_check(best):
        hints.append(f"Фигура на {from_name} может дать шах.")
    else:
        hints.append(f"Лучший план начинается движением фигуры с {from_name}. Найди самое активное поле.")

    return d,hints


def open_progressive_hint():
    pack=current_progressive_hints()
    if not pack:
        messagebox.showinfo("Подсказки","Сначала выбери проанализированный ход.")
        return
    d,hints=pack
    win=ctk.CTkToplevel(root)
    win.title("Умная подсказка")
    win.geometry("620x540")
    state={"level":0}

    shell=ctk.CTkFrame(win,corner_radius=18)
    shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="💡 Подсказка без спойлера",
                 font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold")).pack(anchor="w",padx=20,pady=(20,4))
    ctk.CTkLabel(shell,text="Каждый уровень становится конкретнее. Решение показывается только по твоей команде.",
                 text_color="#98A3B1",wraplength=550,justify="left").pack(anchor="w",padx=20,pady=(0,16))
    box=ctk.CTkTextbox(shell,height=250,wrap="word",font=("Segoe UI",15),corner_radius=12)
    box.pack(fill="both",expand=True,padx=20,pady=(0,12))
    status=ctk.CTkLabel(shell,text="Уровень 0/3 • ответ скрыт",text_color="#AAB3BF")
    status.pack(anchor="w",padx=20,pady=(0,8))

    def show_next():
        if state["level"]>=3:
            return
        state["level"]+=1
        box.configure(state="normal")
        if state["level"]==1:
            box.delete("1.0","end")
        box.insert("end",f"Подсказка {state['level']}\n{hints[state['level']-1]}\n\n")
        box.configure(state="disabled")
        status.configure(text=f"Уровень {state['level']}/3 • лучший ход всё ещё скрыт")

    def reveal():
        box.configure(state="normal")
        box.insert("end",f"Решение\n{d['best_san']}\n\nПопробуй объяснить себе, почему этот ход сильнее твоего исходного выбора.")
        box.configure(state="disabled")
        status.configure(text="Решение открыто")

    row=ctk.CTkFrame(shell,fg_color="transparent")
    row.pack(fill="x",padx=20,pady=(0,18))
    ctk.CTkButton(row,text="💡 Следующая подсказка",command=show_next,height=40).pack(side="left",fill="x",expand=True,padx=(0,5))
    ctk.CTkButton(row,text="👁 Показать решение",command=reveal,height=40).pack(side="left",fill="x",expand=True,padx=(5,0))
    show_next()


def open_error_profile():
    p=build_thinking_profile()
    win=ctk.CTkToplevel(root)
    win.title("Профиль мышления")
    win.geometry("760x650")
    shell=ctk.CTkFrame(win,corner_radius=18)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(shell,text="🧠 Профиль твоего мышления",
                 font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,
                 text=f"Основано на {p['total']} сохранённых/проанализированных ошибочных позициях. Категории эвристические.",
                 text_color="#98A3B1",wraplength=680,justify="left").pack(anchor="w",padx=22,pady=(0,16))

    ctk.CTkLabel(shell,text=f"Слабая фаза: {p['weak_phase']}",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=22,pady=(0,10))

    scroll=ctk.CTkScrollableFrame(shell,corner_radius=13)
    scroll.pack(fill="both",expand=True,padx=22,pady=(0,14))

    if p["categories"]:
        ctk.CTkLabel(scroll,text="Чаще встречается",
                     font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=12,pady=(10,6))
        for name,count in p["categories"]:
            card=ctk.CTkFrame(scroll,corner_radius=10)
            card.pack(fill="x",padx=8,pady=4)
            ctk.CTkLabel(card,text=name,font=ctk.CTkFont(size=14,weight="bold")).pack(side="left",padx=12,pady=10)
            ctk.CTkLabel(card,text=f"{count}×",text_color="#AAB3BF").pack(side="right",padx=12)

    ctk.CTkLabel(scroll,text="Что изменить в мышлении",
                 font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=12,pady=(16,6))
    for i,h in enumerate(p["habits"],1):
        ctk.CTkLabel(scroll,text=f"{i}. {h}",wraplength=620,justify="left").pack(anchor="w",padx=12,pady=5)


def personal_training_plan():
    a=adaptive_coach_profile()
    due=due_training_count() if training_positions else 0
    p=build_thinking_profile()
    topics=[name for name,_ in p.get("categories",[])[:3]] or [a["topic"]]
    return {
        "minutes": 15 + min(15,a["target_count"]),
        "repeat": min(a["target_count"],due),
        "mistakes": a["target_count"],
        "calculation": 3 if a["mode"]=="calculation" else (2 if analysed_moves else 0),
        "topics": topics,
        "phase": a["weak_phase"],
        "difficulty": a["difficulty"],
        "mode": a["mode"],
        "reason": a["reason"],
    }



def open_personal_plan():
    plan=personal_training_plan()
    win=ctk.CTkToplevel(root)
    win.title("Персональный план")
    win.geometry("700x620")
    shell=ctk.CTkFrame(win,corner_radius=18)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(shell,text="🎯 Адаптивный персональный план",
                 font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,text=f"Сегодня ~{plan['minutes']} минут • фокус: {plan['mode']} • сложность: {plan['difficulty']}",
                 text_color="#98A3B1").pack(anchor="w",padx=22,pady=(0,16))

    tasks=[
        ("1", "🔁 Повтори старые ошибки", f"{plan['repeat']} позиций, которые пора освежить."),
        ("2", "🧠 Реши свои критические позиции", f"{plan['mistakes']} позиций без немедленного ответа."),
        ("3", "🧩 Расчёт варианта", f"{plan['calculation']} упражнения с продолжением Stockfish."),
        ("4", "💡 Работа над привычкой", "Перед каждым решением проговори: шахи → взятия → угрозы → ответ соперника."),
    ]
    for no,title,desc in tasks:
        card=ctk.CTkFrame(shell,corner_radius=12)
        card.pack(fill="x",padx=22,pady=5)
        ctk.CTkLabel(card,text=f"{no}. {title}",font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=14,pady=(10,2))
        ctk.CTkLabel(card,text=desc,text_color="#AAB3BF",wraplength=600,justify="left").pack(anchor="w",padx=14,pady=(0,10))

    topics=" • ".join(plan["topics"])
    ctk.CTkLabel(shell,text="Главные темы: "+topics,wraplength=620,justify="left",
                 font=ctk.CTkFont(size=14,weight="bold")).pack(anchor="w",padx=22,pady=(12,8))
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=22,pady=(6,18))
    ctk.CTkButton(row,text="▶ Начать тренировку",command=lambda:(win.destroy(),open_daily_session()),height=42).pack(side="left",fill="x",expand=True,padx=(0,5))
    ctk.CTkButton(row,text="🧠 Профиль ошибок",command=open_error_profile,height=42).pack(side="left",fill="x",expand=True,padx=(5,0))


def open_personal_coach():
    p=build_thinking_profile()
    plan=personal_training_plan()
    win=ctk.CTkToplevel(root)
    win.title("Personal Coach")
    win.geometry("820x670")
    shell=ctk.CTkFrame(win,corner_radius=20)
    shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧑‍🏫 Personal Coach",
                 font=ctk.CTkFont(family="Segoe UI",size=28,weight="bold")).pack(anchor="w",padx=24,pady=(22,3))
    ctk.CTkLabel(shell,text="Не просто показывает лучший ход — помогает улучшать способ принятия решений.",
                 text_color="#98A3B1",wraplength=720,justify="left").pack(anchor="w",padx=24,pady=(0,18))

    cards=ctk.CTkFrame(shell,fg_color="transparent");cards.pack(fill="x",padx=18)
    cards.grid_columnconfigure((0,1),weight=1)
    data=[
        ("🧠 Профиль мышления", f"{p['total']} позиций изучено", open_error_profile),
        ("🧠 Adaptive Coach", f"{plan['difficulty']} • ~{plan['minutes']} минут", open_adaptive_coach),
        ("💡 Подсказка", "3 уровня без спойлера", open_progressive_hint),
        ("📊 Прогресс", f"Level {learning_level()} • {learning_profile.get('xp',0)} XP", open_progress_center),
    ]
    for i,(title,desc,cmd) in enumerate(data):
        card=ctk.CTkFrame(cards,corner_radius=14)
        card.grid(row=i//2,column=i%2,sticky="nsew",padx=6,pady=6)
        ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=15,pady=(13,2))
        ctk.CTkLabel(card,text=desc,text_color="#9DA7B4").pack(anchor="w",padx=15,pady=(0,9))
        ctk.CTkButton(card,text="Открыть",command=cmd,height=34).pack(fill="x",padx=15,pady=(0,13))

    ctk.CTkLabel(shell,text="Главная привычка на сейчас",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=24,pady=(18,6))
    ctk.CTkLabel(shell,text=p["habits"][0],wraplength=720,justify="left",
                 text_color="#C6CDD6",font=ctk.CTkFont(size=15)).pack(anchor="w",padx=24)



def position_change_report():
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return None
    d=analysed_moves[current_ply_index]
    before=chess.Board(d["fen"]); after=before.copy(); after.push(d["move"])
    mover=d["mover_color"]

    def hanging(board,color):
        names=[]
        for sq,pc in board.piece_map().items():
            if pc.color!=color or pc.piece_type==chess.KING: continue
            if board.attackers(not color,sq) and not board.attackers(color,sq):
                names.append(f"{_coach_piece_name(pc)} {chess.square_name(sq)}")
        return names

    hb=hanging(before,mover);ha=hanging(after,mover)
    new_hanging=[x for x in ha if x not in hb]
    gone=[x for x in hb if x not in ha]
    notes=[]
    delta=float(d.get("after_cp",0))-float(d.get("before_cp",0))
    # Express evaluation change from mover's perspective.
    mover_delta=delta if mover==chess.WHITE else -delta
    if mover_delta < -30: notes.append(f"Оценка ухудшилась примерно на {abs(mover_delta)/100:.2f} пешки.")
    elif mover_delta > 30: notes.append(f"Оценка улучшилась примерно на {mover_delta/100:.2f} пешки.")
    else: notes.append("Оценка позиции изменилась незначительно.")
    if new_hanging: notes.append("После хода без достаточной защиты: "+", ".join(new_hanging[:3])+".")
    if gone: notes.append("Удалось решить проблему с фигурой: "+", ".join(gone[:2])+".")
    if after.is_check(): notes.append("Ход создал шах, поэтому соперник обязан реагировать.")
    if before.is_capture(d["move"]): notes.append("Произошло взятие — изменилась материальная/тактическая структура.")
    best=d.get("best_move")
    if best and best!=d["move"]:
        notes.append(f"Stockfish предпочитал {d['best_san']}; сравни его с твоим {d['san']}.")
    return d,notes


def open_what_changed():
    rep=position_change_report()
    if not rep:
        messagebox.showinfo("GameCoach","Сначала выбери проанализированный ход.");return
    d,notes=rep
    win=ctk.CTkToplevel(root);win.title("Что изменилось?");win.geometry("650x540")
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🔄 Что изменилось после хода?",
                 font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold")).pack(anchor="w",padx=20,pady=(20,4))
    ctk.CTkLabel(shell,text=f"{d['move_label']} {d['san']} • {d['quality']}",
                 text_color="#98A3B1").pack(anchor="w",padx=20,pady=(0,14))
    for note in notes:
        card=ctk.CTkFrame(shell,corner_radius=11);card.pack(fill="x",padx=20,pady=5)
        ctk.CTkLabel(card,text=note,wraplength=550,justify="left",
                     font=ctk.CTkFont(size=14)).pack(anchor="w",padx=13,pady=11)
    ctk.CTkButton(shell,text="🗺 Показать сравнение на доске",command=show_tactical_map).pack(anchor="w",padx=20,pady=14)


def coach_answer_for(question):
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        return "Сначала выбери проанализированный ход."
    d=analysed_moves[current_ply_index];before=chess.Board(d["fen"])
    q=question.lower().strip()
    if not q: return "Напиши вопрос о текущей позиции."
    if "угрож" in q:
        reply=_best_reply_from_pv(d)
        if reply:
            try:
                b=before.copy();b.push(d["move"])
                return "После твоего хода один из сильных ответов в сохранённой линии Stockfish: "+b.san(reply)+". Проверь, что именно он атакует."
            except Exception: pass
        return "Начни с проверки шахов, взятий и прямых атак соперника."
    if "почему" in q or "плох" in q or "ошиб" in q:
        reasons=explain_best_move_difference(before,d["move"],d.get("best_move"),d["mover_color"])
        base=f"Твой ход: {d['san']}. Stockfish предпочитает {d['best_san']}. Потеря оценки около {d['loss']/100:.2f}."
        if reasons: base+="\n\n"+" ".join(reasons[:3])
        return base
    if "план" in q or "делать" in q:
        phase=d.get("phase","позиции")
        return f"В фазе «{phase}» сначала проверь форсирующие ходы, затем худшую фигуру и безопасность короля. В этой конкретной позиции главный ориентир Stockfish — {d['best_san']}, но попробуй сначала объяснить его идею самостоятельно."
    if "подсказ" in q:
        pack=current_progressive_hints()
        return pack[1][0] if pack else "Для этой позиции подсказка недоступна."
    return f"Для текущей позиции начни с трёх вопросов: 1) что угрожает соперник, 2) какие есть шахи и взятия, 3) какой самый неприятный ответ на мой ход. Stockfish оценивает твой ход как «{d['quality']}»."


def open_ask_coach():
    win=ctk.CTkToplevel(root);win.title("Спроси тренера");win.geometry("720x620")
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="💬 Спроси тренера",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=20,pady=(20,4))
    ctk.CTkLabel(shell,text="Вопрос относится к выбранной позиции. Ответ использует анализ GameCoach и Stockfish.",
                 text_color="#98A3B1").pack(anchor="w",padx=20,pady=(0,12))
    entry=ctk.CTkEntry(shell,placeholder_text="Например: Почему мой ход плохой?",height=42)
    entry.pack(fill="x",padx=20,pady=(0,8))
    answer=ctk.CTkTextbox(shell,wrap="word",font=("Segoe UI",15),corner_radius=12)
    answer.pack(fill="both",expand=True,padx=20,pady=(0,10))
    def ask(text=None):
        q=text or entry.get()
        answer.delete("1.0","end");answer.insert("1.0",coach_answer_for(q))
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=20,pady=(0,18))
    for label,q in [("Почему?","Почему мой ход плохой?"),("Что угрожает?","Что угрожает соперник?"),("Какой план?","Какой план?")]:
        ctk.CTkButton(row,text=label,command=lambda x=q:ask(x)).pack(side="left",padx=(0,5))
    ctk.CTkButton(row,text="Спросить",command=ask).pack(side="right")


def open_review_mode():
    if not analysed_moves:
        messagebox.showinfo("Review","Сначала проанализируй партию.");return
    moments=get_key_moments(6)
    if not moments:
        messagebox.showinfo("Review","В этой партии не найдено достаточно ключевых моментов.");return
    win=ctk.CTkToplevel(root);win.title("GameCoach Review");win.geometry("700x600")
    state={"n":0}
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    title=ctk.CTkLabel(shell,text="",font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold"))
    title.pack(anchor="w",padx=20,pady=(20,4))
    text=ctk.CTkTextbox(shell,wrap="word",font=("Segoe UI",15),corner_radius=12)
    text.pack(fill="both",expand=True,padx=20,pady=12)
    def show():
        _,idx,label=moments[state["n"]];d=analysed_moves[idx];go_to_ply(idx)
        title.configure(text=f"🎬 Момент {state['n']+1}/{len(moments)} • {label}")
        text.delete("1.0","end")
        text.insert("1.0",f"Позиция перед ходом {d['move_label']}.\n\nНе смотри сразу на лучший ход. Сначала ответь себе:\n\n• Что угрожает соперник?\n• Какие есть шахи и взятия?\n• Какой ход ты выбрал бы сейчас?\n\nКогда готов — используй «💡 Подсказка» или «Показать разбор».")
    def nxt():
        if state["n"]<len(moments)-1:state["n"]+=1;show()
        else:text.insert("end","\n\n✅ Review завершён. Теперь повтори сохранённые позиции.")
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=20,pady=(0,18))
    ctk.CTkButton(row,text="💡 Подсказка",command=open_progressive_hint).pack(side="left",padx=(0,5))
    ctk.CTkButton(row,text="🔍 Показать разбор",command=enhanced_why_current_move).pack(side="left",padx=5)
    ctk.CTkButton(row,text="Следующий ▶",command=nxt).pack(side="right")
    show()



def _san_or_uci(board, move):
    try: return board.san(move)
    except Exception: return move.uci()


def open_opponent_prediction():
    """Train the habit of finding the opponent's strongest reply."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери проанализированный ход.");return
    d=analysed_moves[current_ply_index]
    pv=d.get("pv_uci") or []
    if len(pv)<2:
        messagebox.showinfo("GameCoach","Для этой позиции нет сохранённого ответа в PV.");return
    before=chess.Board(d["fen"])
    first=chess.Move.from_uci(pv[0])
    if first not in before.legal_moves:return
    b=before.copy();b.push(first)
    reply=chess.Move.from_uci(pv[1])
    if reply not in b.legal_moves:return

    win=ctk.CTkToplevel(root);win.title("Угадай ответ соперника");win.geometry("620x470")
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🔮 Найди ответ соперника",
                 font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold")).pack(anchor="w",padx=20,pady=(20,4))
    ctk.CTkLabel(shell,text=f"Представь, что сыгран лучший ход {before.san(first)}. Как соперник ответит сильнее всего?",
                 wraplength=540,justify="left",text_color="#AAB3BF").pack(anchor="w",padx=20,pady=(0,14))
    entry=ctk.CTkEntry(shell,placeholder_text="Введи ход, например ...Nxe4 или e7e5",height=42)
    entry.pack(fill="x",padx=20,pady=8)
    result=ctk.CTkTextbox(shell,height=190,wrap="word",font=("Segoe UI",14));result.pack(fill="both",expand=True,padx=20,pady=8)
    def check():
        raw=entry.get().strip()
        ok=False
        try:
            mv=b.parse_san(raw);ok=(mv==reply)
        except Exception:
            try: ok=(chess.Move.from_uci(raw.lower())==reply)
            except Exception: pass
        result.delete("1.0","end")
        if ok:
            award_learning_xp(True);safe_beep("correct")
            result.insert("1.0",f"✅ Верно: {b.san(reply)}\n\nТы проверил ход с точки зрения соперника. +12 XP")
        else:
            award_learning_xp(False);safe_beep("wrong")
            result.insert("1.0","❌ Не совпало с главной линией Stockfish.\n\nНе открывай ответ сразу: проверь шахи, взятия и прямые угрозы соперника.")
    def reveal():
        result.delete("1.0","end");result.insert("1.0",f"Сильный ответ в сохранённой линии: {b.san(reply)}\n\nЛиния: {pv_to_san(before,[chess.Move.from_uci(x) for x in pv[:6]],6)}")
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=20,pady=(0,16))
    ctk.CTkButton(row,text="Проверить",command=check).pack(side="left",padx=(0,5))
    ctk.CTkButton(row,text="Показать ответ",command=reveal).pack(side="right")


def open_candidate_trainer():
    """Name up to three candidates, then evaluate each with Stockfish at equal depth."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери позицию."); return
    if not ensure_stockfish_path():
        return

    d = analysed_moves[current_ply_index]
    base = chess.Board(d["fen"])
    mover = base.turn

    win = ctk.CTkToplevel(root)
    win.title("Три кандидата • честная проверка")
    win.geometry("760x650")
    shell = ctk.CTkFrame(win, corner_radius=18)
    shell.pack(fill="both", expand=True, padx=16, pady=16)

    ctk.CTkLabel(
        shell, text="🧠 Назови 3 кандидата",
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
    ).pack(anchor="w", padx=20, pady=(20,4))
    ctk.CTkLabel(
        shell,
        text="Каждый введённый ход будет отдельно проверен Stockfish. "
             "GameCoach больше не считает ход плохим только потому, что он не первый в PV.",
        text_color="#98A3B1", wraplength=670, justify="left"
    ).pack(anchor="w", padx=20, pady=(0,14))

    entries=[]
    for i in range(3):
        e=ctk.CTkEntry(shell, placeholder_text=f"Кандидат {i+1}: SAN или UCI", height=40)
        e.pack(fill="x", padx=20, pady=5)
        entries.append(e)

    out=ctk.CTkTextbox(shell, wrap="word", font=("Segoe UI",14), corner_radius=12)
    out.pack(fill="both", expand=True, padx=20, pady=12)

    status=ctk.CTkLabel(shell, text="Сначала сформируй кандидатов самостоятельно.", text_color="#AAB3BF")
    status.pack(anchor="w", padx=20, pady=(0,8))

    def parse(txt):
        try:
            return base.parse_san(txt)
        except Exception:
            try:
                m=chess.Move.from_uci(txt.lower())
                return m if m in base.legal_moves else None
            except Exception:
                return None

    def compare():
        candidates=[]
        invalid=[]
        for e in entries:
            raw=e.get().strip()
            if not raw: continue
            mv=parse(raw)
            if mv is None: invalid.append(raw)
            elif mv not in candidates: candidates.append(mv)

        out.delete("1.0","end")
        if invalid:
            out.insert("1.0","Не удалось распознать: "+", ".join(invalid))
            return
        if not candidates:
            out.insert("1.0","Введи хотя бы один легальный кандидат.")
            return

        status.configure(text="Stockfish одинаково проверяет каждый кандидат…")
        for e in entries: e.configure(state="disabled")

        fen=base.fen()
        depth=max(8, min(14, int(app_settings.get("engine_depth_profile",8))+2))

        def worker():
            eng=None
            try:
                eng=launch_stockfish_engine()
                b0=chess.Board(fen)
                root_info=eng.analyse(b0, chess.engine.Limit(depth=depth))
                root_cp=score_cp_for_color(root_info, mover)
                best_pv=root_info.get("pv",[])
                engine_best=best_pv[0] if best_pv else d.get("best_move")

                rows=[]
                for mv in candidates:
                    b=b0.copy()
                    san=_san_or_uci(b,mv)
                    b.push(mv)
                    info=eng.analyse(b, chess.engine.Limit(depth=depth))
                    cp=score_cp_for_color(info,mover)
                    loss=max(0, root_cp-cp)
                    rows.append((san,cp,loss,fair_candidate_label(loss)))

                def apply():
                    if not win.winfo_exists(): return
                    for e in entries: e.configure(state="normal")
                    out.delete("1.0","end")
                    best_san=_san_or_uci(b0,engine_best) if engine_best else "—"
                    out.insert("end",f"Stockfish depth {depth} • лучший найденный ход: {best_san}\n\n")
                    for n,(san,cp,loss,label) in enumerate(rows,1):
                        out.insert("end",f"{n}. {san}\n   оценка для тебя: {cp/100:+.2f}\n   потеря: {loss/100:.2f} • {label}\n\n")
                    best_user=min((r[2] for r in rows), default=99999)
                    success=best_user<=50
                    out.insert("end",
                        "GameCoach оценивает качество кандидата по потере оценки, "
                        "а не только по совпадению с первой линией PV.\n\n"
                        "Важно: эти категории — собственные метрики GameCoach, не Chess.com."
                    )
                    award_learning_xp(success)
                    status.configure(text="✅ Кандидаты проверены одинаковой глубиной Stockfish.")
                root.after(0,apply)
            except Exception as exc:
                root.after(0,lambda e=str(exc): status.configure(text=f"Ошибка анализа: {e}"))
                root.after(0,lambda: [e.configure(state="normal") for e in entries if win.winfo_exists()])
            finally:
                if eng:
                    try: eng.quit()
                    except Exception: pass

        threading.Thread(target=worker,daemon=True).start()

    ctk.CTkButton(shell,text="⚖ Проверить кандидатов",command=compare,height=42).pack(fill="x",padx=20,pady=(0,18))



def open_calculation_tree():
    """Build a user's calculation line, then compare it with the saved Stockfish PV."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери позицию.");return
    d=analysed_moves[current_ply_index];base=chess.Board(d["fen"])
    engine_line=[chess.Move.from_uci(x) for x in (d.get("pv_uci") or [])[:6]]
    if not engine_line:
        messagebox.showinfo("GameCoach","Для позиции нет сохранённой линии.");return
    win=ctk.CTkToplevel(root);win.title("Линия расчёта");win.geometry("760x650")
    state={"board":base.copy(),"line":[]}
    shell=ctk.CTkFrame(win,corner_radius=18);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🌳 Линия расчёта",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=20,pady=(20,4))
    ctk.CTkLabel(shell,text="Вводи свой вариант по одному ходу. GameCoach не показывает PV до проверки.",
                 text_color="#98A3B1").pack(anchor="w",padx=20,pady=(0,12))
    tree=ctk.CTkTextbox(shell,height=250,wrap="word",font=("Consolas",15));tree.pack(fill="x",padx=20,pady=8)
    entry=ctk.CTkEntry(shell,placeholder_text="Следующий ход: SAN или UCI",height=42);entry.pack(fill="x",padx=20,pady=6)
    result=ctk.CTkTextbox(shell,wrap="word",font=("Segoe UI",14));result.pack(fill="both",expand=True,padx=20,pady=8)
    def refresh():
        b=base.copy();parts=[]
        for i,m in enumerate(state["line"]):
            san=_san_or_uci(b,m);parts.append(f"{i+1}. {san}");b.push(m)
        tree.delete("1.0","end");tree.insert("1.0"," → ".join(parts) if parts else "Твой вариант пока пуст.")
    def add():
        raw=entry.get().strip();b=state["board"]
        try:m=b.parse_san(raw)
        except Exception:
            try:m=chess.Move.from_uci(raw.lower())
            except Exception:m=None
        if not m or m not in b.legal_moves:
            result.delete("1.0","end");result.insert("1.0","Нелегальный или нераспознанный ход.");return
        state["line"].append(m);b.push(m);entry.delete(0,"end");refresh()
    def reset():
        state["board"]=base.copy();state["line"]=[];refresh();result.delete("1.0","end")
    def check():
        line=state["line"];same=0
        for a,e in zip(line,engine_line):
            if a==e:same+=1
            else:break
        result.delete("1.0","end")
        pvtxt=pv_to_san(base,engine_line,len(engine_line))
        if same==len(line) and line:
            result.insert("1.0",f"✅ Твоя линия совпадает с PV на {same} полуходов.\n\nStockfish: {pvtxt}")
            award_learning_xp(True)
        else:
            result.insert("1.0",f"Совпадение до первого расхождения: {same} полуходов.\n\nStockfish: {pvtxt}\n\nНайди, почему ветка расходится именно в этом месте.")
            award_learning_xp(False)
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=20,pady=(0,16))
    ctk.CTkButton(row,text="+ Добавить ход",command=add).pack(side="left",padx=(0,5))
    ctk.CTkButton(row,text="Сброс",command=reset).pack(side="left",padx=5)
    ctk.CTkButton(row,text="Проверить линию",command=check).pack(side="right")
    refresh()


def open_thinking_workout():
    win=ctk.CTkToplevel(root);win.title("Thinking System");win.geometry("760x610")
    shell=ctk.CTkFrame(win,corner_radius=20);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧠 Thinking System",
                 font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,text="Тренируй последовательность: угроза → кандидаты → расчёт → решение.",
                 text_color="#98A3B1").pack(anchor="w",padx=22,pady=(0,16))
    items=[
        ("1. 🔮 Ответ соперника","Сначала найди самый неприятный ответ.",open_opponent_prediction),
        ("2. 🧠 Три кандидата","Не хватайся за первый ход.",open_candidate_trainer),
        ("3. 🌳 Линия расчёта","Построй линию и сравни её с PV.",open_calculation_tree),
        ("4. 💡 Подсказки","Если застрял — получай помощь постепенно.",open_progressive_hint),
    ]
    for title,desc,cmd in items:
        card=ctk.CTkFrame(shell,corner_radius=12);card.pack(fill="x",padx=22,pady=5)
        ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=14,pady=(10,2))
        ctk.CTkLabel(card,text=desc,text_color="#AAB3BF").pack(anchor="w",padx=14,pady=(0,7))
        ctk.CTkButton(card,text="Открыть",command=cmd,height=32).pack(anchor="e",padx=14,pady=(0,10))




# ============================================================
# GAMECOACH 29 — ADAPTIVE COACH
# ============================================================

def adaptive_coach_profile():
    """Select a training focus from the user's own recent errors and training history."""
    thinking=build_thinking_profile()
    trend=progress_trend_summary()
    m7=db_recent_progress(7)
    m30=db_recent_progress(30)
    end_stats=load_endgame_profile().get("stats",{})

    attempts=m7.get("attempts",0)
    acc7=(100*m7.get("correct",0)/attempts) if attempts else None

    cats=thinking.get("categories",[])
    top_topic=cats[0][0] if cats else "проверка ответа соперника"
    weak_phase=str(thinking.get("weak_phase","—"))

    if acc7 is None:
        difficulty="Нормальная"
        target_count=5
        hint_policy="Подсказки доступны, но сначала попробуй сам."
    elif acc7 < 45:
        difficulty="Поддерживающая"
        target_count=4
        hint_policy="Разрешены ранние подсказки: сейчас важнее закрепить правильный процесс."
    elif acc7 < 70:
        difficulty="Нормальная"
        target_count=6
        hint_policy="Используй подсказку только после собственной попытки."
    elif acc7 < 85:
        difficulty="Сложная"
        target_count=8
        hint_policy="Сначала решай без подсказок и сравнивай несколько кандидатов."
    else:
        difficulty="Интенсивная"
        target_count=10
        hint_policy="Минимум подсказок; добавляй расчёт и профилактику."

    mode="thinking"
    reason=f"Главная повторяющаяся тема: {top_topic}."

    lower_phase=weak_phase.lower()
    if "деб" in lower_phase:
        mode="opening"
        reason=f"Слабая фаза сейчас — {weak_phase}; репертуар должен стать стабильнее."
    elif "энд" in lower_phase:
        mode="endgame"
        reason=f"Слабая фаза сейчас — {weak_phase}; полезнее переигрывать окончания."
    elif any(k in top_topic for k in ["шах","взят","вилка","форс"]):
        mode="tactics"
        reason=f"Чаще всего повторяется тактическая тема «{top_topic}»."
    elif any(k in top_topic for k in ["ответ соперника","безопасност","незащищ"]):
        mode="prevention"
        reason=f"Главный фокус — профилактика: «{top_topic}»."
    elif "расч" in top_topic:
        mode="calculation"
        reason=f"Главный фокус — расчёт: «{top_topic}»."

    # If recent form worsened significantly, reduce volume and emphasize review.
    delta=trend.get("delta")
    if delta is not None and delta >= 0.5:
        target_count=max(4,target_count-2)
        reason += " Последний блок партий ухудшился, поэтому объём уменьшен, а разбор усилен."

    endgame_attempts=sum(int(v.get("attempts",0)) for v in end_stats.values() if isinstance(v,dict))

    return {
        "mode":mode,
        "topic":top_topic,
        "weak_phase":weak_phase,
        "difficulty":difficulty,
        "target_count":target_count,
        "accuracy7":acc7,
        "attempts7":attempts,
        "attempts30":m30.get("attempts",0),
        "reason":reason,
        "hint_policy":hint_policy,
        "trend":trend.get("direction",""),
        "endgame_attempts":endgame_attempts,
    }


def adaptive_session_steps():
    p=adaptive_coach_profile()
    steps=[]
    due=due_training_count() if training_positions else 0

    # Always start with spaced repetition when something is due.
    if training_positions and due:
        n=min(p["target_count"],max(1,due))
        steps.append(("🔁 Повторение",f"{n} задач, которые сейчас пора повторить.",start_due_training))

    mode=p["mode"]
    if mode=="opening":
        steps.append(("📚 Repertoire Drill","Повтори свои реальные дебютные развилки.",open_repertoire_drill))
        if analysed_moves:
            steps.append(("🎬 Review дебюта","Посмотри, где именно дебют начал отклоняться.",open_opening_coach))
    elif mode=="endgame":
        steps.append(("🏁 Endgame Drill","Переиграй собственное окончание против Stockfish.",open_random_endgame_drill))
        steps.append(("📊 Endgame Progress","Проверь, какой тип окончания отстаёт.",open_endgame_progress))
    elif mode=="tactics":
        if analysed_moves:
            steps.append(("🕵 Найди ошибку","Сначала найди критический момент без оценки.",open_find_mistake))
            steps.append(("🧠 Три кандидата","Не хватайся за первый тактический ход.",open_candidate_trainer))
            steps.append(("🧩 Puzzle Lab","Реши собственные тактические ошибки.",open_timed_puzzle))
    elif mode=="calculation":
        if analysed_moves:
            steps.append(("🌳 Линия расчёта","Построй вариант до просмотра PV.",open_calculation_tree))
            steps.append(("🧠 Три кандидата","Сравни несколько продолжений.",open_candidate_trainer))
    elif mode=="prevention":
        if analysed_moves:
            steps.append(("🔮 Ответ соперника","Найди самый неприятный ответ соперника.",open_opponent_prediction))
            steps.append(("👁 Что я пропустил?","Поставь диагноз ошибке до открытия ответа.",open_what_did_i_miss))
            steps.append(("🔄 Что изменилось?","Сравни позицию до и после решения.",open_what_changed))
    else:
        if analysed_moves:
            steps.append(("🕵 Найди ошибку","Найди критический момент самостоятельно.",open_find_mistake))
            steps.append(("🔮 Ответ соперника","Проверь профилактическое мышление.",open_opponent_prediction))
            steps.append(("🌳 Расчёт","Рассчитай короткую линию.",open_calculation_tree))

    if not steps and training_positions:
        steps.append(("🧩 Личные задачи","Реши задачи из собственной библиотеки.",start_due_training))
    if not steps:
        steps.append(("📂 Подготовка","Импортируй и проанализируй партию или создай профиль Chess.com.",lambda:None))

    return steps


def open_adaptive_coach():
    p=adaptive_coach_profile()
    win=ctk.CTkToplevel(root)
    win.title("Adaptive Coach • GameCoach 30.0")
    win.geometry("860x720")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="🧠 Adaptive Coach",
        font=ctk.CTkFont(family="Segoe UI",size=28,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,
        text="GameCoach сам выбирает фокус и сложность занятия по твоим ошибкам, фазам игры и недавним тренировкам.",
        text_color=GC_TEXT_MUTED,wraplength=790,justify="left"
    ).pack(anchor="w",padx=22,pady=(0,14))

    cards=ctk.CTkFrame(shell,fg_color="transparent")
    cards.pack(fill="x",padx=18,pady=(0,10))
    vals=[
        ("ФОКУС",p["mode"]),
        ("СЛОЖНОСТЬ",p["difficulty"]),
        ("ЦЕЛЬ",str(p["target_count"])+" поз."),
        ("7 ДНЕЙ","—" if p["accuracy7"] is None else f"{p['accuracy7']:.0f}%"),
    ]
    for i,(t,v) in enumerate(vals):
        cards.grid_columnconfigure(i,weight=1)
        card=ctk.CTkFrame(cards,corner_radius=12,fg_color=GC_PANEL_2)
        card.grid(row=0,column=i,sticky="nsew",padx=4)
        ctk.CTkLabel(card,text=t,text_color="#8F9AAA",font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=12,pady=(11,3))
        ctk.CTkLabel(card,text=v,font=ctk.CTkFont(size=20,weight="bold"),wraplength=150).pack(anchor="w",padx=12,pady=(0,12))

    why=ctk.CTkFrame(shell,corner_radius=14,fg_color=GC_PANEL_2)
    why.pack(fill="x",padx=22,pady=7)
    ctk.CTkLabel(why,text="Почему GameCoach выбрал это",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=15,pady=(12,4))
    ctk.CTkLabel(why,text=p["reason"]+"\n"+p["trend"],
                 wraplength=760,justify="left",text_color="#C7CED6").pack(anchor="w",padx=15,pady=(0,12))

    habit=ctk.CTkFrame(shell,corner_radius=14,fg_color=GC_PANEL_2)
    habit.pack(fill="x",padx=22,pady=7)
    ctk.CTkLabel(habit,text="Правило сложности",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=15,pady=(12,4))
    ctk.CTkLabel(habit,text=p["hint_policy"],wraplength=760,justify="left",
                 text_color="#C7CED6").pack(anchor="w",padx=15,pady=(0,12))

    steps=adaptive_session_steps()
    ctk.CTkLabel(shell,text="Сегодняшний адаптивный план",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=22,pady=(14,5))
    for n,(title,desc,_) in enumerate(steps[:5],1):
        ctk.CTkLabel(shell,text=f"{n}. {title} — {desc}",wraplength=790,justify="left").pack(anchor="w",padx=24,pady=3)

    row=ctk.CTkFrame(shell,fg_color="transparent")
    row.pack(fill="x",padx=22,pady=(16,18))
    ctk.CTkButton(row,text="▶ Начать адаптивную тренировку",
                  command=lambda:(win.destroy(),open_daily_session()),
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=44).pack(side="left",fill="x",expand=True,padx=(0,5))
    ctk.CTkButton(row,text="📈 Прогресс",command=open_quality_progress,
                  fg_color="#6B5B3E",hover_color="#806D49",height=44).pack(side="left",fill="x",expand=True,padx=5)


# ============================================================
# GAMECOACH 21 — GUIDED DAILY SESSION
# ============================================================

def build_daily_session_steps():
    """GameCoach 29: daily session is chosen adaptively from current weaknesses."""
    return adaptive_session_steps()



def open_daily_session():
    steps=build_daily_session_steps()
    win=ctk.CTkToplevel(root)
    win.title("Адаптивная тренировка • GameCoach 29")
    win.geometry("780x670")
    state={"idx":0,"done":0,"started":int(time.time())}

    shell=ctk.CTkFrame(win,corner_radius=20)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    header=ctk.CTkLabel(shell,text="🧠 Адаптивная тренировка",
                        font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold"))
    header.pack(anchor="w",padx=22,pady=(22,4))
    subtitle=ctk.CTkLabel(shell,text="",text_color="#98A3B1")
    subtitle.pack(anchor="w",padx=22,pady=(0,10))

    progress=ctk.CTkProgressBar(shell)
    progress.pack(fill="x",padx=22,pady=(0,14))

    current=ctk.CTkFrame(shell,corner_radius=14)
    current.pack(fill="x",padx=22,pady=(0,12))
    step_title=ctk.CTkLabel(current,text="",font=ctk.CTkFont(size=19,weight="bold"))
    step_title.pack(anchor="w",padx=16,pady=(16,4))
    step_desc=ctk.CTkLabel(current,text="",wraplength=650,justify="left",text_color="#B1BAC6")
    step_desc.pack(anchor="w",padx=16,pady=(0,16))

    ctk.CTkLabel(shell,text="План занятия",font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=22,pady=(4,6))
    listbox=ctk.CTkTextbox(shell,height=230,wrap="word",font=("Segoe UI",14),corner_radius=12)
    listbox.pack(fill="both",expand=True,padx=22,pady=(0,12))
    listbox.configure(state="disabled")

    row=ctk.CTkFrame(shell,fg_color="transparent")
    row.pack(fill="x",padx=22,pady=(0,18))

    def redraw():
        n=len(steps);i=state["idx"]
        subtitle.configure(text=f"Этап {min(i+1,n)}/{n} • завершено {state['done']}")
        progress.set(state["done"]/max(1,n))
        title,desc,_=steps[min(i,n-1)]
        step_title.configure(text=title)
        step_desc.configure(text=desc)
        listbox.configure(state="normal");listbox.delete("1.0","end")
        for k,(t,d,_) in enumerate(steps):
            mark="✅" if k<state["done"] else ("▶" if k==i else "○")
            listbox.insert("end",f"{mark} {k+1}. {t}\n   {d}\n\n")
        listbox.configure(state="disabled")

    def launch():
        _,_,cmd=steps[state["idx"]]
        if cmd:
            cmd()

    def complete_and_next():
        if state["done"] < state["idx"]+1:
            state["done"]=state["idx"]+1
        if state["idx"] < len(steps)-1:
            state["idx"]+=1
            redraw()
        else:
            finish()

    def finish():
        db_log_session(
            state["started"], len(steps), state["done"],
            training_session_correct, training_session_wrong, "guided-daily"
        )
        mins=max(1,round((time.time()-state["started"])/60))
        messagebox.showinfo(
            "Тренировка завершена",
            f"✅ Сессия сохранена.\n\nЭтапов: {state['done']}/{len(steps)}\nВремя: ~{mins} мин\n"
            f"Решения в режиме повторения: {training_session_correct} верно / {training_session_wrong} ошибочно.",
            parent=win
        )
        try: win.destroy()
        except Exception: pass

    ctk.CTkButton(row,text="▶ Открыть этап",command=launch,height=42).pack(side="left",fill="x",expand=True,padx=(0,5))
    ctk.CTkButton(row,text="✓ Этап выполнен →",command=complete_and_next,height=42).pack(side="left",fill="x",expand=True,padx=5)
    ctk.CTkButton(row,text="Завершить",command=finish,height=42,width=100).pack(side="right",padx=(5,0))
    redraw()


def open_analysis_toolbox():
    win=ctk.CTkToplevel(root)
    win.title("Инструменты анализа")
    win.geometry("720x620")
    shell=ctk.CTkFrame(win,corner_radius=18)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(shell,text="🧰 Инструменты анализа",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(shell,text="Редкие функции собраны здесь, чтобы основной экран оставался чистым.",
                 text_color="#98A3B1").pack(anchor="w",padx=22,pady=(0,14))

    tools=[
        ("🧠 Adaptive Coach","Автоматически выбирает фокус, сложность и план занятия.",open_adaptive_coach),
        ("📈 Progress Intelligence","Тренды, сравнение последних партий и недельный отчёт.",open_quality_progress),
        ("📅 Weekly Coach Report","Короткий отчёт и следующая тренировочная цель.",open_weekly_coach_report),
        ("🏁 Endgame Coach Pro","Найди, реши и переиграй собственные эндшпили.",open_endgame_coach),
        ("📚 Opening Repertoire","Дерево твоих дебютов, стабильность ходов и тренировка.",open_opening_repertoire),
        ("🎯 Replay Trainer","Продолжи игру против Stockfish из своей критической позиции.",open_replay_hub),
        ("🧩 Puzzle Lab","Задачи из собственных партий, таймер и XP 2.0.",open_puzzle_lab),
        ("🎯 Сыграй лучше","Повторно реши выбранную критическую позицию.",replay_position_vs_stockfish),
        ("👁 Что я пропустил?","Сначала поставь диагноз ошибке без спойлера.",open_what_did_i_miss),
        ("🕵 Blind Review","Повтори ключевые моменты без оценки движка.",open_blind_review),
        ("💬 Спроси тренера","Объяснение выбранной позиции.",open_ask_coach),
        ("🔄 Что изменилось?","Сравнение до и после твоего хода.",open_what_changed),
        ("🎬 Review","Ключевые моменты партии как урок.",open_review_mode),
        ("🔮 Ответ соперника","Тренировка профилактического мышления.",open_opponent_prediction),
        ("🧠 3 кандидата","Честная оценка нескольких ходов Stockfish.",open_candidate_trainer),
        ("🌳 Линия расчёта","Сравнение собственного варианта с PV.",open_calculation_tree),
        ("🗂 Мои задачи","Постоянная личная библиотека.",open_puzzle_library),
        ("🧠 Thinking System","Комплексная тренировка мышления.",open_thinking_workout),
    ]
    grid=ctk.CTkScrollableFrame(shell,corner_radius=12)
    grid.pack(fill="both",expand=True,padx=20,pady=(0,18))
    for title,desc,cmd in tools:
        card=ctk.CTkFrame(grid,corner_radius=11)
        card.pack(fill="x",padx=6,pady=5)
        text=ctk.CTkFrame(card,fg_color="transparent")
        text.pack(side="left",fill="both",expand=True,padx=13,pady=10)
        ctk.CTkLabel(text,text=title,font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(text,text=desc,text_color="#9CA6B3").pack(anchor="w",pady=(2,0))
        ctk.CTkButton(card,text="Открыть",command=cmd,width=90,height=34).pack(side="right",padx=12)


def open_quality_progress():
    trend=progress_trend_summary()
    m7=db_recent_progress(7)
    m30=db_recent_progress(30)
    rec=trend["recent"]; prev=trend["previous"]

    win=ctk.CTkToplevel(root)
    win.title("Progress Intelligence • GameCoach 30.0")
    win.geometry("940x760")
    win.minsize(800,650)

    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="📈 Progress Intelligence",
        font=ctk.CTkFont(family="Segoe UI",size=28,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,
        text="Сравнивает последние партии и реальные тренировочные записи из локальной базы GameCoach.",
        text_color=GC_TEXT_MUTED,wraplength=850,justify="left"
    ).pack(anchor="w",padx=22,pady=(0,14))

    cards=ctk.CTkFrame(shell,fg_color="transparent")
    cards.pack(fill="x",padx=18,pady=(0,10))
    for i in range(4):cards.grid_columnconfigure(i,weight=1)

    vals=[
        ("ПАРТИЙ В БЛОКЕ",str(rec["games"])),
        ("ОШИБОК / ПАРТИЮ",f"{rec['errors_pg']:.2f}"),
        ("ЗЕВКОВ / ПАРТИЮ",f"{rec['blunders_pg']:.2f}"),
        ("ТРЕНИРОВОК 7 ДНЕЙ",str(m7["attempts"])),
    ]
    for i,(title,value) in enumerate(vals):
        card=ctk.CTkFrame(cards,corner_radius=12,fg_color=GC_PANEL_2)
        card.grid(row=0,column=i,sticky="nsew",padx=4)
        ctk.CTkLabel(card,text=title,text_color="#8F9AAA",
                     font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=12,pady=(12,3))
        ctk.CTkLabel(card,text=value,font=ctk.CTkFont(size=22,weight="bold")).pack(anchor="w",padx=12,pady=(0,12))

    trend_card=ctk.CTkFrame(shell,corner_radius=14,fg_color=GC_PANEL_2)
    trend_card.pack(fill="x",padx=22,pady=7)
    ctk.CTkLabel(trend_card,text="Сравнение последних 10 партий",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=15,pady=(12,4))
    compare=trend["direction"]
    if prev["games"]:
        compare+=f"\nСейчас: {rec['errors_pg']:.2f} ошибок/партию • раньше: {prev['errors_pg']:.2f}"
        compare+=f"\nЗевки: {rec['blunders_pg']:.2f} → ранее {prev['blunders_pg']:.2f}"
    ctk.CTkLabel(trend_card,text=compare,wraplength=840,justify="left",
                 text_color="#C7CED6").pack(anchor="w",padx=15,pady=(0,13))

    train_card=ctk.CTkFrame(shell,corner_radius=14,fg_color=GC_PANEL_2)
    train_card.pack(fill="x",padx=22,pady=7)
    acc7=100*m7["correct"]/m7["attempts"] if m7["attempts"] else 0
    acc30=100*m30["correct"]/m30["attempts"] if m30["attempts"] else 0
    ctk.CTkLabel(train_card,text="Тренировочная форма",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=15,pady=(12,4))
    ctk.CTkLabel(
        train_card,
        text=f"7 дней: {m7['attempts']} попыток • {acc7:.0f}% верно • {m7['sessions']} сессий\n"
             f"30 дней: {m30['attempts']} попыток • {acc30:.0f}% верно • {m30['sessions']} сессий",
        justify="left",text_color="#C7CED6"
    ).pack(anchor="w",padx=15,pady=(0,13))

    btns=ctk.CTkFrame(shell,fg_color="transparent")
    btns.pack(fill="x",padx=22,pady=(10,18))
    ctk.CTkButton(btns,text="📅 Weekly Coach Report",command=open_weekly_coach_report,
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=42).pack(side="left",fill="x",expand=True,padx=(0,5))
    ctk.CTkButton(btns,text="🧬 Player Intelligence",command=open_player_intelligence,
                  fg_color="#6B5B3E",hover_color="#806D49",height=42).pack(side="left",fill="x",expand=True,padx=5)


def open_weekly_coach_report():
    win=ctk.CTkToplevel(root)
    win.title("Weekly Coach Report • GameCoach 28")
    win.geometry("820x700")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="📅 Weekly Coach Report",
        font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,text="Автоматический отчёт по последним сохранённым партиям и тренировкам.",
        text_color=GC_TEXT_MUTED
    ).pack(anchor="w",padx=22,pady=(0,12))

    box=ctk.CTkTextbox(shell,wrap="word",font=("Segoe UI",14),corner_radius=12)
    box.pack(fill="both",expand=True,padx=22,pady=(4,14))
    box.insert("1.0",weekly_coach_report_text())
    box.configure(state="disabled")

    ctk.CTkButton(
        shell,text="🧠 Открыть Adaptive Coach",
        command=open_adaptive_coach,fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=42
    ).pack(fill="x",padx=22,pady=(0,18))





# ============================================================
# GAMECOACH 22 — PLAYER INTELLIGENCE
# ============================================================

def player_intelligence_snapshot():
    p=build_thinking_profile()
    attempts=sum(int(r.get("attempts",0)) for r in training_stats.values() if isinstance(r,dict))
    correct=sum(int(r.get("correct",0)) for r in training_stats.values() if isinstance(r,dict))
    acc=(100*correct/attempts) if attempts else 0
    cats=dict(p.get("categories",[]))
    total=max(1,p.get("total",0))

    def score_for(keys, base=55):
        bad=sum(cats.get(k,0) for k in keys)
        penalty=min(40, bad/max(1,total)*120)
        bonus=min(20, acc/5) if attempts else 0
        return max(20,min(95,round(base+bonus-penalty)))

    return {
        "tactics":score_for(["двойное нападение / вилка","пропущенный шах","пропущенное взятие"],58),
        "calculation":score_for(["расчёт размена","проверка ответа соперника"],54),
        "prevention":score_for(["проверка безопасности фигуры","незащищённая фигура","проверка ответа соперника"],52),
        "opening":score_for(["ранний выход ферзя"],60),
        "endgame":max(25,min(90,round(50+(acc-50)*0.25))) if attempts else 50,
        "accuracy":acc,
        "attempts":attempts,
        "profile":p,
    }


def recurring_error_groups():
    p=build_thinking_profile()
    groups=[]
    for name,count in p.get("categories",[]):
        if count:
            groups.append((name,int(count)))
    return groups


def open_player_intelligence():
    snap=player_intelligence_snapshot()
    win=ctk.CTkToplevel(root);win.title("Player Intelligence");win.geometry("800x690")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧬 Player Intelligence",
                 font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")).pack(anchor="w",padx=24,pady=(22,3))
    ctk.CTkLabel(shell,text="Профиль строится по твоим сохранённым ошибкам и тренировкам. Это GameCoach Skill Scores, не Elo.",
                 text_color=GC_TEXT_MUTED,wraplength=710,justify="left").pack(anchor="w",padx=24,pady=(0,16))
    skills=[("⚔ Тактика","tactics"),("🌳 Расчёт","calculation"),("🛡 Профилактика","prevention"),
            ("📚 Дебют","opening"),("🏁 Эндшпиль","endgame")]
    for title,key in skills:
        row=ctk.CTkFrame(shell,corner_radius=11,fg_color=GC_PANEL_2);row.pack(fill="x",padx=24,pady=4)
        ctk.CTkLabel(row,text=title,width=150,anchor="w",font=ctk.CTkFont(size=14,weight="bold")).pack(side="left",padx=14,pady=11)
        bar=ctk.CTkProgressBar(row,progress_color=GC_ACCENT,fg_color="#30363D")
        bar.pack(side="left",fill="x",expand=True,padx=8);bar.set(snap[key]/100)
        ctk.CTkLabel(row,text=str(snap[key]),width=42,font=ctk.CTkFont(size=16,weight="bold"),
                     text_color="#73D6A4").pack(side="right",padx=14)
    ctk.CTkLabel(shell,text="Повторяющиеся проблемы",
                 font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=24,pady=(18,6))
    groups=recurring_error_groups()
    text="\n".join(f"• {name}: {count} раз" for name,count in groups[:5]) if groups else "Пока недостаточно сохранённых ошибок для устойчивого профиля."
    ctk.CTkLabel(shell,text=text,justify="left",wraplength=700,text_color="#C9D0D8").pack(anchor="w",padx=24)
    ctk.CTkButton(shell,text="📅 Построить тренировку по слабостям",command=open_daily_session,
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=42).pack(fill="x",padx=24,pady=20)


def classify_endgame(board):
    """Heuristic endgame classifier. It is deliberately not a tablebase/ECO-style authority."""
    pieces=[p for p in board.piece_map().values() if p.piece_type!=chess.KING]
    if len(pieces)>12:
        return None

    counts=Counter((p.color,p.piece_type) for p in pieces)
    queens=sum(v for (c,t),v in counts.items() if t==chess.QUEEN)
    rooks=sum(v for (c,t),v in counts.items() if t==chess.ROOK)
    bishops=sum(v for (c,t),v in counts.items() if t==chess.BISHOP)
    knights=sum(v for (c,t),v in counts.items() if t==chess.KNIGHT)
    pawns=sum(v for (c,t),v in counts.items() if t==chess.PAWN)

    if queens:
        return "Ферзевый эндшпиль"
    if rooks and not bishops and not knights:
        return "Ладейный эндшпиль"
    if rooks and (bishops or knights):
        return "Ладья + лёгкая фигура"
    if bishops and not knights:
        return "Слоновый эндшпиль"
    if knights and not bishops:
        return "Коневой эндшпиль"
    if bishops and knights:
        return "Эндшпиль лёгких фигур"
    if pawns:
        return "Пешечный эндшпиль"
    return "Минимальный материал"


def endgame_material_signature(board):
    values={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9}
    w=sum(values.get(p.piece_type,0) for p in board.piece_map().values() if p.color==chess.WHITE)
    b=sum(values.get(p.piece_type,0) for p in board.piece_map().values() if p.color==chess.BLACK)
    return w,b


def endgame_positions_from_analysis():
    out=[]
    for idx,d in enumerate(analysed_moves):
        try:
            b=chess.Board(d["fen"])
            kind=classify_endgame(b)
            if not kind:
                continue
            w,bv=endgame_material_signature(b)
            out.append({
                "index":idx,
                "kind":kind,
                "fen":d["fen"],
                "san":d.get("san",""),
                "move_label":d.get("move_label",""),
                "loss":float(d.get("loss",0) or 0),
                "before_cp":float(d.get("before_cp",0) or 0),
                "after_cp":float(d.get("after_cp",0) or 0),
                "material":(w,bv),
                "turn":"white" if b.turn==chess.WHITE else "black"
            })
        except Exception:
            pass
    return out


def load_endgame_profile():
    try:
        d=load_json(ENDGAME_FILE,{})
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}


def save_endgame_attempt(kind,success,delta_cp=0):
    data=load_endgame_profile()
    stats=data.setdefault("stats",{})
    row=stats.setdefault(kind,{"attempts":0,"success":0,"delta_total":0.0})
    row["attempts"]+=1
    if success:
        row["success"]+=1
    row["delta_total"]+=float(delta_cp)
    data["updated"]=datetime.now().isoformat(timespec="seconds")
    save_json(ENDGAME_FILE,data)





# ============================================================
# GAMECOACH 26 — OPENING REPERTOIRE
# ============================================================

def load_repertoire():
    try:
        data=load_json(REPERTOIRE_FILE,{})
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}


def save_repertoire(data):
    try:
        save_json(REPERTOIRE_FILE,data)
    except Exception:
        pass


def _result_for_user(result,user_color):
    if result=="1-0": return "win" if user_color==chess.WHITE else "loss"
    if result=="0-1": return "win" if user_color==chess.BLACK else "loss"
    return "draw" if result=="1/2-1/2" else "unknown"


def build_repertoire_from_pgn_games(games,username,max_plies=18):
    """Build a personal opening tree from the user's own games, not an ECO database."""
    positions={}
    games_used=0
    opening_counts=Counter()

    for g in games:
        try:
            game=chess.pgn.read_game(io.StringIO(g.get("pgn","")))
            if game is None: continue
            white=game.headers.get("White","")
            black=game.headers.get("Black","")
            if white.lower()==username.lower():
                user_color=chess.WHITE
            elif black.lower()==username.lower():
                user_color=chess.BLACK
            else:
                continue

            result=_result_for_user(game.headers.get("Result","*"),user_color)
            board=game.board()
            sans=[]
            raw=list(game.mainline_moves())
            opening_counts[detect_opening_from_sans(
                [board.san(m) if False else "" for m in []]
            )]+=0  # keeps Counter initialized without pretending to know ECO

            for ply,mv in enumerate(raw[:max_plies]):
                before=board.copy()
                san=before.san(mv)

                if before.turn==user_color:
                    key=before.fen()
                    rec=positions.setdefault(key,{
                        "fen":key,
                        "color":"white" if user_color==chess.WHITE else "black",
                        "ply":ply,
                        "prefix":" ".join(sans),
                        "moves":{},
                        "games":0,
                        "wins":0,"draws":0,"losses":0
                    })
                    rec["games"]+=1
                    if result=="win":rec["wins"]+=1
                    elif result=="draw":rec["draws"]+=1
                    elif result=="loss":rec["losses"]+=1

                    mr=rec["moves"].setdefault(mv.uci(),{
                        "uci":mv.uci(),"san":san,"count":0,
                        "wins":0,"draws":0,"losses":0
                    })
                    mr["count"]+=1
                    if result=="win":mr["wins"]+=1
                    elif result=="draw":mr["draws"]+=1
                    elif result=="loss":mr["losses"]+=1

                sans.append(san)
                board.push(mv)

            # identify opening family from actual SAN sequence
            opening_counts[detect_opening_from_sans(sans[:8])]+=1
            games_used+=1
        except Exception:
            continue

    # useful summaries
    for rec in positions.values():
        moves=list(rec["moves"].values())
        moves.sort(key=lambda x:x["count"],reverse=True)
        rec["moves"]={m["uci"]:m for m in moves}

    return {
        "username":username,
        "created":datetime.now().isoformat(timespec="seconds"),
        "games_used":games_used,
        "max_plies":max_plies,
        "openings":dict(opening_counts),
        "positions":positions
    }


def start_build_repertoire():
    username=username_entry.get().strip()
    if not username:
        messagebox.showwarning("Opening Repertoire","Введи ник Chess.com.")
        return
    n=int(app_settings.get("recent_games",20))
    status_label.configure(text=f"📚 Загружаю последние {n} партий для репертуара…")

    def worker():
        try:
            games=fetch_recent_chesscom_games(username,n)
            if not games: raise Exception("Не найдено партий Chess.com.")
            rep=build_repertoire_from_pgn_games(games,username)
            save_repertoire(rep)
            root.after(0,lambda: status_label.configure(
                text=f"✅ Репертуар: {rep.get('games_used',0)} партий • {len(rep.get('positions',{}))} позиций"
            ))
            root.after(0,open_opening_repertoire)
        except Exception as e:
            root.after(0,lambda msg=str(e):messagebox.showerror("Opening Repertoire",msg))
            root.after(0,lambda:status_label.configure(text="❌ Не удалось построить репертуар"))

    threading.Thread(target=worker,daemon=True).start()


def repertoire_position_rows(rep,color_filter=None):
    rows=[]
    for rec in rep.get("positions",{}).values():
        if color_filter and rec.get("color")!=color_filter:continue
        moves=list(rec.get("moves",{}).values())
        if not moves:continue
        moves.sort(key=lambda m:m.get("count",0),reverse=True)
        total=max(1,sum(m.get("count",0) for m in moves))
        top=moves[0]
        # uncertainty = user changes move often; useful training target
        consistency=top.get("count",0)/total
        score=rec.get("games",0)*(1.35-consistency)
        rows.append((score,rec,moves))
    return sorted(rows,key=lambda x:(x[0],x[1].get("games",0)),reverse=True)


def open_repertoire_drill():
    rep=load_repertoire()
    rows=repertoire_position_rows(rep)
    if not rows:
        messagebox.showinfo("Repertoire Drill","Сначала построй репертуар из Chess.com.")
        return

    # prefer positions with at least two observations, then fall back to all
    pool=[r for r in rows if r[1].get("games",0)>=2] or rows
    random.shuffle(pool)

    win=ctk.CTkToplevel(root);win.title("Repertoire Drill • GameCoach 26");win.geometry("760x650")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧠 Repertoire Drill",
                 font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(shell,text="Вспомни ход, который ты чаще всего выбираешь в этой позиции.",
                 text_color=GC_TEXT_MUTED).pack(anchor="w",padx=22,pady=(0,12))

    progress=ctk.CTkLabel(shell,text="");progress.pack(anchor="w",padx=22)
    line_label=ctk.CTkLabel(shell,text="",wraplength=680,justify="left",
                            font=ctk.CTkFont(size=16,weight="bold"))
    line_label.pack(anchor="w",padx=22,pady=(12,10))
    answer_frame=ctk.CTkFrame(shell,fg_color="transparent");answer_frame.pack(fill="x",padx=22,pady=8)
    feedback=ctk.CTkLabel(shell,text="",wraplength=680,justify="left");feedback.pack(anchor="w",padx=22,pady=12)

    state={"i":0,"correct":0,"wrong":0}

    def show():
        for w in answer_frame.winfo_children():w.destroy()
        if state["i"]>=min(10,len(pool)):
            feedback.configure(text=f"🏁 Готово: {state['correct']} верно • {state['wrong']} ошибок")
            line_label.configure(text="Тренировка репертуара завершена.")
            progress.configure(text="")
            return
        _,rec,moves=pool[state["i"]]
        progress.configure(text=f"Позиция {state['i']+1}/{min(10,len(pool))}")
        prefix=rec.get("prefix","") or "Начальная позиция"
        line_label.configure(text=f"Линия:\n{prefix}\n\nТвой ход ({'белые' if rec.get('color')=='white' else 'чёрные'}). Что сыграешь?")
        feedback.configure(text="")

        # top moves from own games + legal distractors
        choices=moves[:4]
        labels=[m.get("san",m.get("uci","")) for m in choices]
        if len(labels)<3:
            try:
                b=chess.Board(rec["fen"])
                for mv in list(b.legal_moves):
                    san=b.san(mv)
                    if san not in labels:
                        labels.append(san)
                    if len(labels)>=4:break
            except Exception:pass
        random.shuffle(labels)
        target=moves[0].get("san",moves[0].get("uci",""))

        def choose(label):
            if label==target:
                state["correct"]+=1;safe_beep("correct")
                txt=f"✅ Да. Твой основной ход: {target} ({moves[0].get('count',0)} раз)."
            else:
                state["wrong"]+=1;safe_beep("wrong")
                txt=f"❌ В твоих партиях основной ход: {target} ({moves[0].get('count',0)} раз)."
            if len(moves)>1:
                alts=", ".join(f"{m.get('san')} ×{m.get('count',0)}" for m in moves[1:4])
                txt+=f"\nДругие твои ходы: {alts}"
            feedback.configure(text=txt)
            for w in answer_frame.winfo_children():w.configure(state="disabled")
            ctk.CTkButton(answer_frame,text="Следующая ▶",
                          command=lambda:(state.__setitem__("i",state["i"]+1),show()),
                          fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER).pack(fill="x",pady=(10,0))

        for lab in labels:
            ctk.CTkButton(answer_frame,text=lab,command=lambda x=lab:choose(x),
                          height=42,fg_color="#444B45",hover_color="#565E57").pack(fill="x",pady=4)
    show()


def open_opening_repertoire():
    rep=load_repertoire()
    win=ctk.CTkToplevel(root);win.title("Opening Repertoire • GameCoach 26");win.geometry("900x760")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(shell,text="📚 Opening Repertoire 26.0",
                 font=ctk.CTkFont(family="Segoe UI",size=28,weight="bold")).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(shell,text="Строится из твоих собственных партий Chess.com. Это личное дерево ходов, а не готовая ECO-база.",
                 text_color=GC_TEXT_MUTED,wraplength=820,justify="left").pack(anchor="w",padx=22,pady=(0,14))

    top=ctk.CTkFrame(shell,fg_color="transparent");top.pack(fill="x",padx=22,pady=(0,10))
    ctk.CTkButton(top,text="🔄 Построить из последних партий",command=start_build_repertoire,
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER).pack(side="left")
    ctk.CTkButton(top,text="🧠 Repertoire Drill",command=open_repertoire_drill,
                  fg_color="#6B5B3E",hover_color="#806D49").pack(side="left",padx=8)

    if not rep:
        ctk.CTkLabel(shell,text="Репертуар ещё не создан. Введи ник Chess.com и нажми кнопку выше.",
                     text_color="#D9B56C").pack(anchor="w",padx=22,pady=20)
        return

    games=rep.get("games_used",0);positions=rep.get("positions",{})
    ctk.CTkLabel(shell,text=f"Игрок: {rep.get('username','—')} • партий: {games} • уникальных позиций: {len(positions)}",
                 font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=22,pady=(2,8))

    openings=Counter(rep.get("openings",{}))
    if openings:
        text="Популярные дебюты:  "+ "   •   ".join(f"{k}: {v}" for k,v in openings.most_common(5))
        ctk.CTkLabel(shell,text=text,wraplength=820,justify="left",text_color="#BFC8D0").pack(anchor="w",padx=22,pady=(0,10))

    tabs=ctk.CTkTabview(shell);tabs.pack(fill="both",expand=True,padx=22,pady=(4,18))
    for tab_name,color_filter in [("Белыми","white"),("Чёрными","black"),("Точки выбора",None)]:
        tab=tabs.add(tab_name)
        scroll=ctk.CTkScrollableFrame(tab,fg_color="transparent");scroll.pack(fill="both",expand=True,padx=6,pady=6)
        rows=repertoire_position_rows(rep,color_filter)
        if tab_name=="Точки выбора":
            rows=[r for r in rows if len(r[1].get("moves",{}))>1]
        if not rows:
            ctk.CTkLabel(scroll,text="Пока нет данных.").pack(anchor="w",padx=10,pady=12)
        for _,rec,moves in rows[:20]:
            card=ctk.CTkFrame(scroll,corner_radius=12,fg_color=GC_PANEL_2);card.pack(fill="x",pady=5)
            prefix=rec.get("prefix","") or "Старт"
            top=moves[0];total=max(1,sum(m.get("count",0) for m in moves))
            consistency=100*top.get("count",0)/total
            ctk.CTkLabel(card,text=prefix[:80],font=ctk.CTkFont(size=14,weight="bold"),
                         wraplength=520,justify="left").pack(anchor="w",padx=14,pady=(10,2))
            move_text=" • ".join(f"{m.get('san')} ×{m.get('count',0)}" for m in moves[:4])
            ctk.CTkLabel(card,text=f"{move_text}\nОсновной ход: {top.get('san')} • стабильность {consistency:.0f}% • партий {rec.get('games',0)}",
                         text_color="#B7C0C9",wraplength=760,justify="left").pack(anchor="w",padx=14,pady=(0,10))


def opening_summary_from_current_game():
    if not game_moves:return ("Нет партии",[])
    b=chess.Board(); sans=[]
    for mv in game_moves[:12]:
        try:sans.append(b.san(mv));b.push(mv)
        except Exception:break
    name="Дебют из текущей партии"
    seq=" ".join(sans[:10])
    # Lightweight common-family identification; deliberately not pretending to be a full opening DB.
    if len(sans)>=2:
        if sans[0]=="e4" and sans[1]=="c5":name="Сицилианская защита"
        elif sans[0]=="e4" and sans[1]=="e5":name="Открытая игра"
        elif sans[0]=="d4" and sans[1]=="d5":name="Ферзевые начала"
        elif sans[0]=="d4" and sans[1]=="Nf6":name="Индийские защиты"
        elif sans[0]=="e4" and sans[1]=="e6":name="Французская защита"
        elif sans[0]=="e4" and sans[1]=="c6":name="Каро-Канн"
    return name,sans


def open_opening_coach():
    name,sans=opening_summary_from_current_game()
    win=ctk.CTkToplevel(root);win.title("Opening Coach");win.geometry("720x560")
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="📚 Opening Coach",font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(shell,text=name,font=ctk.CTkFont(size=19,weight="bold"),text_color="#73D6A4").pack(anchor="w",padx=22,pady=(6,4))
    ctk.CTkLabel(shell,text=" ".join(sans[:12]) if sans else "Сначала загрузи партию.",
                 wraplength=630,justify="left",text_color="#C5CCD4").pack(anchor="w",padx=22,pady=(0,16))
    opening_moves=[d for d in analysed_moves if str(d.get("phase","")).lower()=="дебют"]
    if opening_moves:
        bad=[d for d in opening_moves if d.get("loss",0)>=70]
        avg=sum(d.get("loss",0) for d in opening_moves)/max(1,len(opening_moves))
        txt=f"Проанализировано ходов в дебютной фазе: {len(opening_moves)}\nЗаметных неточностей: {len(bad)}\nСредняя потеря оценки: {avg/100:.2f}"
    else:
        txt="После анализа партии здесь появятся данные по дебютной фазе."
    ctk.CTkLabel(shell,text=txt,justify="left",wraplength=630).pack(anchor="w",padx=22,pady=8)
    ctk.CTkButton(shell,text="🎬 Review дебюта",command=open_review_mode,fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER).pack(anchor="w",padx=22,pady=16)
    ctk.CTkButton(shell,text="📚 Мой репертуар",command=open_opening_repertoire,fg_color="#6B5B3E",hover_color="#806D49").pack(anchor="w",padx=22,pady=(0,16))


def open_endgame_coach():
    positions=endgame_positions_from_analysis()
    win=ctk.CTkToplevel(root)
    win.title("Endgame Coach Pro • GameCoach 27.0")
    win.geometry("900x760")
    win.minsize(780,650)

    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="🏁 Endgame Coach Pro 27.0",
        font=ctk.CTkFont(family="Segoe UI",size=28,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,
        text="Находит окончания в твоей проанализированной партии, показывает ошибки и позволяет переиграть позицию против Stockfish.",
        text_color=GC_TEXT_MUTED,wraplength=820,justify="left"
    ).pack(anchor="w",padx=22,pady=(0,14))

    stats=load_endgame_profile().get("stats",{})
    top=ctk.CTkFrame(shell,fg_color="transparent")
    top.pack(fill="x",padx=22,pady=(0,10))

    ctk.CTkButton(
        top,text="🎯 Тренировать случайный эндшпиль",
        command=open_random_endgame_drill,
        fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER
    ).pack(side="left")

    ctk.CTkButton(
        top,text="📊 Мои результаты",
        command=open_endgame_progress,
        fg_color="#6B5B3E",hover_color="#806D49"
    ).pack(side="left",padx=8)

    if not positions:
        ctk.CTkLabel(
            shell,
            text="В текущей проанализированной партии подходящих эндшпильных позиций пока не найдено.",
            text_color="#D9B56C",wraplength=800,justify="left"
        ).pack(anchor="w",padx=22,pady=24)
        return

    counts=Counter(p["kind"] for p in positions)
    errors=Counter(p["kind"] for p in positions if p["loss"]>=70)

    summary="   •   ".join(f"{k}: {v} поз." for k,v in counts.most_common())
    ctk.CTkLabel(shell,text=summary,wraplength=820,justify="left",
                 font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=22,pady=(4,10))

    tabs=ctk.CTkTabview(shell)
    tabs.pack(fill="both",expand=True,padx=22,pady=(0,18))

    for tab_name,filter_mode in [("Все","all"),("Ошибки","errors"),("Типы","types")]:
        tab=tabs.add(tab_name)
        scroll=ctk.CTkScrollableFrame(tab,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=6,pady=6)

        if filter_mode=="types":
            for kind,n in counts.most_common():
                card=ctk.CTkFrame(scroll,corner_radius=12,fg_color=GC_PANEL_2)
                card.pack(fill="x",pady=5)
                att=stats.get(kind,{}).get("attempts",0)
                suc=stats.get(kind,{}).get("success",0)
                rate=(100*suc/att) if att else 0
                ctk.CTkLabel(card,text=kind,font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=14,pady=(11,2))
                ctk.CTkLabel(
                    card,
                    text=f"{n} позиций • ошибок {errors[kind]} • тренировок {att} • успех {rate:.0f}%",
                    text_color="#B7C0C9"
                ).pack(anchor="w",padx=14,pady=(0,11))
            continue

        rows=positions if filter_mode=="all" else [p for p in positions if p["loss"]>=70]
        rows=sorted(rows,key=lambda p:(p["loss"],abs(p["before_cp"]-p["after_cp"])),reverse=True)
        if not rows:
            ctk.CTkLabel(scroll,text="Нет подходящих позиций.").pack(anchor="w",padx=10,pady=12)
        for p in rows[:30]:
            card=ctk.CTkFrame(scroll,corner_radius=12,fg_color=GC_PANEL_2)
            card.pack(fill="x",pady=5)

            left=ctk.CTkFrame(card,fg_color="transparent")
            left.pack(side="left",fill="x",expand=True,padx=14,pady=10)
            ctk.CTkLabel(
                left,
                text=f"{p['kind']} • {p['move_label']} {p['san']}",
                font=ctk.CTkFont(size=15,weight="bold")
            ).pack(anchor="w")
            wmat,bmat=p["material"]
            ctk.CTkLabel(
                left,
                text=f"Потеря {p['loss']/100:.2f} • материал Б {wmat} / Ч {bmat} • ход {'белых' if p['turn']=='white' else 'чёрных'}",
                text_color="#AAB2BC"
            ).pack(anchor="w",pady=(2,0))

            def launch(i=p["index"],w=win):
                global current_ply_index
                current_ply_index=i
                try:go_to_ply(i)
                except Exception:pass
                w.destroy()
                replay_position_vs_stockfish()

            ctk.CTkButton(
                card,text="▶ Переиграть",command=launch,
                fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,width=115
            ).pack(side="right",padx=12,pady=10)


def open_random_endgame_drill():
    positions=endgame_positions_from_analysis()
    if not positions:
        messagebox.showinfo("Endgame Coach Pro","Сначала проанализируй партию с эндшпилем.")
        return

    # Prefer actual endgame mistakes; otherwise any endgame position.
    pool=[p for p in positions if p["loss"]>=70] or positions
    p=random.choice(pool)

    global current_ply_index
    current_ply_index=p["index"]
    try:go_to_ply(current_ply_index)
    except Exception:pass

    win=ctk.CTkToplevel(root)
    win.title("Endgame Drill")
    win.geometry("700x560")
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="🏁 Endgame Drill",
        font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,
        text=f"{p['kind']} • позиция перед ходом {p['move_label']} {p['san']}",
        text_color="#D9B56C",font=ctk.CTkFont(size=16,weight="bold")
    ).pack(anchor="w",padx=22,pady=(2,12))

    cp=p["before_cp"]
    if abs(cp)<=80:
        goal="Удержи равную позицию. Не допускай ухудшения больше примерно одной пешки."
    elif cp>80:
        goal="У тебя преимущество. Постарайся сохранить и реализовать его."
    else:
        goal="Ты хуже. Цель — максимально усложнить игру и улучшить оценку."

    ctk.CTkLabel(
        shell,text=goal,wraplength=620,justify="left",
        font=ctk.CTkFont(size=15)
    ).pack(anchor="w",padx=22,pady=(0,14))

    tips={
        "Пешечный эндшпиль":"Проверь оппозицию королей, проходные пешки и темпы.",
        "Ладейный эндшпиль":"Активность ладьи и короля обычно важнее пассивной защиты пешек.",
        "Слоновый эндшпиль":"Следи за цветом полей, проходными и активностью короля.",
        "Коневой эндшпиль":"Коню нужны устойчивые поля; король должен быть активным.",
        "Ферзевый эндшпиль":"Король уязвим: сначала проверяй шахи и вечный шах.",
        "Ладья + лёгкая фигура":"Согласуй фигуры и не оставляй короля без защиты.",
        "Эндшпиль лёгких фигур":"Сравни активность королей и слабые пешки."
    }
    ctk.CTkLabel(
        shell,text="💡 "+tips.get(p["kind"],"Активизируй короля и ищи проходные пешки."),
        text_color="#B7C0C9",wraplength=620,justify="left"
    ).pack(anchor="w",padx=22,pady=(0,18))

    ctk.CTkButton(
        shell,text="🎯 Переиграть против Stockfish",
        command=lambda:(win.destroy(),replay_position_vs_stockfish()),
        fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=44
    ).pack(fill="x",padx=22,pady=6)

    ctk.CTkButton(
        shell,text="🧩 Сначала решить лучший ход",
        command=lambda:(win.destroy(),solve_current_position()),
        fg_color="#6B5B3E",hover_color="#806D49",height=42
    ).pack(fill="x",padx=22,pady=6)


def open_endgame_progress():
    data=load_endgame_profile()
    stats=data.get("stats",{})
    win=ctk.CTkToplevel(root)
    win.title("Endgame Progress")
    win.geometry("720x600")
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL)
    shell.pack(fill="both",expand=True,padx=16,pady=16)

    ctk.CTkLabel(
        shell,text="📊 Endgame Progress",
        font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold")
    ).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(
        shell,text="Статистика именно тренировок Endgame Coach Pro, а не шахматный рейтинг.",
        text_color=GC_TEXT_MUTED,wraplength=640,justify="left"
    ).pack(anchor="w",padx=22,pady=(0,14))

    if not stats:
        ctk.CTkLabel(
            shell,text="Пока нет завершённых эндшпильных тренировок.",
            text_color="#D9B56C"
        ).pack(anchor="w",padx=22,pady=20)
        return

    scroll=ctk.CTkScrollableFrame(shell,fg_color="transparent")
    scroll.pack(fill="both",expand=True,padx=18,pady=8)

    for kind,row in sorted(stats.items(),key=lambda kv:kv[1].get("attempts",0),reverse=True):
        att=int(row.get("attempts",0))
        suc=int(row.get("success",0))
        rate=100*suc/att if att else 0
        avg_delta=float(row.get("delta_total",0))/att if att else 0
        card=ctk.CTkFrame(scroll,corner_radius=12,fg_color=GC_PANEL_2)
        card.pack(fill="x",pady=5)
        ctk.CTkLabel(card,text=kind,font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=14,pady=(10,2))
        ctk.CTkLabel(
            card,
            text=f"Попыток: {att} • успешных: {suc} • успех: {rate:.0f}% • среднее изменение: {avg_delta/100:+.2f}",
            text_color="#B7C0C9"
        ).pack(anchor="w",padx=14,pady=(0,10))



def open_player_hub():
    win=ctk.CTkToplevel(root);win.title("Player Intelligence Hub");win.geometry("760x600")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧬 Player Intelligence",font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,text="GameCoach связывает ошибки, фазы партии и тренировки в единый профиль прогресса.",
                 text_color=GC_TEXT_MUTED).pack(anchor="w",padx=22,pady=(0,16))
    items=[("🧬 Профиль игрока","Skill Scores и повторяющиеся ошибки",open_player_intelligence),
           ("📚 Opening Coach","Разбор дебютной фазы текущей партии",open_opening_coach),
           ("🏁 Endgame Coach Pro","Переигрывание и тренировка собственных окончаний",open_endgame_coach),
           ("📈 Progress Intelligence","Сравнение периодов и недельный отчёт",open_quality_progress)]
    for title,desc,cmd in items:
        card=ctk.CTkFrame(shell,corner_radius=12,fg_color=GC_PANEL_2);card.pack(fill="x",padx=22,pady=6)
        ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=14,pady=(11,2))
        ctk.CTkLabel(card,text=desc,text_color="#AAB2BC").pack(anchor="w",padx=14,pady=(0,7))
        ctk.CTkButton(card,text="Открыть",command=cmd,fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=32).pack(anchor="e",padx=14,pady=(0,10))



def open_what_did_i_miss():
    """Turn the selected mistake into a diagnosis exercise before revealing the answer."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери проанализированный ход.");return
    d=analysed_moves[current_ply_index]
    before=chess.Board(d["fen"])
    lessons=detect_position_lessons(before,d["move"],d.get("best_move"),d["mover_color"])
    win=ctk.CTkToplevel(root);win.title("Что я пропустил?");win.geometry("690x570")
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="👁 Что ты пропустил?",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=22,pady=(20,4))
    ctk.CTkLabel(shell,text=f"Ход {d.get('move_label','')} {d.get('san','')}. Не смотри лучший ход — сначала поставь диагноз.",
                 text_color=GC_TEXT_MUTED,wraplength=610,justify="left").pack(anchor="w",padx=22,pady=(0,16))
    out=ctk.CTkTextbox(shell,height=190,wrap="word",font=("Segoe UI",14));out.pack(fill="both",expand=True,padx=22,pady=10)
    mapping={
        "Шах":["пропущенный шах","форсированный шах"],
        "Взятие":["пропущенное взятие","расчёт размена"],
        "Висящая фигура":["незащищённая фигура","проверка безопасности фигуры"],
        "Ответ соперника":["проверка ответа соперника"],
        "Другое":[]
    }
    def choose(label):
        hit=any(x in lessons for x in mapping[label])
        out.delete("1.0","end")
        if hit:
            out.insert("1.0",f"✅ Хороший диагноз: {label}.\n\nТемы GameCoach: "+(" • ".join(lessons) if lessons else "общая проверка позиции"))
            safe_beep("correct");award_learning_xp(True)
        else:
            out.insert("1.0",f"Не похоже, что «{label}» — главная тема этой позиции.\n\nПопробуй ещё раз, прежде чем открывать разбор.")
            safe_beep("wrong")
    grid=ctk.CTkFrame(shell,fg_color="transparent");grid.pack(fill="x",padx=22,pady=8)
    for i,label in enumerate(mapping):
        ctk.CTkButton(grid,text=label,command=lambda x=label:choose(x),fg_color="#3A433D",hover_color="#4A5B50").grid(row=i//2,column=i%2,sticky="ew",padx=4,pady=4)
    grid.grid_columnconfigure((0,1),weight=1)
    ctk.CTkButton(shell,text="Открыть полный разбор",command=lambda:(win.destroy(),enhanced_why_current_move()),
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER,height=40).pack(fill="x",padx=22,pady=(8,18))


def open_blind_review():
    """Review key moments without showing engine evaluation first."""
    if not analysed_moves:
        messagebox.showinfo("GameCoach","Сначала проанализируй партию.");return
    moments=get_key_moments(8)
    if not moments:
        messagebox.showinfo("GameCoach","Ключевые моменты не найдены.");return
    # Reuse robustly: extract any integer that is a valid analysed_moves index.
    indexes=[]
    for m in moments:
        vals=m if isinstance(m,(list,tuple)) else [m]
        idx=next((x for x in vals if isinstance(x,int) and 0<=x<len(analysed_moves)),None)
        if idx is not None and idx not in indexes:indexes.append(idx)
    if not indexes:return
    win=ctk.CTkToplevel(root);win.title("Blind Review");win.geometry("700x560")
    state={"n":0}
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    title=ctk.CTkLabel(shell,text="🕵 Blind Review",font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold"));title.pack(anchor="w",padx=22,pady=(20,4))
    text=ctk.CTkTextbox(shell,wrap="word",font=("Segoe UI",15));text.pack(fill="both",expand=True,padx=22,pady=12)
    def show():
        idx=indexes[state["n"]];d=analysed_moves[idx]
        draw_board(chess.Board(d["fen"]))
        text.delete("1.0","end")
        text.insert("1.0",f"Момент {state['n']+1}/{len(indexes)}\n\nПозиция показана на главной доске ПЕРЕД ходом.\n\nОценка и лучший ход скрыты.\n\n1. Что угрожает соперник?\n2. Назови 2–3 кандидата.\n3. Какой ход выберешь?\n\nКогда готов — открой диагноз или разбор.")
    def nxt():
        if state["n"]<len(indexes)-1:state["n"]+=1;show()
        else:messagebox.showinfo("Blind Review","✅ Все выбранные моменты просмотрены.",parent=win)
    row=ctk.CTkFrame(shell,fg_color="transparent");row.pack(fill="x",padx=22,pady=(0,18))
    ctk.CTkButton(row,text="👁 Диагноз",command=open_what_did_i_miss,fg_color="#6B5B3E",hover_color="#806D49").pack(side="left",padx=(0,5))
    ctk.CTkButton(row,text="❓ Разбор",command=enhanced_why_current_move,fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER).pack(side="left",padx=5)
    ctk.CTkButton(row,text="Следующий ▶",command=nxt).pack(side="right")
    show()



# ============================================================
# GAMECOACH 24 — PERSONAL PUZZLE LAB
# ============================================================

def puzzle_difficulty(item):
    loss=float(item.get("loss",0) or 0)
    return 1 if loss<80 else 2 if loss<150 else 3 if loss<250 else 4 if loss<400 else 5


def current_as_puzzle():
    if current_ply_index<0 or current_ply_index>=len(analysed_moves):return None
    d=analysed_moves[current_ply_index]
    if not d.get("best_move"):return None
    return {"fen":d["fen"],"best_move":d["best_move"].uci(),"played_move":d["move"].uci(),
            "played_san":d.get("san",""),"best_san":d.get("best_san",""),"loss":d.get("loss",0),
            "phase":d.get("phase",""),"user_color":"white" if d["mover_color"]==chess.WHITE else "black",
            "source":"analysis","created":datetime.now().isoformat(timespec="seconds")}


def generate_puzzles_from_analysis():
    global saved_training_positions
    if not analysed_moves:
        messagebox.showinfo("GameCoach","Сначала проанализируй партию.");return
    added=0
    for d in analysed_moves:
        if float(d.get("loss",0) or 0)<70 or not d.get("best_move"):continue
        item={"fen":d["fen"],"best_move":d["best_move"].uci(),"played_move":d["move"].uci(),
              "played_san":d.get("san",""),"best_san":d.get("best_san",""),"loss":d.get("loss",0),
              "phase":d.get("phase",""),"user_color":"white" if d["mover_color"]==chess.WHITE else "black",
              "source":"auto-puzzle","created":datetime.now().isoformat(timespec="seconds")}
        if persist_training_item(item,"auto-puzzle"):added+=1
    messagebox.showinfo("Puzzle Lab",f"🧩 Добавлено новых задач: {added}\nВсего в личной библиотеке: {len(saved_training_positions)}")


def open_timed_puzzle():
    global training_active,training_positions,training_index,player_color_global
    pool=list(saved_training_positions) or list(training_positions)
    if not pool:
        messagebox.showinfo("Puzzle Lab","Сначала создай задачи из проанализированной партии.");return
    item=random.choice(pool)
    training_positions=[item];training_index=0;training_active=True
    player_color_global=chess.WHITE if item.get("user_color","white")=="white" else chess.BLACK
    started=time.time()
    item["_timer_started"]=started
    item["_first_try"]=True
    item["_hint_used"]=False
    show_training_position()
    training_status.configure(text=f"⏱ Задача началась • сложность {puzzle_difficulty(item)}/5 • {item.get('phase','')}\nНайди сильный ход без подсказки.")


def replay_position_vs_stockfish():
    """Replay the selected analysed position against Stockfish from its exact FEN."""
    if current_ply_index < 0 or current_ply_index >= len(analysed_moves):
        messagebox.showinfo("GameCoach","Сначала выбери проанализированный ход или критическую позицию.")
        return
    if not ensure_stockfish_path():
        return

    d = analysed_moves[current_ply_index]
    try:
        start_board = chess.Board(d["fen"])
    except Exception:
        messagebox.showerror("Replay Trainer","Не удалось открыть FEN выбранной позиции.")
        return

    human = start_board.turn
    original_move = d.get("move")
    original_san = d.get("san","")
    original_after = float(d.get("after_cp",0) or 0)
    original_before = float(d.get("before_cp",0) or 0)

    win = ctk.CTkToplevel(root)
    win.title("Replay Trainer • GameCoach 27.0")
    win.geometry("1210x820")
    win.minsize(1030, 700)

    state = {
        "board": start_board.copy(),
        "start_fen": start_board.fen(),
        "human": human,
        "selected": None,
        "thinking": False,
        "engine": None,
        "last_move": None,
        "human_moves": 0,
        "max_human_moves": 8,
        "start_cp": None,
        "current_cp": None,
        "best_attempt_cp": None,
        "finished": False,
        "attempt": 1,
        "history": [],
    }

    top = ctk.CTkFrame(win, fg_color="transparent")
    top.pack(fill="x", padx=18, pady=(14,6))
    ctk.CTkLabel(
        top, text="🎯 Replay Trainer",
        font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
    ).pack(side="left")

    level_var = tk.StringVar(value="Средний")
    ctk.CTkLabel(top,text="Stockfish").pack(side="left",padx=(30,6))
    level_menu = ctk.CTkOptionMenu(
        top, values=["Лёгкий","Средний","Сильный","Очень сильный"],
        variable=level_var, width=140
    )
    level_menu.pack(side="left")

    goal_label = ctk.CTkLabel(
        top, text="Определяю цель…", text_color="#D9B56C",
        font=ctk.CTkFont(size=14,weight="bold")
    )
    goal_label.pack(side="right",padx=8)

    left = ctk.CTkFrame(win, fg_color="transparent")
    left.pack(side="left",fill="both",padx=(18,8),pady=(8,18))
    right = ctk.CTkFrame(win,corner_radius=17,fg_color=GC_PANEL)
    right.pack(side="right",fill="both",expand=True,padx=(8,18),pady=(8,18))

    size=620
    sqs=size/8
    canvas=tk.Canvas(left,width=size,height=size,highlightthickness=0)
    canvas.pack()

    status=ctk.CTkLabel(
        left,text="Позиция загружена.",font=ctk.CTkFont(size=14,weight="bold")
    )
    status.pack(pady=(10,2))

    ctk.CTkLabel(
        right,text="Сыграй позицию лучше",
        font=ctk.CTkFont(family="Segoe UI",size=22,weight="bold")
    ).pack(anchor="w",padx=18,pady=(18,4))

    info=ctk.CTkTextbox(right,wrap="word",font=("Segoe UI",14),corner_radius=12)
    info.pack(fill="both",expand=True,padx=18,pady=(6,12))

    controls=ctk.CTkFrame(right,fg_color="transparent")
    controls.pack(fill="x",padx=18,pady=(0,8))
    controls2=ctk.CTkFrame(right,fg_color="transparent")
    controls2.pack(fill="x",padx=18,pady=(0,16))

    refs=[]

    def depth_value():
        return {"Лёгкий":6,"Средний":9,"Сильный":12,"Очень сильный":15}.get(level_var.get(),9)

    def human_flipped():
        return state["human"] == chess.BLACK

    def square_xy(square):
        f=chess.square_file(square); r=chess.square_rank(square)
        if human_flipped():
            f=7-f; r=7-r
        return f*sqs,(7-r)*sqs

    def event_square(event):
        c=int(event.x//sqs); rr=int(event.y//sqs)
        if not (0<=c<8 and 0<=rr<8): return None
        if human_flipped():
            f=7-c; rank=rr
        else:
            f=c; rank=7-rr
        return chess.square(f,rank)

    def piece_photo(symbol):
        filename=PIECE_MAP.get(symbol)
        if not filename:return None
        path=os.path.join(PIECES_FOLDER,filename+".png")
        if not os.path.exists(path):return None
        im=Image.open(path).convert("RGBA")
        im.thumbnail((int(sqs*.90),int(sqs*.90)),Image.Resampling.LANCZOS)
        cell=Image.new("RGBA",(int(sqs),int(sqs)),(0,0,0,0))
        cell.alpha_composite(im,((cell.width-im.width)//2,(cell.height-im.height)//2))
        cell=_styled_piece_image(cell,app_settings.get("piece_style","Wikipedia"))
        photo=ImageTk.PhotoImage(cell);refs.append(photo);return photo

    def redraw():
        canvas.delete("all");refs.clear()
        b=state["board"]; theme=current_board_theme()
        for sq in chess.SQUARES:
            x,y=square_xy(sq)
            light=(chess.square_file(sq)+chess.square_rank(sq))%2==1
            fill=theme["light"] if light else theme["dark"]
            if state["last_move"] and sq in (state["last_move"].from_square,state["last_move"].to_square):
                fill=theme["last_light"] if light else theme["last_dark"]
            if state["selected"]==sq:
                fill=theme.get("select","#D89B3C")
            canvas.create_rectangle(x,y,x+sqs,y+sqs,fill=fill,outline="")
        if state["selected"] is not None:
            for m in b.legal_moves:
                if m.from_square==state["selected"]:
                    x,y=square_xy(m.to_square)
                    canvas.create_oval(x+sqs*.40,y+sqs*.40,x+sqs*.60,y+sqs*.60,
                                       fill=theme.get("legal","#445"),outline="")
        for sq,p in b.piece_map().items():
            x,y=square_xy(sq);ph=piece_photo(p.symbol())
            if ph:canvas.create_image(x+sqs/2,y+sqs/2,image=ph)
        # coordinates
        for i in range(8):
            file_i=7-i if human_flipped() else i
            rank_i=i+1 if human_flipped() else 8-i
            canvas.create_text(i*sqs+5,size-10,text=chess.FILE_NAMES[file_i],
                               anchor="sw",fill="#20251F",font=("Segoe UI",9,"bold"))
            canvas.create_text(4,i*sqs+4,text=str(rank_i),anchor="nw",
                               fill="#20251F",font=("Segoe UI",9,"bold"))

    def set_info(text):
        info.configure(state="normal");info.delete("1.0","end");info.insert("1.0",text);info.configure(state="disabled")

    def cp_text(cp):
        if cp is None:return "…"
        if abs(cp)>=90000:return "мат"
        return f"{cp/100:+.2f}"

    def goal_from_cp(cp):
        if cp is None:return "Сыграй позицию максимально точно"
        if abs(cp)<=80:return "🎯 Цель: удержать/улучшить равную позицию"
        if cp>80:return "🎯 Цель: реализовать преимущество"
        return "🎯 Цель: защититься и улучшить позицию"

    def evaluation_summary():
        startcp=state["start_cp"];cur=state["current_cp"]
        if startcp is None or cur is None:return ""
        delta=cur-startcp
        old_delta=cur-original_after
        return (
            f"Стартовая оценка: {cp_text(startcp)}\n"
            f"Текущая оценка: {cp_text(cur)}\n"
            f"Изменение относительно старта: {delta/100:+.2f}\n"
            f"Оригинальный ход {original_san or '—'} оставил примерно: {cp_text(original_after)}\n"
            f"Сравнение с исходной партией: {old_delta/100:+.2f}\n"
        )

    def finish_replay(reason=""):
        if state["finished"]:return
        state["finished"]=True
        finalcp=state["current_cp"]
        if finalcp is not None:
            best=state["best_attempt_cp"]
            if best is None or finalcp>best:state["best_attempt_cp"]=finalcp
        text="🏁 Попытка завершена.\n\n"+evaluation_summary()
        if reason:text+="\n"+reason
        if finalcp is not None and state["start_cp"] is not None:
            delta=finalcp-state["start_cp"]
            success = delta >= -100
            if delta>=-30:text+="\n\n✅ Ты сохранил качество позиции."
            elif delta>=-100:text+="\n\n👍 Позиция ухудшилась немного."
            else:text+="\n\n⚠ Позиция заметно ухудшилась. Попробуй ещё раз."
            try:
                eg_kind=classify_endgame(chess.Board(state["start_fen"]))
                if eg_kind:
                    save_endgame_attempt(eg_kind,success,delta)
                    text+=f"\n\n🏁 Endgame Coach: результат сохранён в «{eg_kind}»."
            except Exception:
                pass
        set_info(text)
        status.configure(text="Попытка завершена • Restart — сыграть снова")

    def eval_async(callback=None):
        if state["thinking"]:return
        state["thinking"]=True
        board_copy=state["board"].copy()
        human_color=state["human"]
        dep=depth_value()
        def worker():
            cp=None
            try:
                eng=state["engine"]
                if eng is None:
                    eng=launch_stockfish_engine();state["engine"]=eng
                inf=eng.analyse(board_copy,chess.engine.Limit(depth=dep))
                cp=score_cp_for_color(inf,human_color)
            except Exception:
                cp=None
            def done():
                state["thinking"]=False
                if not win.winfo_exists():return
                if cp is not None:
                    state["current_cp"]=cp
                    if state["start_cp"] is None:
                        state["start_cp"]=cp
                        goal_label.configure(text=goal_from_cp(cp))
                if callback:callback(cp)
            try:win.after(0,done)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def engine_reply():
        if state["finished"] or state["board"].is_game_over():return
        if state["board"].turn==state["human"]:return
        state["thinking"]=True
        status.configure(text="Stockfish думает…")
        board_copy=state["board"].copy();dep=depth_value()
        def worker():
            mv=None
            try:
                eng=state["engine"]
                if eng is None:
                    eng=launch_stockfish_engine();state["engine"]=eng
                result=eng.play(board_copy,chess.engine.Limit(depth=dep))
                mv=result.move
            except Exception:
                mv=None
            def done():
                state["thinking"]=False
                if not win.winfo_exists():return
                if mv and mv in state["board"].legal_moves:
                    state["board"].push(mv);state["last_move"]=mv;state["history"].append(mv.uci())
                    safe_beep("move");redraw()
                if state["board"].is_game_over():
                    eval_async(lambda cp:finish_replay("Партия закончилась: "+state["board"].result()))
                else:
                    status.configure(text=f"Твой ход • попытка {state['attempt']}")
                    eval_async(lambda cp:set_info("После ответа Stockfish:\n\n"+evaluation_summary()))
            try:win.after(0,done)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def submit_human_move(mv):
        if state["thinking"] or state["finished"]:return
        b=state["board"]
        if mv not in b.legal_moves:return
        try:san=b.san(mv)
        except Exception:san=mv.uci()
        b.push(mv);state["last_move"]=mv;state["selected"]=None
        state["human_moves"]+=1;state["history"].append(mv.uci())
        safe_beep("capture" if b.is_check() else "move")
        redraw();status.configure(text=f"Ты сыграл {san}. Оцениваю…")
        def after_eval(cp):
            set_info(
                f"Ход {state['human_moves']}: {san}\n\n"+evaluation_summary()+
                "\nGameCoach сравнивает позицию с твоей исходной партией, а не требует повторить один PV Stockfish."
            )
            if state["board"].is_game_over():
                finish_replay("Партия закончилась: "+state["board"].result());return
            if state["human_moves"]>=state["max_human_moves"]:
                finish_replay(f"Завершены {state['max_human_moves']} твоих ходов.");return
            engine_reply()
        eval_async(after_eval)

    def on_click(event):
        if state["thinking"] or state["finished"] or state["board"].turn!=state["human"]:return
        sq=event_square(event)
        if sq is None:return
        b=state["board"]
        if state["selected"] is None:
            p=b.piece_at(sq)
            if p and p.color==state["human"]:
                state["selected"]=sq;redraw()
            return
        frm=state["selected"]
        p=b.piece_at(frm)
        mv=chess.Move(frm,sq)
        if p and p.piece_type==chess.PAWN and chess.square_rank(sq) in (0,7):
            mv=chess.Move(frm,sq,promotion=chess.QUEEN)
        if mv in b.legal_moves:
            submit_human_move(mv)
        else:
            p2=b.piece_at(sq)
            state["selected"]=sq if p2 and p2.color==state["human"] else None
            redraw()

    def restart():
        state["board"]=chess.Board(state["start_fen"])
        state["selected"]=None;state["last_move"]=None;state["human_moves"]=0
        state["finished"]=False;state["history"]=[]
        state["attempt"]+=1;state["current_cp"]=state["start_cp"]
        redraw()
        status.configure(text=f"Новая попытка #{state['attempt']} • твой ход")
        set_info(
            f"♻ Позиция восстановлена.\n\nОригинальный ход: {original_san or '—'}\n"
            f"Стартовая оценка: {cp_text(state['start_cp'])}\n\nПопробуй другой план."
        )

    def stop_now():
        eval_async(lambda cp:finish_replay("Ты завершил попытку вручную."))

    def save_attempt():
        item=current_as_puzzle()
        if item:
            item["source"]="replay-25"
            item["replay_moves"]=list(state["history"])
            item["replay_final_cp"]=state["current_cp"]
            item["replay_started_cp"]=state["start_cp"]
            persist_training_item(item,"replay-25")
            messagebox.showinfo("Replay Trainer","Попытка сохранена в личную библиотеку.",parent=win)

    ctk.CTkButton(controls,text="♻ Restart position",command=restart,
                  fg_color="#444B45",hover_color="#565E57").pack(side="left",fill="x",expand=True,padx=(0,4))
    ctk.CTkButton(controls,text="🏁 Завершить",command=stop_now,
                  fg_color="#6B5B3E",hover_color="#806D49").pack(side="left",fill="x",expand=True,padx=4)
    ctk.CTkButton(controls2,text="💾 Сохранить попытку",command=save_attempt,
                  fg_color=GC_ACCENT,hover_color=GC_ACCENT_HOVER).pack(fill="x")

    def close():
        try:
            if state["engine"]:state["engine"].quit()
        except Exception:pass
        win.destroy()

    win.protocol("WM_DELETE_WINDOW",close)
    canvas.bind("<Button-1>",on_click)

    redraw()
    color_name="белыми" if human==chess.WHITE else "чёрными"
    set_info(
        f"Ты играешь {color_name} из реальной позиции своей партии.\n\n"
        f"Оригинальный ход: {original_san or '—'}\n"
        f"GameCoach даст тебе до {state['max_human_moves']} собственных ходов против Stockfish.\n\n"
        "Цель определяется после стартовой оценки."
    )
    status.configure(text="Оцениваю исходную позицию…")
    eval_async(lambda cp:status.configure(text=f"Твой ход • старт {cp_text(cp)}"))



def open_puzzle_lab():
    win=ctk.CTkToplevel(root);win.title("Personal Puzzle Lab");win.geometry("780x650")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🧩 Personal Puzzle Lab",font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,text="Твои собственные ошибки превращаются в задачи с повторением, сложностью и временем решения.",
                 text_color=GC_TEXT_MUTED,wraplength=690,justify="left").pack(anchor="w",padx=22,pady=(0,16))
    stats=ctk.CTkFrame(shell,corner_radius=12,fg_color=GC_PANEL_2);stats.pack(fill="x",padx=22,pady=6)
    ctk.CTkLabel(stats,text=f"Сохранено задач: {len(saved_training_positions)}",font=ctk.CTkFont(size=17,weight="bold")).pack(side="left",padx=16,pady=14)
    due=due_training_count() if training_positions else 0
    ctk.CTkLabel(stats,text=f"На повторение: {due}",text_color="#D9B56C").pack(side="right",padx=16)
    actions=[("✨ Создать задачи из партии",generate_puzzles_from_analysis,GC_ACCENT),
             ("⏱ Случайная задача с таймером",open_timed_puzzle,"#6B5B3E"),
             ("🗂 Открыть библиотеку",open_puzzle_library,"#444B45"),
             ("🎯 Переиграть выбранную позицию",replay_position_vs_stockfish,"#7B4F3E")]
    for title,cmd,color in actions:
        ctk.CTkButton(shell,text=title,command=cmd,fg_color=color,height=43).pack(fill="x",padx=22,pady=6)
    ctk.CTkLabel(shell,text="XP 2.0",font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=22,pady=(18,5))
    ctk.CTkLabel(shell,text="Первая правильная попытка без подсказки даёт максимум XP. "
                 "Повторное решение той же задачи в тот же день больше не фармит XP.",
                 wraplength=680,justify="left",text_color="#B7C0C9").pack(anchor="w",padx=22)



def open_stability_info():
    win=ctk.CTkToplevel(root);win.title("GameCoach 24.1");win.geometry("650x500")
    shell=ctk.CTkFrame(win,corner_radius=18,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🛠 Stability Update 24.1",
                 font=ctk.CTkFont(family="Segoe UI",size=25,weight="bold")).pack(anchor="w",padx=22,pady=(20,6))
    txt=(
        "Что усилено:\\n\\n"
        "• более надёжные callbacks после ошибок Stockfish;\\n"
        "• training_key теперь безопасно работает и со строками, и с chess.Move;\\n"
        "• кандидаты сравниваются через root_moves из одной исходной позиции;\\n"
        "• Puzzle Library делает best-effort запись и в JSON, и в SQLite;\\n"
        "• уменьшены минимальные размеры главного окна для ноутбуков;\\n"
        "• «Calculation tree» переименован в «Линия расчёта», пока нет настоящего ветвления."
    )
    ctk.CTkLabel(shell,text=txt,justify="left",wraplength=580,text_color="#C4CCD4").pack(anchor="w",padx=22,pady=12)



def open_replay_hub():
    win=ctk.CTkToplevel(root);win.title("Replay Trainer 25.0");win.geometry("760x650")
    shell=ctk.CTkFrame(win,corner_radius=20,fg_color=GC_PANEL);shell.pack(fill="both",expand=True,padx=16,pady=16)
    ctk.CTkLabel(shell,text="🎯 Replay Trainer 25.0",
                 font=ctk.CTkFont(family="Segoe UI",size=27,weight="bold")).pack(anchor="w",padx=22,pady=(22,4))
    ctk.CTkLabel(shell,text="Переигрывай реальные позиции своих партий против Stockfish — не только находи один лучший ход.",
                 text_color=GC_TEXT_MUTED,wraplength=680,justify="left").pack(anchor="w",padx=22,pady=(0,14))
    if not analysed_moves:
        ctk.CTkLabel(shell,text="Сначала загрузи и проанализируй партию.",
                     text_color="#D9B56C").pack(anchor="w",padx=22,pady=18)
        return
    moments=get_key_moments(6)
    if not moments:
        ctk.CTkLabel(shell,text="Критические моменты пока не найдены.").pack(anchor="w",padx=22,pady=18)
        return
    scroll=ctk.CTkScrollableFrame(shell,fg_color="transparent");scroll.pack(fill="both",expand=True,padx=18,pady=8)
    for num,(_,idx,label) in enumerate(moments,1):
        d=analysed_moves[idx]
        card=ctk.CTkFrame(scroll,corner_radius=12,fg_color=GC_PANEL_2);card.pack(fill="x",pady=5)
        text=f"{num}. {label} • {d.get('phase','')} • {d.get('san','')} • потеря {float(d.get('loss',0))/100:.2f}"
        ctk.CTkLabel(card,text=text,font=ctk.CTkFont(size=14,weight="bold")).pack(side="left",padx=14,pady=13)
        def launch(i=idx,w=win):
            global current_ply_index
            current_ply_index=i
            try:go_to_ply(i)
            except Exception:pass
            w.destroy()
            replay_position_vs_stockfish()
        ctk.CTkButton(card,text="▶ Переиграть",command=launch,fg_color=GC_ACCENT,
                      hover_color=GC_ACCENT_HOVER,width=120).pack(side="right",padx=12,pady=8)



# ============================================================
# GAMECOACH 30 — UNIFIED MAIN WINDOW
# ============================================================

def show_analysis_page():
    """Return to the primary board + coach workspace."""
    try:
        home_overlay.pack_forget()
    except Exception:
        pass
    try:
        left_panel.pack(side="left",fill="both",expand=True,padx=(0,10))
        right_panel.pack(side="left",fill="both",expand=True,padx=(10,0))
    except Exception:
        pass


def refresh_home_page():
    """Refresh the main dashboard from durable local metrics."""
    try:
        p=adaptive_coach_profile()
        trend=progress_trend_summary()
        m7=db_recent_progress(7)
        m30=db_recent_progress(30)
        profile=load_json(PROFILE_FILE,{})
        games=int(profile.get("games",0))
        due=due_training_count() if training_positions else 0
        xp=int(learning_profile.get("xp",0))
        level=learning_level()
        rec=trend.get("recent",{})
        errors_pg=float(rec.get("errors_pg",0) or 0)

        home_games_value.configure(text=str(games))
        home_errors_value.configure(text=f"{errors_pg:.2f}")
        home_due_value.configure(text=str(due))
        home_level_value.configure(text=f"{level}")

        focus_names={
            "opening":"Дебют",
            "endgame":"Эндшпиль",
            "tactics":"Тактика",
            "calculation":"Расчёт",
            "prevention":"Профилактика",
            "thinking":"Мышление",
        }
        home_focus_title.configure(text=focus_names.get(p.get("mode"),str(p.get("mode","—")).title()))
        acc=p.get("accuracy7")
        acc_txt="нет данных" if acc is None else f"{acc:.0f}%"
        home_focus_text.configure(
            text=f"{p.get('reason','')}\n\n"
                 f"Сложность: {p.get('difficulty','—')} • цель: {p.get('target_count',0)} позиций\n"
                 f"Точность тренировок за 7 дней: {acc_txt}\n"
                 f"{p.get('hint_policy','')}"
        )

        home_trend_title.configure(text=trend.get("direction","Пока недостаточно данных"))
        home_trend_text.configure(
            text=f"Последний блок: {int(rec.get('games',0))} партий • "
                 f"{errors_pg:.2f} ошибок/партию\n"
                 f"Тренировки: 7 дней — {m7['attempts']} попыток; "
                 f"30 дней — {m30['attempts']} попыток"
        )

        home_xp_label.configure(text=f"Level {level} • {xp} XP")
        home_xp_bar.set((xp%250)/250 if xp>=0 else 0)
    except Exception:
        pass


def show_home_page():
    """Show the integrated GameCoach 30 dashboard in the main content area."""
    try:
        left_panel.pack_forget()
        right_panel.pack_forget()
    except Exception:
        pass
    try:
        home_overlay.pack(fill="both",expand=True)
        refresh_home_page()
    except Exception:
        pass


migrate_legacy_user_files()
sys.excepthook = log_unhandled_exception

root = ctk.CTk()
try:
    _icon_path = os.path.join(_program_dir(), "GameCoach.ico")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        _bundled_icon = os.path.join(sys._MEIPASS, "GameCoach.ico")
        if os.path.exists(_bundled_icon):
            _icon_path = _bundled_icon
    if os.path.exists(_icon_path):
        root.iconbitmap(_icon_path)
except Exception:
    pass
root.title(APP_NAME)
ctk.set_appearance_mode("dark")
root.geometry("1480x900")
root.minsize(1120, 700)
root.configure(fg_color="#111411")

def _tk_callback_exception(exc_type, exc_value, exc_tb):
    log_unhandled_exception(exc_type,exc_value,exc_tb)
    try:
        messagebox.showerror(
            "GameCoach",
            "Произошла ошибка. GameCoach сохранил технический журнал в папку данных.\n\n"
            "Открой «О программе» → «Папка данных» и найди gamecoach_error.log."
        )
    except Exception:
        pass

root.report_callback_exception = _tk_callback_exception

main = ctk.CTkFrame(root, fg_color="transparent")
main.pack(fill="both", expand=True, padx=18, pady=18)

topbar = ctk.CTkFrame(main, fg_color="#191D1A", corner_radius=16)
topbar.pack(fill="x", pady=(0, 14))

username_entry = ctk.CTkEntry(topbar, placeholder_text="Твой ник Chess.com", width=180, height=42)
username_entry.pack(side="left", padx=(15, 8), pady=14)

ctk.CTkButton(topbar, text="⚙ Stockfish", command=choose_stockfish, height=42, fg_color="#444B45", hover_color="#565E57").pack(side="left", padx=5)
stockfish_status = ctk.CTkLabel(topbar, text="не выбран", text_color="#888F99")
stockfish_status.pack(side="left", padx=(3, 10))

ctk.CTkButton(topbar, text="📂 PGN", command=lambda:(show_analysis_page(),choose_pgn()), height=42, fg_color="#6B5B3E", hover_color="#806D49").pack(side="left", padx=5)
pgn_status = ctk.CTkLabel(topbar, text="не выбран", text_color="#888F99")
pgn_status.pack(side="left", padx=(3, 10))

chesscom_button = ctk.CTkButton(topbar, text="🌐 Последняя", command=fetch_latest_game, height=42, width=110)
chesscom_button.pack(side="left", padx=5)

profile_button = ctk.CTkButton(topbar, text="🧠 Мой профиль", command=start_profile_analysis, height=42, width=145)
profile_button.pack(side="left", padx=5)

analyse_button = ctk.CTkButton(topbar, text="🚀 Анализировать", command=lambda:(show_analysis_page(),start_single_analysis()), height=44, fg_color=GC_ACCENT, hover_color=GC_ACCENT_HOVER)
analyse_button.pack(side="right", padx=15)

# GameCoach 18 workspace with persistent sidebar navigation
work_area = ctk.CTkFrame(main, fg_color="transparent")
work_area.pack(fill="both", expand=True)

sidebar = ctk.CTkFrame(work_area, width=198, corner_radius=18, fg_color="#171B18")
sidebar.pack(side="left", fill="y", padx=(0, 12))
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar, text="♟ GameCoach",
    font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
).pack(anchor="w", padx=16, pady=(18, 4))
ctk.CTkLabel(
    sidebar, text="RELEASE • 1.0",
    font=ctk.CTkFont(size=10, weight="bold"),
    text_color="#7F8A98"
).pack(anchor="w", padx=16, pady=(0, 14))

def side_button(text, command):
    b=ctk.CTkButton(
        sidebar, text=text, command=command,
        anchor="w", height=40, corner_radius=10,
        fg_color="#22282E", hover_color="#2C5944",
        text_color="#E8ECEF"
    )
    b.pack(fill="x", padx=10, pady=3)
    return b

ctk.CTkLabel(
    sidebar,text="ОСНОВНОЕ",font=ctk.CTkFont(size=10,weight="bold"),
    text_color="#68737E"
).pack(anchor="w",padx=16,pady=(2,4))
side_button("🏠 Главная", open_gamecoach_home)
side_button("🔍 Анализ партии", show_analysis_page)
side_button("🧠 Adaptive Coach", open_adaptive_coach)
side_button("⚔ Играть", open_play_vs_stockfish)

ctk.CTkLabel(
    sidebar,text="ТРЕНИРОВКА",font=ctk.CTkFont(size=10,weight="bold"),
    text_color="#68737E"
).pack(anchor="w",padx=16,pady=(12,4))
side_button("📅 Сегодня", open_daily_session)
side_button("🧩 Puzzle Lab", open_puzzle_lab)
side_button("🎯 Replay Trainer", open_replay_hub)
side_button("📚 Репертуар", open_opening_repertoire)
side_button("🏁 Endgame Pro", open_endgame_coach)

ctk.CTkLabel(
    sidebar,text="РАЗВИТИЕ",font=ctk.CTkFont(size=10,weight="bold"),
    text_color="#68737E"
).pack(anchor="w",padx=16,pady=(12,4))
side_button("🧬 Player Intelligence", open_player_hub)
side_button("📈 Progress Intel", open_quality_progress)
side_button("🧰 Все инструменты", open_analysis_toolbox)
side_button("ℹ О программе", open_about_window)

ctk.CTkFrame(sidebar, height=2, fg_color="#262D36").pack(fill="x", padx=12, pady=12)
side_button("🎨 Оформление", show_appearance_window)
side_button("🛠 Stability", open_stability_info)
side_button("⚙ Настройки", show_settings_window)

ctk.CTkLabel(
    sidebar,
    text="💡 Совет\nСначала подумай сам,\nпотом открывай подсказку.",
    justify="left", text_color="#8994A3",
    font=ctk.CTkFont(size=11)
).pack(side="bottom", anchor="w", padx=16, pady=18)

content = ctk.CTkFrame(work_area, fg_color="transparent")
content.pack(side="left", fill="both", expand=True)


# Main stacked area
main_stack = ctk.CTkFrame(root, fg_color="transparent")
# Old embedded dashboard kept for compatibility but hidden.
# It is now opened from the "Обзор" button in a separate window.
main_stack.grid_rowconfigure(0, weight=1)
main_stack.grid_columnconfigure(0, weight=1)

dashboard_frame = ctk.CTkFrame(main_stack, corner_radius=18, fg_color="#0F141A")
workspace_frame = ctk.CTkFrame(main_stack, corner_radius=18, fg_color="transparent")
dashboard_frame.grid(row=0, column=0, sticky="nsew")
workspace_frame.grid(row=0, column=0, sticky="nsew")

# ---------- Dashboard header ----------
dash_header = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
dash_header.pack(fill="x", padx=24, pady=(24, 14))

ctk.CTkLabel(
    dash_header, text="Твой шахматный обзор",
    font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
).pack(anchor="w")

ctk.CTkLabel(
    dash_header,
    text="Коротко о последних партиях, слабых местах и тренировке.",
    font=ctk.CTkFont(family="Segoe UI", size=14),
    text_color="#9AA4B2"
).pack(anchor="w", pady=(4, 0))

# ---------- Metric cards ----------
cards = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
cards.pack(fill="x", padx=24, pady=(4, 14))

for i in range(4):
    cards.grid_columnconfigure(i, weight=1)

def make_dash_card(parent, col, title):
    card = ctk.CTkFrame(parent, corner_radius=14, fg_color="#171D25")
    card.grid(row=0, column=col, sticky="nsew", padx=6)
    ctk.CTkLabel(
        card, text=title,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        text_color="#8F9AAA"
    ).pack(anchor="w", padx=16, pady=(14, 4))
    value = ctk.CTkLabel(
        card, text="0",
        font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
    )
    value.pack(anchor="w", padx=16, pady=(0, 14))
    return value

dash_games_value = make_dash_card(cards, 0, "ПАРТИЙ")
dash_errors_value = make_dash_card(cards, 1, "ОШИБОК / ПАРТИЮ")
dash_blunders_value = make_dash_card(cards, 2, "ЗЕВКОВ")
dash_due_value = make_dash_card(cards, 3, "НА ПОВТОРЕНИЕ")

# ---------- Two-column insights ----------
insights = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
insights.pack(fill="both", expand=True, padx=24, pady=(0, 14))
insights.grid_columnconfigure(0, weight=1)
insights.grid_columnconfigure(1, weight=1)
insights.grid_rowconfigure(0, weight=1)

left_card = ctk.CTkFrame(insights, corner_radius=14, fg_color="#171D25")
left_card.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=4)

ctk.CTkLabel(
    left_card, text="📈 Форма",
    font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
).pack(anchor="w", padx=18, pady=(18, 8))

dash_progress_label = ctk.CTkLabel(
    left_card, text="GameCoach форма: 0%",
    font=ctk.CTkFont(family="Segoe UI", size=14)
)
dash_progress_label.pack(anchor="w", padx=18, pady=(4, 6))

dash_progress = ctk.CTkProgressBar(left_card, height=12, corner_radius=6)
dash_progress.pack(fill="x", padx=18, pady=(0, 18))
dash_progress.set(0)

ctk.CTkLabel(
    left_card, text="Самая слабая фаза",
    font=ctk.CTkFont(family="Segoe UI", size=12),
    text_color="#8F9AAA"
).pack(anchor="w", padx=18, pady=(6, 2))
dash_weak_value = ctk.CTkLabel(
    left_card, text="—",
    font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
)
dash_weak_value.pack(anchor="w", padx=18, pady=(0, 14))

ctk.CTkLabel(
    left_card, text="Дебют с наибольшим числом ошибок",
    font=ctk.CTkFont(family="Segoe UI", size=12),
    text_color="#8F9AAA"
).pack(anchor="w", padx=18, pady=(4, 2))
dash_opening_value = ctk.CTkLabel(
    left_card, text="—",
    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
    wraplength=420, justify="left"
)
dash_opening_value.pack(anchor="w", padx=18, pady=(0, 18))

right_card = ctk.CTkFrame(insights, corner_radius=14, fg_color="#171D25")
right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 6), pady=4)

ctk.CTkLabel(
    right_card, text="🎓 Тренировка",
    font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
).pack(anchor="w", padx=18, pady=(18, 8))

dash_training_text = ctk.CTkLabel(
    right_card,
    text="Создай профиль по последним партиям, чтобы появились персональные тренировки.",
    font=ctk.CTkFont(family="Segoe UI", size=14),
    text_color="#B5BECA",
    wraplength=430,
    justify="left"
)
dash_training_text.pack(anchor="w", padx=18, pady=(4, 16))

ctk.CTkButton(
    right_card,
    text="🔁 Начать повторение",
    command=start_due_training,
    height=40,
    corner_radius=10
).pack(anchor="w", padx=18, pady=(4, 8))

ctk.CTkButton(
    right_card,
    text="📊 Обновить профиль",
    command=start_profile_analysis,
    height=40,
    corner_radius=10
).pack(anchor="w", padx=18, pady=(0, 18))

# Workspace content starts here

left_panel = ctk.CTkFrame(content, fg_color="#181B21", corner_radius=18)
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

ctk.CTkLabel(
    left_panel, text="♟ GAMECOACH 30 • ANALYSIS",
    font=ctk.CTkFont(family="Segoe UI", size=23, weight="bold")
).pack(pady=(16, 4))

opening_label = ctk.CTkLabel(left_panel, text="Дебют: —", text_color="#AEB5BF")
opening_label.pack(pady=(0, 8))

board_row = ctk.CTkFrame(left_panel, fg_color="transparent")
board_row.pack()

eval_canvas = tk.Canvas(
    board_row, width=EVAL_BAR_W, height=BOARD_SIZE,
    bg="#181B21", highlightthickness=0
)
eval_canvas.pack(side="left", padx=(0, 7))

board_canvas = tk.Canvas(
    board_row, width=BOARD_SIZE, height=BOARD_SIZE,
    bg="#181B21", highlightthickness=0
)
board_canvas.pack(side="left")

board_canvas.bind("<ButtonPress-1>", on_board_press)
board_canvas.bind("<B1-Motion>", on_board_motion)
board_canvas.bind("<ButtonRelease-1>", on_board_release)

controls = ctk.CTkFrame(left_panel, fg_color="transparent")
controls.pack(pady=(10, 4))

ctk.CTkButton(controls, text="⏮", width=55, command=go_start).pack(side="left", padx=4)
ctk.CTkButton(controls, text="◀", width=55, command=go_prev).pack(side="left", padx=4)

autoplay_button = ctk.CTkButton(controls, text="▶ Авто", width=100, command=toggle_autoplay)
autoplay_button.pack(side="left", padx=4)

ctk.CTkButton(controls, text="▶", width=55, command=go_next).pack(side="left", padx=4)
ctk.CTkButton(controls, text="⏭", width=55, command=go_end).pack(side="left", padx=4)

move_counter_label = ctk.CTkLabel(controls, text="Старт", width=90)
move_counter_label.pack(side="left", padx=10)

training_row = ctk.CTkFrame(left_panel, fg_color="transparent")
training_row.pack(pady=4)

ctk.CTkButton(training_row, text="🎓 Тренировать ошибки", command=start_training, width=170).pack(side="left", padx=4)
ctk.CTkButton(training_row, text="Следующая ▶", command=next_training_position, width=120).pack(side="left", padx=4)
ctk.CTkButton(training_row, text="💡 Ответ", command=reveal_training_answer, width=100).pack(side="left", padx=4)

training_status = ctk.CTkLabel(left_panel, text="", wraplength=520, text_color="#AEB5BF")
training_status.pack(pady=(3, 10))

smart_training_row = ctk.CTkFrame(left_panel, fg_color="transparent")
smart_training_row.pack(fill="x", pady=(4, 8))
ctk.CTkButton(smart_training_row, text="🔁 Повторить ошибки", command=start_due_training, height=34).pack(side="left", padx=(0, 5))
ctk.CTkButton(smart_training_row, text="✕ Выйти", command=exit_training, width=80, height=34).pack(side="left")

right_panel = ctk.CTkFrame(content, width=520, fg_color="#181B21", corner_radius=18)
right_panel.pack(side="left", fill="both", expand=True, padx=(10, 0))

analysis_title = ctk.CTkLabel(
    right_panel, text="Начальная позиция",
    font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
)
analysis_title.pack(anchor="w", padx=22, pady=(20, 6))

eval_label = ctk.CTkLabel(right_panel, text="Оценка: —")
eval_label.pack(anchor="w", padx=22, pady=3)

best_label = ctk.CTkLabel(right_panel, text="Лучший ход: —", text_color="#61D98B")
best_label.pack(anchor="w", padx=22, pady=3)

variation_label = ctk.CTkLabel(right_panel, text="Линия Stockfish:\n—", justify="left", wraplength=455)
variation_label.pack(anchor="w", padx=22, pady=(6, 10))

ctk.CTkLabel(
    right_panel, text="Ходы партии",
    font=ctk.CTkFont(size=16, weight="bold")
).pack(anchor="w", padx=22)

moves_box = ctk.CTkTextbox(
    right_panel, height=180, wrap="word",
    font=ctk.CTkFont(family="Segoe UI", size=14),
    corner_radius=10, fg_color="#12161C"
)
moves_box.pack(fill="x", padx=22, pady=(6, 12))
moves_box.configure(state="disabled")
moves_box.bind("<Button-1>", on_move_list_click)

ctk.CTkLabel(
    right_panel, text="Разбор хода",
    font=ctk.CTkFont(size=16, weight="bold")
).pack(anchor="w", padx=22)

analysis_text = ctk.CTkTextbox(
    right_panel,
    wrap="word",
    font=ctk.CTkFont(family="Segoe UI", size=15),
    corner_radius=14,
    border_width=1,
    border_color="#2A3038",
    fg_color="#12161C"
)
analysis_text.pack(fill="both", expand=True, padx=22, pady=(8, 12))
analysis_text.insert("1.0", "Выбери партию и запусти анализ.\n\nGameCoach разберёт ход за ходом и покажет главное без лишнего текста.\n\nПосле анализа попробуй «🧠 Сам», затем открой «❓ Почему» и «🗺 Карта».")
analysis_text.configure(state="disabled")

bottom_actions = ctk.CTkFrame(right_panel, fg_color="transparent")
bottom_actions.pack(fill="x", padx=22, pady=(0, 8))

ctk.CTkButton(bottom_actions, text="❓ Почему", command=enhanced_why_current_move, height=38, width=92).pack(side="left", padx=(0,4))
ctk.CTkButton(bottom_actions, text="🧠 Сам", command=think_first_current_position, height=38, width=88).pack(side="left", padx=4)
ctk.CTkButton(bottom_actions, text="👁 Пропустил?", command=open_what_did_i_miss, height=38, width=100).pack(side="left", padx=4)
ctk.CTkButton(bottom_actions, text="👁 Лучший", command=show_best_move_visual, height=38, width=92).pack(side="left", padx=4)
ctk.CTkButton(bottom_actions, text="🎓 Задача", command=solve_current_position, height=38, width=92).pack(side="left", padx=4)
ctk.CTkButton(bottom_actions, text="🔁 Повторить", command=add_current_error_to_repetition, height=38, width=98).pack(side="left", padx=4)
ctk.CTkButton(bottom_actions, text="💡 Подсказка", command=open_progressive_hint, height=38, width=100).pack(side="left", padx=4)

analysis_tools = ctk.CTkFrame(right_panel, fg_color="transparent")
analysis_tools.pack(fill="x", padx=22, pady=(0, 8))
ctk.CTkButton(analysis_tools, text="🎯 Ключевые моменты", command=open_key_moments, height=38).pack(side="left", fill="x", expand=True, padx=(0,4))
ctk.CTkButton(analysis_tools, text="📈 График", command=open_eval_graph, height=38).pack(side="left", fill="x", expand=True, padx=4)
ctk.CTkButton(analysis_tools, text="🧩 Рассчитать", command=start_calculation_challenge, height=38).pack(side="left", fill="x", expand=True, padx=(4,0))

quality_tools = ctk.CTkFrame(right_panel, fg_color="transparent")
quality_tools.pack(fill="x", padx=22, pady=(0, 8))
ctk.CTkButton(quality_tools, text="💬 Тренер", command=open_ask_coach, height=38).pack(side="left", fill="x", expand=True, padx=(0,4))
ctk.CTkButton(quality_tools, text="📅 Урок сегодня", command=open_daily_session, height=38).pack(side="left", fill="x", expand=True, padx=4)
ctk.CTkButton(quality_tools, text="🧰 Ещё инструменты", command=open_analysis_toolbox, height=38).pack(side="left", fill="x", expand=True, padx=(4,0))

progress_bar = ctk.CTkProgressBar(right_panel)
progress_bar.pack(fill="x", padx=22, pady=(2, 8))
progress_bar.set(0)

status_label = ctk.CTkLabel(right_panel, text="Готов к анализу", text_color="#999FA8")
status_label.pack(pady=(0, 14))


# ---------- GameCoach 30 integrated home ----------
home_overlay=ctk.CTkFrame(content,fg_color="#131713",corner_radius=18)

home_header=ctk.CTkFrame(home_overlay,fg_color="transparent")
home_header.pack(fill="x",padx=26,pady=(24,12))
ctk.CTkLabel(
    home_header,text="Твой шахматный центр",
    font=ctk.CTkFont(family="Segoe UI",size=30,weight="bold")
).pack(anchor="w")
ctk.CTkLabel(
    home_header,
    text="Играй • разбирай • тренируй свои ошибки • следи за прогрессом",
    text_color="#929C98",font=ctk.CTkFont(size=14)
).pack(anchor="w",pady=(4,0))

home_metrics=ctk.CTkFrame(home_overlay,fg_color="transparent")
home_metrics.pack(fill="x",padx=20,pady=(0,12))
for _i in range(4):
    home_metrics.grid_columnconfigure(_i,weight=1)

def _home_metric(col,title):
    card=ctk.CTkFrame(home_metrics,corner_radius=14,fg_color="#1B211D")
    card.grid(row=0,column=col,sticky="nsew",padx=5)
    ctk.CTkLabel(card,text=title,text_color="#7F8B85",
                 font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=14,pady=(12,3))
    val=ctk.CTkLabel(card,text="0",font=ctk.CTkFont(size=25,weight="bold"))
    val.pack(anchor="w",padx=14,pady=(0,13))
    return val

home_games_value=_home_metric(0,"ПАРТИЙ В ПРОФИЛЕ")
home_errors_value=_home_metric(1,"ОШИБОК / ПАРТИЮ")
home_due_value=_home_metric(2,"НА ПОВТОРЕНИЕ")
home_level_value=_home_metric(3,"LEVEL")

home_body=ctk.CTkFrame(home_overlay,fg_color="transparent")
home_body.pack(fill="both",expand=True,padx=20,pady=(0,12))
home_body.grid_columnconfigure(0,weight=3)
home_body.grid_columnconfigure(1,weight=2)
home_body.grid_rowconfigure(0,weight=1)

home_left=ctk.CTkFrame(home_body,corner_radius=16,fg_color="#1A201C")
home_left.grid(row=0,column=0,sticky="nsew",padx=(5,7),pady=5)
home_right=ctk.CTkFrame(home_body,corner_radius=16,fg_color="#1A201C")
home_right.grid(row=0,column=1,sticky="nsew",padx=(7,5),pady=5)

ctk.CTkLabel(
    home_left,text="🧠 Сегодняшний фокус",
    font=ctk.CTkFont(size=18,weight="bold")
).pack(anchor="w",padx=18,pady=(18,4))
home_focus_title=ctk.CTkLabel(
    home_left,text="—",
    font=ctk.CTkFont(size=24,weight="bold"),text_color="#73D6A4"
)
home_focus_title.pack(anchor="w",padx=18,pady=(2,6))
home_focus_text=ctk.CTkLabel(
    home_left,text="Собираю твой профиль…",wraplength=650,justify="left",
    text_color="#B6C0BB",font=ctk.CTkFont(size=14)
)
home_focus_text.pack(anchor="w",padx=18,pady=(0,16))

home_action_grid=ctk.CTkFrame(home_left,fg_color="transparent")
home_action_grid.pack(fill="x",padx=14,pady=(2,16))
home_action_grid.grid_columnconfigure((0,1),weight=1)

_home_actions=[
    ("▶ Начать тренировку",open_adaptive_coach,GC_ACCENT),
    ("🔍 Разобрать партию",show_analysis_page,"#414A44"),
    ("🎯 Replay Trainer",open_replay_hub,"#6B5B3E"),
    ("🧩 Puzzle Lab",open_puzzle_lab,"#414A44"),
]
for _i,(_t,_cmd,_c) in enumerate(_home_actions):
    ctk.CTkButton(
        home_action_grid,text=_t,command=_cmd,fg_color=_c,
        height=42,corner_radius=11
    ).grid(row=_i//2,column=_i%2,sticky="ew",padx=4,pady=4)

ctk.CTkLabel(
    home_left,text="Быстрые режимы",
    font=ctk.CTkFont(size=16,weight="bold")
).pack(anchor="w",padx=18,pady=(6,6))
quick=ctk.CTkFrame(home_left,fg_color="transparent")
quick.pack(fill="x",padx=14,pady=(0,18))
for _t,_cmd in [
    ("⚔ Играть",open_play_vs_stockfish),
    ("📚 Дебюты",open_opening_repertoire),
    ("🏁 Эндшпили",open_endgame_coach),
    ("🧰 Инструменты",open_analysis_toolbox),
]:
    ctk.CTkButton(quick,text=_t,command=_cmd,height=36,
                  fg_color="#2A332D",hover_color="#37483D").pack(side="left",fill="x",expand=True,padx=3)

ctk.CTkLabel(
    home_right,text="📈 Форма",
    font=ctk.CTkFont(size=18,weight="bold")
).pack(anchor="w",padx=18,pady=(18,4))
home_trend_title=ctk.CTkLabel(
    home_right,text="—",wraplength=390,justify="left",
    font=ctk.CTkFont(size=16,weight="bold"),text_color="#D9B56C"
)
home_trend_title.pack(anchor="w",padx=18,pady=(4,6))
home_trend_text=ctk.CTkLabel(
    home_right,text="",wraplength=390,justify="left",text_color="#AEB8B3"
)
home_trend_text.pack(anchor="w",padx=18,pady=(0,18))

ctk.CTkLabel(
    home_right,text="🏆 Прогресс",
    font=ctk.CTkFont(size=18,weight="bold")
).pack(anchor="w",padx=18,pady=(6,5))
home_xp_label=ctk.CTkLabel(
    home_right,text="Level 1 • 0 XP",
    font=ctk.CTkFont(size=16,weight="bold")
)
home_xp_label.pack(anchor="w",padx=18,pady=(2,6))
home_xp_bar=ctk.CTkProgressBar(home_right,height=10,progress_color=GC_ACCENT)
home_xp_bar.pack(fill="x",padx=18,pady=(0,14))
home_xp_bar.set(0)

ctk.CTkButton(
    home_right,text="📈 Progress Intelligence",command=open_quality_progress,
    fg_color="#414A44",height=40
).pack(fill="x",padx=18,pady=4)
ctk.CTkButton(
    home_right,text="📅 Weekly Coach Report",command=open_weekly_coach_report,
    fg_color="#414A44",height=40
).pack(fill="x",padx=18,pady=4)
ctk.CTkButton(
    home_right,text="🧬 Player Intelligence",command=open_player_intelligence,
    fg_color="#414A44",height=40
).pack(fill="x",padx=18,pady=4)

home_footer=ctk.CTkFrame(home_overlay,fg_color="transparent")
home_footer.pack(fill="x",padx=26,pady=(0,18))
ctk.CTkLabel(
    home_footer,
    text="GameCoach 1.0 • партии → ошибки → упражнения → прогресс",
    text_color="#748079",font=ctk.CTkFont(size=12)
).pack(side="left")
ctk.CTkButton(
    home_footer,text="⚙ Настройки",command=show_settings_window,
    width=110,height=34,fg_color="#303832"
).pack(side="right",padx=(6,0))
ctk.CTkButton(
    home_footer,text="🎨 Оформление",command=show_appearance_window,
    width=120,height=34,fg_color="#303832"
).pack(side="right")

# Startup
status_label.configure(text="♟ Проверяю фигуры...")
root.update_idletasks()

if download_piece_images():
    load_piece_images()
    status_label.configure(text="✅ Фигуры готовы")
else:
    load_piece_images()
    status_label.configure(text="⚠ PNG недоступны — включены встроенные фигуры")

draw_board(chess.Board())
draw_eval_bar(0)

load_app_settings()
download_piece_images()
load_piece_images()
init_database()
load_training_stats()
load_saved_training_positions()
for _p in list(saved_training_positions):
    try:
        db_save_puzzle(_p)
    except Exception:
        pass
load_learning_profile()
ensure_stockfish_path(show_message=False)
ensure_sound_files()
show_home_page()

def show_first_run_welcome():
    """Show a lightweight welcome screen once per Windows user."""
    marker = os.path.join(APP_DATA_DIR, "welcome_1_0_seen.txt")
    if os.path.exists(marker):
        return

    win = ctk.CTkToplevel(root)
    win.title("Добро пожаловать в GameCoach")
    win.geometry("760x650")
    win.resizable(False, False)
    win.transient(root)
    try:
        win.grab_set()
    except Exception:
        pass

    outer = ctk.CTkFrame(win, corner_radius=22)
    outer.pack(fill="both", expand=True, padx=18, pady=18)

    ctk.CTkLabel(
        outer,
        text="♔  GameCoach",
        font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold")
    ).pack(pady=(34, 4))

    ctk.CTkLabel(
        outer,
        text="Твой персональный шахматный тренер",
        font=ctk.CTkFont(family="Segoe UI", size=18),
        text_color="#AAB4C3"
    ).pack(pady=(0, 24))

    intro = (
        "GameCoach помогает не просто увидеть ошибку, а понять её.\n"
        "Анализируй партии, разбирай ключевые моменты и превращай\n"
        "свои ошибки в персональные упражнения."
    )
    ctk.CTkLabel(
        outer, text=intro, justify="center",
        font=ctk.CTkFont(size=15), wraplength=650
    ).pack(pady=(0, 22))

    features = ctk.CTkFrame(outer, corner_radius=16)
    features.pack(fill="x", padx=48, pady=8)

    for icon, title, desc in [
        ("🔍", "Анализ", "Stockfish + объяснения GameCoach"),
        ("🧠", "Тренировка", "Упражнения из твоих собственных ошибок"),
        ("📈", "Прогресс", "Слабые места, повторения и развитие"),
    ]:
        row = ctk.CTkFrame(features, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=10)
        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=25), width=42).pack(side="left")
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(
            text_frame, text=title,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_frame, text=desc, text_color="#9CA8B7",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")

    ctk.CTkLabel(
        outer,
        text="Stockfish должен быть установлен вместе с GameCoach или выбран в настройках.",
        text_color="#8F9BAA", wraplength=620
    ).pack(pady=(18, 8))

    def finish_welcome():
        try:
            Path(marker).write_text("GameCoach 1.0 welcome completed\n", encoding="utf-8")
        except Exception:
            pass
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    ctk.CTkButton(
        outer,
        text="Начать работу  →",
        command=finish_welcome,
        height=48,
        width=260,
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(pady=(10, 8))

    ctk.CTkLabel(
        outer,
        text="ANALYZE  •  LEARN  •  IMPROVE",
        text_color="#758195",
        font=ctk.CTkFont(size=11)
    ).pack(pady=(4, 18))

    win.protocol("WM_DELETE_WINDOW", finish_welcome)


root.after(350, show_first_run_welcome)
root.mainloop()
