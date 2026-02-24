"""
=======================================================
  FIL-ORGANISATOR  |  USB-udgave  v3.0
=======================================================
  Start via:  START_ORGANISATOR.bat
  Eller:      py organisator.py
=======================================================
"""

import os
import sys
import shutil
import ctypes
import hashlib
import datetime
import threading
import json
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from sprog import T, TEKSTER, SPROG_LISTE, SprogVælger, init_sprog, set_sprog

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

try:
    import exifread
    EXIFREAD_OK = True
except ImportError:
    EXIFREAD_OK = False

try:
    import reverse_geocoder as rg
    GEOCODER_OK = True
except ImportError:
    GEOCODER_OK = False

try:
    from send2trash import send2trash as _send2trash
    TRASH_OK = True
except ImportError:
    TRASH_OK = False

# Lande-koder til læsbare navne
LANDE = {
    "DK": "Danmark",       "SE": "Sverige",       "NO": "Norge",
    "DE": "Tyskland",      "FR": "Frankrig",      "ES": "Spanien",
    "IT": "Italien",       "GB": "Storbritannien","US": "USA",
    "PT": "Portugal",      "GR": "Graekenland",   "NL": "Holland",
    "BE": "Belgien",       "CH": "Schweiz",       "AT": "Oestrig",
    "PL": "Polen",         "CZ": "Tjekkiet",      "HR": "Kroatien",
    "TR": "Tyrkiet",       "TH": "Thailand",      "JP": "Japan",
    "CN": "Kina",          "AU": "Australien",    "CA": "Canada",
    "MX": "Mexico",        "BR": "Brasilien",     "ZA": "Sydafrika",
    "EG": "Egypten",       "MA": "Marokko",       "AE": "Dubai (UAE)",
    "ID": "Indonesien",    "MY": "Malaysia",      "SG": "Singapore",
    "IN": "Indien",        "NZ": "New Zealand",   "IE": "Irland",
    "FI": "Finland",       "IS": "Island",        "HU": "Ungarn",
    "RO": "Rumænien",      "BG": "Bulgarien",     "RS": "Serbien",
    "HR": "Kroatien",      "SK": "Slovakiet",     "SI": "Slovenien",
}

# RAW-formater som Pillow ikke kan læse – bruger exifread til disse
RAW_TYPER = {".cr2", ".nef", ".arw", ".dng", ".raw", ".orf", ".rw2",
             ".pef", ".srw", ".x3f", ".raf"}

# ───────────────────────────────────────────────────
#  KONSTANTER
# ───────────────────────────────────────────────────
VERSION = "4.0"

MÅNEDER = {
    1: "01_Januar",    2: "02_Februar",   3: "03_Marts",
    4: "04_April",     5: "05_Maj",       6: "06_Juni",
    7: "07_Juli",      8: "08_August",    9: "09_September",
    10: "10_Oktober",  11: "11_November", 12: "12_December"
}

BILLEDE_TYPER  = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".heif",
                  ".raw", ".cr2", ".nef", ".arw", ".dng"}
VIDEO_TYPER    = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v",
                  ".mpg", ".mpeg", ".3gp", ".webm", ".ts", ".mts", ".m2ts",
                  ".vob", ".divx", ".xvid", ".rmvb"}
DOKUMENT_TYPER = {".docx", ".doc", ".docm", ".pdf",
                  ".xlsx", ".xls", ".xlsm", ".csv", ".pages"}

DOKUMENT_UNDERMAPPE = {
    ".docx": "Word", ".doc": "Word", ".docm": "Word",
    ".pdf":  "PDF",
    ".xlsx": "Excel", ".xls": "Excel", ".xlsm": "Excel", ".csv": "Excel",
    ".pages": "Pages",
}

SKIP_MAPPER = {
    "windows", "program files", "program files (x86)", "programdata",
    "appdata", "system volume information", "$recycle.bin", "recovery",
    "steamapps", "steam", "epic games", "battle.net", "riotgames",
    "origin games", "ea games", "ubisoft", "gog galaxy", "xbox", "common",
    "node_modules", "site-packages", ".git", "cache", "temp", "tmp",
}

KAMERA_EXIF = {"DateTimeOriginal", "DateTimeDigitized", "Make", "Model"}
MIN_VIDEO_MB = 5

# ── Farver ──────────────────────────────────────────
BG     = "#1e1e2e"
PANEL  = "#2a2a3e"
ACCENT = "#7c6af7"
TEKST  = "#cdd6f4"
DIM    = "#6c7086"
GRØN   = "#a6e3a1"
RØD    = "#f38ba8"
GUL    = "#f9e2af"


# ───────────────────────────────────────────────────
#  HJÆLPEFUNKTIONER
# ───────────────────────────────────────────────────
def find_drev():
    return [f"{b}:\\" for b in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if os.path.exists(f"{b}:\\")]


def skal_skippes(sti, dest):
    if dest and sti.lower().startswith(dest.lower()):
        return True
    return any(d in SKIP_MAPPER
               for d in sti.lower().replace("\\", "/").split("/"))


def unikt_filnavn(dest_mappe, filnavn):
    dest = os.path.join(dest_mappe, filnavn)
    if not os.path.exists(dest):
        return dest
    navn, ext = Path(filnavn).stem, Path(filnavn).suffix
    i = 1
    while os.path.exists(dest):
        dest = os.path.join(dest_mappe, f"{navn}_{i}{ext}")
        i += 1
    return dest


# Filtyper der aldrig har EXIF - brug filens dato direkte (meget hurtigere)
INGEN_EXIF_TYPER = {".png", ".gif", ".bmp", ".webp", ".svg", ".pages",
                    ".docx", ".doc", ".pdf", ".xlsx", ".xls", ".csv"}

def hent_exif(filepath):
    """
    Læser EXIF fra billedfiler hurtigt og effektivt.
    - PNG/GIF/BMP osv.: returnerer None med det samme (ingen EXIF)
    - RAW-filer:        bruger exifread
    - JPG/TIFF osv.:    bruger Pillow, kun de nødvendige dato-tags
    """
    ext = Path(filepath).suffix.lower()

    # ── Filtyper uden EXIF – spring over med det samme ──
    if ext in INGEN_EXIF_TYPER:
        return None

    # ── RAW-filer via exifread ───────────────────────────
    if ext in RAW_TYPER:
        if not EXIFREAD_OK:
            return {"Make": "RAW"}
        try:
            with open(filepath, "rb") as f:
                # stop_tag gør at den stopper så snart den finder datoen
                tags = exifread.process_file(f, stop_tag="DateTimeOriginal",
                                             details=False)
            if not tags:
                return {"Make": "RAW"}
            return {key.split(" ")[-1]: str(val) for key, val in tags.items()}
        except Exception:
            return {"Make": "RAW"}

    # ── JPG / TIFF / HEIC via Pillow ────────────────────
    if not PILLOW_OK:
        return None
    try:
        with Image.open(filepath) as img:
            # Læs kun de første få KB (header) for at finde dato-tags
            img.draft(None, (1, 1))
            raw = img._getexif()
            if not raw:
                return None
            # Returner kun dato-relaterede tags – meget hurtigere end hele EXIF
            dato_tag_ids = {36867, 36868, 306}  # DateTimeOriginal, DateTimeDigitized, DateTime
            return {TAGS.get(tid, tid): v
                    for tid, v in raw.items()
                    if tid in dato_tag_ids}
    except Exception:
        return None


def fil_dato(filepath):
    try:
        t = min(os.path.getctime(filepath), os.path.getmtime(filepath))
        return datetime.datetime.fromtimestamp(t)
    except Exception:
        return None


def hent_gps(filepath):
    """
    Læser GPS-koordinater fra billedets EXIF.
    Returnerer (breddegrad, laengdegrad) eller None.
    """
    ext = Path(filepath).suffix.lower()
    try:
        # RAW-filer
        if ext in RAW_TYPER and EXIFREAD_OK:
            with open(filepath, "rb") as f:
                tags = exifread.process_file(f, details=False)
            lat = tags.get("GPS GPSLatitude")
            lat_ref = tags.get("GPS GPSLatitudeRef")
            lon = tags.get("GPS GPSLongitude")
            lon_ref = tags.get("GPS GPSLongitudeRef")
            if not (lat and lon):
                return None
            def dms_til_decimal(dms, ref):
                d, m, s = [float(x.num) / float(x.den)
                           for x in dms.values]
                decimal = d + m / 60 + s / 3600
                if str(ref) in ("S", "W"):
                    decimal = -decimal
                return decimal
            return (dms_til_decimal(lat, lat_ref),
                    dms_til_decimal(lon, lon_ref))

        # JPG/TIFF via Pillow
        if PILLOW_OK:
            with Image.open(filepath) as img:
                raw = img._getexif()
                if not raw:
                    return None
                # Tag 34853 = GPSInfo
                gps_info = raw.get(34853)
                if not gps_info:
                    return None
                def konverter(koordinat, ref):
                    d, m, s = [float(x) for x in koordinat]
                    decimal = d + m / 60 + s / 3600
                    if ref in ("S", "W"):
                        decimal = -decimal
                    return decimal
                lat = konverter(gps_info.get(2, [0,0,0]),
                                gps_info.get(1, "N"))
                lon = konverter(gps_info.get(4, [0,0,0]),
                                gps_info.get(3, "E"))
                if lat == 0 and lon == 0:
                    return None
                return (lat, lon)
    except Exception:
        return None


def koordinater_til_sted(lat, lon):
    """
    Omregner GPS-koordinater til (land, by) via reverse_geocoder.
    Returnerer ("Ukendt_land", "Ukendt_by") hvis det fejler.
    """
    if not GEOCODER_OK:
        return ("Ukendt_land", "Ukendt_by")
    try:
        resultat = rg.search((lat, lon), verbose=False)
        if not resultat:
            return ("Ukendt_land", "Ukendt_by")
        r    = resultat[0]
        kode = r.get("cc", "??")
        land = LANDE.get(kode, r.get("cc", "Ukendt_land"))
        by   = r.get("name", "Ukendt_by")
        # Rens ugyldige tegn fra mappenavne
        by   = "".join(c for c in by if c not in r'\/:*?"<>|')
        land = "".join(c for c in land if c not in r'\/:*?"<>|')
        return (land, by)
    except Exception:
        return ("Ukendt_land", "Ukendt_by")


def find_filer(rødder, typer, dest, log=None, min_mb=None):
    """Scanner en liste af mapper og returnerer matchende filer."""
    filer = []
    mapper_sprunget = []
    for rod in rødder:
        for dirpath, dirnavne, filnavne in os.walk(rod):
            if skal_skippes(dirpath, dest):
                mapper_sprunget.append(dirpath)
                dirnavne.clear()
                continue
            dirnavne[:] = [d for d in dirnavne
                           if not skal_skippes(os.path.join(dirpath, d), dest)]
            for fn in filnavne:
                if Path(fn).suffix.lower() in typer:
                    fuld = os.path.join(dirpath, fn)
                    if min_mb:
                        try:
                            if os.path.getsize(fuld) / 1_048_576 < min_mb:
                                continue
                        except Exception:
                            continue
                    filer.append(fuld)
    if log and mapper_sprunget:
        log(T["log_skipped"].format(len(mapper_sprunget)))
    return filer


# ───────────────────────────────────────────────────
#  ORGANISATIONS-LOGIK
# ───────────────────────────────────────────────────
def kør_billeder(rødder, dest, log, progress, stop_flag):
    if not PILLOW_OK and not EXIFREAD_OK:
        log(T["log_no_pillow"], farve=RØD)
        return
    log(T["log_scan_photos"])
    filer = find_filer(rødder, BILLEDE_TYPER, dest, log=log)
    log(T["log_found_photos"].format(len(filer)) + "\n")

    flyttet = ingen_exif_dato = fejl = 0
    for i, fil in enumerate(filer, 1):
        if stop_flag():
            log(T["log_stopped"], farve=GUL); break
        progress(i, len(filer), os.path.basename(fil))

        # Forsøg EXIF-dato
        dato = None
        try:
            exif = hent_exif(fil)
            if exif:
                dato = next(
                    (datetime.datetime.strptime(exif[f], "%Y:%m:%d %H:%M:%S")
                     for f in ("DateTimeOriginal", "DateTimeDigitized", "DateTime")
                     if f in exif),
                    None
                )
        except Exception:
            pass

        # Fallback: filens oprettelsesdato
        if not dato:
            dato = fil_dato(fil)
            ingen_exif_dato += 1

        år  = str(dato.year)      if dato else "Ukendt_dato"
        mnd = MÅNEDER[dato.month] if dato else "Ukendt_maaned"
        mappe = os.path.join(dest, år, mnd)
        os.makedirs(mappe, exist_ok=True)
        try:
            shutil.move(fil, unikt_filnavn(mappe, os.path.basename(fil)))
            flyttet += 1
            # Vis en statuslinje for hvert 10. billede
            if flyttet % 10 == 0:
                log(T["log_moved_n"].format(flyttet))
        except Exception as e:
            log(T["log_err"].format(os.path.basename(fil), e), farve=RØD)
            fejl += 1

    log(f"\n══════════════════════════════", farve=GRØN)
    log(T["log_done"], farve=GRØN)
    log(T["log_photos_moved"].format(flyttet), farve=GRØN)
    log(T["log_filedate"].format(ingen_exif_dato), farve=GUL)
    log(T["log_errors"].format(fejl), farve=RØD if fejl else GRØN)
    log(f"══════════════════════════════", farve=GRØN)


def kør_billeder_gps(rødder, dest, log, progress, stop_flag):
    """Sorterer billeder efter GPS-lokation: Dest/Land/By/fil"""
    if not GEOCODER_OK:
        log(T["log_no_geocoder"], farve=RØD)
        log(T["log_install_geo"], farve=GUL)
        return

    log(T["log_scan_gps"])
    filer = find_filer(rødder, BILLEDE_TYPER, dest, log=log)
    log(T["log_found_photos"].format(len(filer)) + "\n")

    flyttet = ingen_gps = fejl = 0
    for i, fil in enumerate(filer, 1):
        if stop_flag():
            log(T["log_stopped"], farve=GUL); break
        progress(i, len(filer), os.path.basename(fil))

        gps = hent_gps(fil)
        if gps:
            land, by = koordinater_til_sted(gps[0], gps[1])
        else:
            land, by = "Ingen_GPS", "Ingen_GPS"
            ingen_gps += 1

        mappe = os.path.join(dest, land, by)
        os.makedirs(mappe, exist_ok=True)
        try:
            shutil.move(fil, unikt_filnavn(mappe, os.path.basename(fil)))
            flyttet += 1
            if flyttet % 10 == 0:
                log(T["log_moved_n"].format(flyttet))
        except Exception as e:
            log(T["log_err"].format(os.path.basename(fil), e), farve=RØD)
            fejl += 1

    log(f"\n══════════════════════════════", farve=GRØN)
    log(T["log_done"], farve=GRØN)
    log(T["log_gps_moved"].format(flyttet), farve=GRØN)
    log(T["log_no_gps"].format(ingen_gps), farve=GUL)
    log(T["log_errors"].format(fejl), farve=RØD if fejl else GRØN)
    log(f"══════════════════════════════", farve=GRØN)


def kør_videoer(rødder, dest, log, progress, stop_flag):
    log(T["log_scan_videos"])
    filer = find_filer(rødder, VIDEO_TYPER, dest, log=log, min_mb=MIN_VIDEO_MB)
    log(T["log_found_videos"].format(len(filer)) + "\n")
    flyttet = fejl = 0
    for i, fil in enumerate(filer, 1):
        if stop_flag():
            log(T["log_stopped"], farve=GUL); break
        progress(i, len(filer), os.path.basename(fil))
        dato = fil_dato(fil)
        år  = str(dato.year)      if dato else "Ukendt_dato"
        mnd = MÅNEDER[dato.month] if dato else "Ukendt_maaned"
        mappe = os.path.join(dest, år, mnd)
        os.makedirs(mappe, exist_ok=True)
        try:
            shutil.move(fil, unikt_filnavn(mappe, os.path.basename(fil)))
            flyttet += 1
        except Exception as e:
            log(T["log_err"].format(os.path.basename(fil), e), farve=RØD); fejl += 1
    log(f"\n══════════════════════════════", farve=GRØN)
    log(T["log_video_done"].format(flyttet, fejl), farve=GRØN)
    log(f"══════════════════════════════", farve=GRØN)


def kør_dokumenter(rødder, dest, log, progress, stop_flag):
    log(T["log_scan_docs"])
    filer = find_filer(rødder, DOKUMENT_TYPER, dest, log=log)
    log(T["log_found_docs"].format(len(filer)) + "\n")
    tæller = {"Word": 0, "PDF": 0, "Excel": 0}
    fejl = 0
    for i, fil in enumerate(filer, 1):
        if stop_flag():
            log(T["log_stopped"], farve=GUL); break
        progress(i, len(filer), os.path.basename(fil))
        ext   = Path(fil).suffix.lower()
        under = DOKUMENT_UNDERMAPPE.get(ext, "Andet")
        mappe = os.path.join(dest, under)
        os.makedirs(mappe, exist_ok=True)
        try:
            shutil.move(fil, unikt_filnavn(mappe, os.path.basename(fil)))
            tæller[under] = tæller.get(under, 0) + 1
        except Exception as e:
            log(T["log_err"].format(os.path.basename(fil), e), farve=RØD); fejl += 1
    log(f"\n══════════════════════════════", farve=GRØN)
    log(T["log_done"], farve=GRØN)
    log(T["log_doc_done"].format(tæller['Word'], tæller['PDF'], tæller['Excel']), farve=GRØN)
    log(T["log_doc_errors"].format(fejl), farve=RØD if fejl else GRØN)
    log(f"══════════════════════════════", farve=GRØN)


# ───────────────────────────────────────────────────
#  DUBLET-SCANNER
# ───────────────────────────────────────────────────
def _format_bytes(b):
    """Formaterer bytes til læsbart format."""
    if b < 1024:          return f"{b} B"
    elif b < 1024**2:     return f"{b/1024:.1f} KB"
    elif b < 1024**3:     return f"{b/1024**2:.1f} MB"
    else:                 return f"{b/1024**3:.2f} GB"


def hash_fil(filepath):
    """MD5-hash af en fil i 64 KB chunks. Returnerer None ved fejl."""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def slet_til_papirkurv(filepath):
    """Sender fil til papirkurven. Returnerer True ved succes."""
    if TRASH_OK:
        try:
            _send2trash(filepath)
            return True
        except Exception:
            pass
    # Fallback: Windows SHFileOperationW (built-in)
    try:
        class _SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ("hwnd",                  ctypes.c_void_p),
                ("wFunc",                 ctypes.c_uint),
                ("pFrom",                 ctypes.c_wchar_p),
                ("pTo",                   ctypes.c_wchar_p),
                ("fFlags",                ctypes.c_ushort),
                ("fAnyOperationsAborted", ctypes.c_bool),
                ("hNameMappings",         ctypes.c_void_p),
                ("lpszProgressTitle",     ctypes.c_wchar_p),
            ]
        FO_DELETE          = 3
        FOF_ALLOWUNDO      = 0x0040
        FOF_NOCONFIRMATION = 0x0010
        FOF_SILENT         = 0x0004
        sti = os.path.abspath(filepath) + "\0\0"
        op = _SHFILEOPSTRUCTW()
        op.hwnd   = None
        op.wFunc  = FO_DELETE
        op.pFrom  = sti
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
        return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0
    except Exception:
        return False


def find_dubletter_filer(rødder, log, progress, stop_flag):
    """
    Finder dubletter: grupper filer efter størrelse, hash derefter.
    Returnerer { hash: [fil1, fil2, ...] } for grupper med 2+ filer.
    """
    alle_typer = BILLEDE_TYPER | VIDEO_TYPER | DOKUMENT_TYPER
    log(T["log_scan_files"])
    filer = find_filer(rødder, alle_typer, "", log=log)
    log(T["log_found_files"].format(len(filer)) + "\n")

    # Trin 1: gruppe efter størrelse – spring unikke størrelser over (hurtigt)
    log(T["log_grouping"])
    str_grupper = {}
    for fil in filer:
        try:
            str_grupper.setdefault(os.path.getsize(fil), []).append(fil)
        except Exception:
            pass

    kandidater = [f for lst in str_grupper.values() if len(lst) > 1 for f in lst]
    log(T["log_candidates"].format(len(kandidater)) + "\n")

    if not kandidater:
        log(T["log_no_dupes"], farve=GRØN)
        return {}

    # Trin 2: hash kandidaterne
    log(T["log_checksums"])
    hash_grupper = {}
    for i, fil in enumerate(kandidater, 1):
        if stop_flag():
            log(T["log_stopped"], farve=GUL)
            return {}
        progress(i, len(kandidater), os.path.basename(fil))
        h = hash_fil(fil)
        if h:
            hash_grupper.setdefault(h, []).append(fil)

    dubletter = {h: lst for h, lst in hash_grupper.items() if len(lst) > 1}

    try:
        total_spares = sum(
            os.path.getsize(lst[0]) * (len(lst) - 1)
            for lst in dubletter.values()
            if os.path.exists(lst[0])
        )
    except Exception:
        total_spares = 0

    log(f"\n══════════════════════════════", farve=GRØN)
    log(T["log_scan_complete"], farve=GRØN)
    log(T["log_dupe_groups"].format(len(dubletter)), farve=GRØN)
    log(T["log_can_save"].format(_format_bytes(total_spares)), farve=GRØN)
    log(f"══════════════════════════════", farve=GRØN)
    return dubletter


# ───────────────────────────────────────────────────
#  DUBLET-RESULTAT VINDUE
# ───────────────────────────────────────────────────
class DubletVindue(tk.Toplevel):
    def __init__(self, forælder, grupper):
        super().__init__(forælder)
        self.title(T["dupe_title"])
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(820, 520)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(980, sw - 40), min(680, sh - 60)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._fil_valgt  = {}   # item_id → bool (True = markeret til sletning)
        self._fil_stier  = {}   # item_id → filepath
        self._gruppe_ids = set()

        self._byg_gui(grupper)

    def _byg_gui(self, grupper):
        total_grupper   = len(grupper)
        total_dubletter = sum(len(v) - 1 for v in grupper.values())
        try:
            total_bytes = sum(
                os.path.getsize(lst[0]) * (len(lst) - 1)
                for lst in grupper.values() if os.path.exists(lst[0])
            )
        except Exception:
            total_bytes = 0

        # ── Titel ─────────────────────────────────────
        top = tk.Frame(self, bg=ACCENT, pady=10)
        top.pack(fill="x")
        tk.Label(top,
                 text=T["dupe_header"].format(total_grupper, total_dubletter, _format_bytes(total_bytes)),
                 font=("Segoe UI", 12, "bold"), bg=ACCENT, fg="white").pack()

        # ── Stats (opdateres ved klik) ─────────────────
        self._stats_lbl = tk.Label(self, text="",
                                   font=("Segoe UI", 9), bg=BG, fg=GUL, anchor="w")
        self._stats_lbl.pack(fill="x", padx=16, pady=(6, 2))

        # ── Treeview ──────────────────────────────────
        tree_ydre = tk.Frame(self, bg=PANEL)
        tree_ydre.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        style = ttk.Style()
        style.configure("Dub.Treeview",
                        background="#13131f", fieldbackground="#13131f",
                        foreground=TEKST, font=("Consolas", 9), rowheight=22)
        style.configure("Dub.Treeview.Heading",
                        background=PANEL, foreground=DIM,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Dub.Treeview",
                  background=[("selected", "#313145")],
                  foreground=[("selected", TEKST)])

        self._tree = ttk.Treeview(
            tree_ydre, style="Dub.Treeview",
            columns=("valg", "filnavn", "sti", "størrelse", "dato"),
            show="headings", selectmode="browse"
        )
        self._tree.heading("valg",      text="")
        self._tree.heading("filnavn",   text=T["dupe_col_file"])
        self._tree.heading("sti",       text=T["dupe_col_folder"])
        self._tree.heading("størrelse", text=T["dupe_col_size"])
        self._tree.heading("dato",      text=T["dupe_col_date"])

        self._tree.column("valg",      width=28,  stretch=False, anchor="center")
        self._tree.column("filnavn",   width=190, stretch=True)
        self._tree.column("sti",       width=330, stretch=True)
        self._tree.column("størrelse", width=80,  stretch=False, anchor="e")
        self._tree.column("dato",      width=120, stretch=False)

        v_sb = tk.Scrollbar(tree_ydre, orient="vertical",   command=self._tree.yview)
        h_sb = tk.Scrollbar(tree_ydre, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)
        h_sb.pack(side="bottom", fill="x")
        v_sb.pack(side="right",  fill="y")
        self._tree.pack(fill="both", expand=True)

        self._tree.tag_configure("gruppe", foreground=GUL,  background="#252538")
        self._tree.tag_configure("slet",   foreground=RØD)
        self._tree.tag_configure("behold", foreground=GRØN)
        self._tree.bind("<ButtonRelease-1>", self._on_klik)

        # ── Udfyld treeview ────────────────────────────
        for i, (_, filer) in enumerate(sorted(grupper.items()), 1):
            try:
                spares = os.path.getsize(filer[0]) * (len(filer) - 1)
            except Exception:
                spares = 0
            g_id = self._tree.insert("", "end", tags=("gruppe",),
                values=(T["dupe_group"].format(i, len(filer), _format_bytes(spares)),
                        "", "", "", ""))
            self._gruppe_ids.add(g_id)

            for j, fil in enumerate(filer):
                try:    str_txt = _format_bytes(os.path.getsize(fil))
                except Exception: str_txt = "?"
                dato = fil_dato(fil)
                dato_txt = dato.strftime("%Y-%m-%d %H:%M") if dato else "?"
                er_slet  = (j > 0)
                f_id = self._tree.insert("", "end",
                    tags=("slet" if er_slet else "behold",),
                    values=("☑" if er_slet else "☐",
                            os.path.basename(fil),
                            os.path.dirname(fil),
                            str_txt, dato_txt))
                self._fil_valgt[f_id] = er_slet
                self._fil_stier[f_id] = fil

        self._opdater_stats()

        # ── Progress ──────────────────────────────────
        prog_ramme = tk.Frame(self, bg=PANEL, padx=16, pady=6)
        prog_ramme.pack(fill="x", padx=16, pady=(0, 4))

        self._prog_lbl = tk.Label(prog_ramme, text=T["dupe_ready"],
                                  font=("Segoe UI", 9), bg=PANEL, fg=DIM, anchor="w")
        self._prog_lbl.pack(fill="x")

        style2 = ttk.Style()
        style2.configure("DubProg.Horizontal.TProgressbar",
                         troughcolor=BG, background=ACCENT, thickness=16)
        self._progressbar = ttk.Progressbar(
            prog_ramme, style="DubProg.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate"
        )
        self._progressbar.pack(fill="x", pady=(4, 2))
        self._pct_lbl = tk.Label(prog_ramme, text="0%",
                                 font=("Segoe UI", 9, "bold"), bg=PANEL, fg=ACCENT)
        self._pct_lbl.pack(anchor="e")

        # ── Log ───────────────────────────────────────
        log_ydre = tk.Frame(self, bg=PANEL, pady=2, padx=2)
        log_ydre.pack(fill="x", padx=16, pady=(0, 4))
        self._log_boks = tk.Text(log_ydre, height=4, font=("Consolas", 9),
                                 bg="#13131f", fg=TEKST, bd=0,
                                 state="disabled", wrap="word")
        log_sb = tk.Scrollbar(log_ydre, command=self._log_boks.yview, bg=PANEL)
        self._log_boks.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side="right", fill="y")
        self._log_boks.pack(fill="both", expand=True)
        self._log_boks.tag_configure("grøn", foreground=GRØN)
        self._log_boks.tag_configure("rød",  foreground=RØD)
        self._log_boks.tag_configure("gul",  foreground=GUL)

        # ── Knapper ───────────────────────────────────
        bund = tk.Frame(self, bg=BG, pady=10)
        bund.pack(fill="x", padx=16)

        self._slet_knap = tk.Button(
            bund, text=T["dupe_btn_del"],
            font=("Segoe UI", 11, "bold"),
            bg=RØD, fg="#1e1e2e", relief="flat", padx=20, pady=8,
            cursor="hand2", activebackground="#e07090",
            command=self._slet_valgte
        )
        self._slet_knap.pack(side="left", padx=(0, 8))

        knap_s = dict(font=("Segoe UI", 10), bg="#45475a", fg=TEKST,
                      relief="flat", padx=14, pady=8, cursor="hand2",
                      activebackground="#585b70", activeforeground=TEKST)
        tk.Button(bund, text=T["dupe_btn_sel"],
                  command=self._vælg_alle, **knap_s).pack(side="left", padx=(0, 6))
        tk.Button(bund, text=T["dupe_btn_desel"],
                  command=self._fravælg_alle, **knap_s).pack(side="left", padx=(0, 6))
        tk.Button(bund, text=T["btn_close"], command=self.destroy,
                  font=("Segoe UI", 10), bg=PANEL, fg=TEKST, relief="flat",
                  padx=14, pady=8, cursor="hand2",
                  activebackground="#3a3a5e", activeforeground=TEKST
                  ).pack(side="left")

    def _on_klik(self, event):
        item = self._tree.identify_row(event.y)
        if not item or item in self._gruppe_ids or item not in self._fil_valgt:
            return
        ny = not self._fil_valgt[item]
        self._fil_valgt[item] = ny
        v = list(self._tree.item(item, "values"))
        v[0] = "☑" if ny else "☐"
        self._tree.item(item, values=v, tags=("slet" if ny else "behold",))
        self._opdater_stats()

    def _opdater_stats(self):
        antal  = sum(1 for v in self._fil_valgt.values() if v)
        bytes_ = sum(
            os.path.getsize(self._fil_stier[i])
            for i, v in self._fil_valgt.items()
            if v and os.path.exists(self._fil_stier.get(i, ""))
        )
        self._stats_lbl.config(
            text=T["dupe_stats"].format(antal, _format_bytes(bytes_))
        )

    def _vælg_alle(self):
        for i in self._fil_valgt:
            self._fil_valgt[i] = True
            v = list(self._tree.item(i, "values")); v[0] = "☑"
            self._tree.item(i, values=v, tags=("slet",))
        self._opdater_stats()

    def _fravælg_alle(self):
        for i in self._fil_valgt:
            self._fil_valgt[i] = False
            v = list(self._tree.item(i, "values")); v[0] = "☐"
            self._tree.item(i, values=v, tags=("behold",))
        self._opdater_stats()

    def _log(self, tekst, tag=""):
        self._log_boks.configure(state="normal")
        self._log_boks.insert("end", tekst + "\n", tag)
        self._log_boks.see("end")
        self._log_boks.configure(state="disabled")

    def _slet_valgte(self):
        markerede = [(i, self._fil_stier[i])
                     for i, v in self._fil_valgt.items() if v]
        if not markerede:
            messagebox.showinfo(T["dupe_none_t"], T["dupe_none"])
            return
        bytes_ = sum(os.path.getsize(s) for _, s in markerede if os.path.exists(s))
        if not messagebox.askyesno(
            T["dupe_confirm_t"],
            T["dupe_confirm"].format(len(markerede), _format_bytes(bytes_))
        ):
            return

        self._slet_knap.config(state="disabled")
        self._progressbar["value"] = 0
        self._pct_lbl.config(text="0%")
        self._prog_lbl.config(text=T["dupe_deleting"], fg=TEKST)
        self.update_idletasks()

        total = len(markerede)
        slettet = fejl = 0
        for nr, (item_id, sti) in enumerate(markerede, 1):
            pct = int((nr / total) * 100)
            self._progressbar["value"] = pct
            self._pct_lbl.config(text=f"{pct}%")
            self._prog_lbl.config(text=os.path.basename(sti)[:60])
            self.update_idletasks()

            if slet_til_papirkurv(sti):
                self._tree.delete(item_id)
                del self._fil_valgt[item_id]
                del self._fil_stier[item_id]
                slettet += 1
                self._log(T["dupe_trash_ok"].format(os.path.basename(sti)), "grøn")
            else:
                self._log(T["dupe_trash_fail"].format(os.path.basename(sti)), "rød")
                fejl += 1

        self._progressbar["value"] = 100
        self._pct_lbl.config(text="100%")
        self._prog_lbl.config(text=T["dupe_done_lbl"], fg=GRØN)
        self._log(T["dupe_del_done"].format(slettet, fejl),
                  "grøn" if not fejl else "gul")
        self._opdater_stats()
        self._slet_knap.config(state="normal")


# ───────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(T["app_title"].format(VERSION))
        self.resizable(True, True)
        self.minsize(660, 500)
        self.configure(bg=BG)
        self._kører        = False
        self._stop         = False
        self._valgte_mapper = []
        self._søge_mode    = tk.StringVar(value="drev")
        self._custom_dest  = tk.StringVar(value="")
        self._dest_mode    = tk.StringVar(value="auto")
        self._byg_gui()
        self._centrer(700, 820)

    def _centrer(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # Sørg for vinduet ikke er større end skærmen
        w = min(w, sw - 40)
        h = min(h, sh - 60)
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Byg GUI ─────────────────────────────────────
    def _byg_gui(self):

        # ── Titel (fast i toppen) ─────────────────────
        top = tk.Frame(self, bg=ACCENT, pady=14)
        top.pack(fill="x", side="top")
        titel_ramme = tk.Frame(top, bg=ACCENT)
        titel_ramme.pack(fill="x")
        tk.Label(titel_ramme, text=T["app_heading"],
                 font=("Segoe UI", 20, "bold"), bg=ACCENT, fg="white").pack(side="left", expand=True)
        tk.Button(titel_ramme, text=f"🌐  {T['lang_btn']}", font=("Segoe UI", 11),
                  bg=ACCENT, fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=12, pady=4,
                  activebackground="#6a58e0", activeforeground="white",
                  command=self._skift_sprog).pack(side="right", padx=(0, 16))
        tk.Label(top, text=T["app_sub"].format(VERSION),
                 font=("Segoe UI", 9), bg=ACCENT, fg="#e0d9ff").pack()

        # ── Knapper (faste i bunden) ──────────────────
        bund = tk.Frame(self, bg=BG, pady=12)
        bund.pack(fill="x", side="bottom")

        self.start_knap = tk.Button(
            bund, text=T["btn_start"],
            font=("Segoe UI", 12, "bold"),
            bg=ACCENT, fg="white", relief="flat", padx=26, pady=10,
            cursor="hand2", activebackground="#6a58e0", activeforeground="white",
            command=self.start
        )
        self.start_knap.pack(side="left", padx=(30, 8))

        self.stop_knap = tk.Button(
            bund, text=T["btn_stop"],
            font=("Segoe UI", 12),
            bg="#45475a", fg=TEKST, relief="flat", padx=26, pady=10,
            cursor="hand2", activebackground="#585b70", activeforeground=TEKST,
            command=self.stop, state="disabled"
        )
        self.stop_knap.pack(side="left", padx=8)

        self.dublet_knap = tk.Button(
            bund, text=T["btn_dupes"],
            font=("Segoe UI", 12),
            bg="#313145", fg=TEKST, relief="flat", padx=20, pady=10,
            cursor="hand2", activebackground="#3a3a5e", activeforeground=TEKST,
            command=self.start_dubletter
        )
        self.dublet_knap.pack(side="left", padx=8)

        tk.Button(
            bund, text=T["btn_close"],
            font=("Segoe UI", 12),
            bg=PANEL, fg=TEKST, relief="flat", padx=26, pady=10,
            cursor="hand2", activebackground="#3a3a5e", activeforeground=TEKST,
            command=self.destroy
        ).pack(side="left", padx=8)

        # ── Separator ────────────────────────────────
        tk.Frame(self, bg="#313145", height=2).pack(fill="x", side="bottom")

        # ── Scrollbart canvas til alt indhold ─────────
        canvas_ramme = tk.Frame(self, bg=BG)
        canvas_ramme.pack(fill="both", expand=True, side="top")

        self._canvas = tk.Canvas(canvas_ramme, bg=BG, highlightthickness=0)
        v_scroll = tk.Scrollbar(canvas_ramme, orient="vertical",
                                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Indholdsramme inde i canvas
        indhold = tk.Frame(self._canvas, bg=BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=indhold, anchor="nw"
        )

        # Opdater scroll-region når indhold ændrer størrelse
        def _on_frame_configure(e):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        indhold.bind("<Configure>", _on_frame_configure)

        # Sørg for indhold fylder hele canvas-bredden
        def _on_canvas_configure(e):
            self._canvas.itemconfig(self._canvas_window, width=e.width)
        self._canvas.bind("<Configure>", _on_canvas_configure)

        # Scroll med musehjul
        def _on_mousewheel(e):
            self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self._canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── INDHOLD ──────────────────────────────────
        wrap = tk.Frame(indhold, bg=BG)
        wrap.pack(fill="both", expand=True, padx=24, pady=12)

        # ── SØGE-TILSTAND ────────────────────────────
        self._sektion(wrap, T["sec_search"])
        mode_ramme = tk.Frame(wrap, bg=PANEL, padx=16, pady=10)
        mode_ramme.pack(fill="x", pady=(0, 6))

        mode_top = tk.Frame(mode_ramme, bg=PANEL)
        mode_top.pack(fill="x")

        tk.Radiobutton(
            mode_top, text=T["search_drive"],
            variable=self._søge_mode, value="drev",
            font=("Segoe UI", 11), bg=PANEL, fg=TEKST,
            selectcolor=BG, activebackground=PANEL, activeforeground=TEKST,
            command=self._opdater_mode
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            mode_top, text=T["search_folders"],
            variable=self._søge_mode, value="mapper",
            font=("Segoe UI", 11), bg=PANEL, fg=TEKST,
            selectcolor=BG, activebackground=PANEL, activeforeground=TEKST,
            command=self._opdater_mode
        ).pack(side="left")

        # ── Container med fast position til drev/mappe-valg ──────
        _søge_container = tk.Frame(wrap, bg=BG)
        _søge_container.pack(fill="x")

        # ── DREV-SEKTION ─────────────────────────────
        self.drev_ramme = tk.Frame(_søge_container, bg=PANEL, padx=16, pady=10)
        self.drev_ramme.pack(fill="x", pady=(0, 6))

        tk.Label(self.drev_ramme, text=T["lbl_drive"],
                 font=("Segoe UI", 10, "bold"), bg=PANEL, fg=DIM).pack(anchor="w", pady=(0,6))

        drev_knapper = tk.Frame(self.drev_ramme, bg=PANEL)
        drev_knapper.pack(fill="x")

        drev_liste = find_drev()
        self.valgt_drev = tk.StringVar(value=drev_liste[0] if drev_liste else "C:\\")
        for drev in drev_liste:
            tk.Radiobutton(
                drev_knapper, text=f"  {drev}", variable=self.valgt_drev, value=drev,
                font=("Segoe UI", 12), bg=PANEL, fg=TEKST,
                selectcolor=BG, activebackground=PANEL, activeforeground=TEKST,
            ).pack(side="left", padx=10)

        # ── MAPPE-SEKTION ─────────────────────────────
        self.mappe_ydre = tk.Frame(_søge_container, bg=PANEL, padx=16, pady=10)

        mappe_header = tk.Frame(self.mappe_ydre, bg=PANEL)
        mappe_header.pack(fill="x", pady=(0, 8))

        tk.Label(mappe_header, text=T["lbl_folders"],
                 font=("Segoe UI", 10, "bold"), bg=PANEL, fg=DIM).pack(side="left")

        knap_style = dict(font=("Segoe UI", 9), relief="flat", padx=10, pady=4,
                          cursor="hand2", bd=0)

        tk.Button(
            mappe_header, text=T["btn_add"],
            bg=ACCENT, fg="white",
            activebackground="#6a58e0", activeforeground="white",
            command=self._tilføj_mappe, **knap_style
        ).pack(side="right", padx=(4, 0))

        tk.Button(
            mappe_header, text=T["btn_remove"],
            bg="#45475a", fg=TEKST,
            activebackground="#585b70", activeforeground=TEKST,
            command=self._fjern_mappe, **knap_style
        ).pack(side="right", padx=(4, 0))

        tk.Button(
            mappe_header, text=T["btn_clear"],
            bg="#45475a", fg=TEKST,
            activebackground="#585b70", activeforeground=TEKST,
            command=self._ryd_mapper, **knap_style
        ).pack(side="right", padx=(0, 8))

        liste_ramme = tk.Frame(self.mappe_ydre, bg="#13131f")
        liste_ramme.pack(fill="both", expand=True)

        self.mappe_liste = tk.Listbox(
            liste_ramme, font=("Consolas", 9),
            bg="#13131f", fg=TEKST, selectbackground=ACCENT,
            selectforeground="white", bd=0, highlightthickness=0,
            height=6, activestyle="none"
        )
        mappe_sb = tk.Scrollbar(liste_ramme, command=self.mappe_liste.yview, bg=PANEL)
        self.mappe_liste.configure(yscrollcommand=mappe_sb.set)
        mappe_sb.pack(side="right", fill="y")
        self.mappe_liste.pack(fill="both", expand=True, padx=4, pady=4)

        self.ingen_mapper_lbl = tk.Label(
            self.mappe_ydre,
            text=T["no_folders"],
            font=("Segoe UI", 9, "italic"), bg=PANEL, fg=DIM, anchor="w"
        )
        self.ingen_mapper_lbl.pack(fill="x", pady=(4, 0))

        self._opdater_mode()

        # ── TYPE-VALG ─────────────────────────────────
        self._sektion(wrap, T["sec_type"])
        type_ramme = tk.Frame(wrap, bg=PANEL, padx=16, pady=10)
        type_ramme.pack(fill="x", pady=(0, 6))

        self.valgt_type = tk.StringVar(value="billeder")
        typer = [
            (T["type_photos"], "billeder",   T["hint_photos"]),
            (T["type_videos"], "videoer",    T["hint_videos"]),
            (T["type_docs"],   "dokumenter", T["hint_docs"]),
        ]
        for label, val, hint in typer:
            række = tk.Frame(type_ramme, bg=PANEL)
            række.pack(fill="x", pady=2)
            tk.Radiobutton(
                række, text=label, variable=self.valgt_type, value=val,
                font=("Segoe UI", 11), bg=PANEL, fg=TEKST,
                selectcolor=BG, activebackground=PANEL, activeforeground=TEKST,
                width=18, anchor="w",
                command=self._opdater_type_mode
            ).pack(side="left")
            tk.Label(række, text=hint, font=("Segoe UI", 9),
                     bg=PANEL, fg=DIM).pack(side="left")

        # ── SORTERINGSMODE ────────────────────────────
        self.valgt_sort = tk.StringVar(value="dato")
        self.sort_mode_ramme = tk.Frame(wrap, bg="#232336", padx=16, pady=12)

        tk.Label(self.sort_mode_ramme,
                 text=T["sort_label"],
                 font=("Segoe UI", 9, "bold"), bg="#232336", fg=DIM
                 ).pack(anchor="w", pady=(0, 6))

        tk.Radiobutton(
            self.sort_mode_ramme,
            text=T["sort_date"],
            variable=self.valgt_sort, value="dato",
            font=("Segoe UI", 11), bg="#232336", fg=TEKST,
            selectcolor=BG, activebackground="#232336", activeforeground=TEKST,
            command=self._opdater_dest_hint
        ).pack(anchor="w", pady=2)

        tk.Radiobutton(
            self.sort_mode_ramme,
            text=T["sort_gps"],
            variable=self.valgt_sort, value="gps",
            font=("Segoe UI", 11), bg="#232336", fg=TEKST,
            selectcolor=BG, activebackground="#232336", activeforeground=TEKST,
            command=self._opdater_dest_hint
        ).pack(anchor="w", pady=2)

        tk.Label(
            self.sort_mode_ramme,
            text=T["sort_gps_hint"],
            font=("Segoe UI", 8, "italic"), bg="#232336", fg=DIM
        ).pack(anchor="w", pady=(0, 2))

        # Vis som standard (billeder er valgt fra start)
        self.sort_mode_ramme.pack(fill="x", pady=(0, 6))

        # ── PROGRESS ─────────────────────────────────
        self._sektion(wrap, T["sec_progress"])
        prog_ramme = tk.Frame(wrap, bg=PANEL, padx=16, pady=10)
        prog_ramme.pack(fill="x", pady=(0, 6))

        self.status_lbl = tk.Label(prog_ramme, text=T["status_ready"],
                                   font=("Segoe UI", 9), bg=PANEL, fg=DIM, anchor="w")
        self.status_lbl.pack(fill="x")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Prog.Horizontal.TProgressbar",
                        troughcolor=BG, background=ACCENT, thickness=20)
        self.progressbar = ttk.Progressbar(
            prog_ramme, style="Prog.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate"
        )
        self.progressbar.pack(fill="x", pady=(6, 2))
        self.pct_lbl = tk.Label(prog_ramme, text="0%",
                                font=("Segoe UI", 9, "bold"), bg=PANEL, fg=ACCENT)
        self.pct_lbl.pack(anchor="e")

        # ── LOG ──────────────────────────────────────
        self._sektion(wrap, T["sec_log"])
        log_ydre = tk.Frame(wrap, bg=PANEL, pady=2, padx=2)
        log_ydre.pack(fill="x", pady=(0, 6))

        self.log_boks = tk.Text(
            log_ydre, height=9, font=("Consolas", 9),
            bg="#13131f", fg=TEKST, bd=0, state="disabled", wrap="word"
        )
        log_sb = tk.Scrollbar(log_ydre, command=self.log_boks.yview, bg=PANEL)
        self.log_boks.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side="right", fill="y")
        self.log_boks.pack(fill="both", expand=True)

        self.log_boks.tag_configure("grøn", foreground=GRØN)
        self.log_boks.tag_configure("rød",  foreground=RØD)
        self.log_boks.tag_configure("gul",  foreground=GUL)
        self.log_boks.tag_configure("hvid", foreground=TEKST)


    # ── Hjælpe-metoder ───────────────────────────────
    def _opdater_type_mode(self):
        """Vis/skjul billede-sorteringsvalg afhængig af valgt type."""
        self._opdater_dest_hint()
        if self.valgt_type.get() == "billeder":
            self.sort_mode_ramme.pack(fill="x", pady=(6, 0))
        else:
            self.sort_mode_ramme.pack_forget()

    def _opdater_dest_hint(self):
        """Opdater auto-destinations teksten når type eller sort ændres."""
        type_ = self.valgt_type.get()
        try:
            sort = self.valgt_sort.get()
        except Exception:
            sort = "dato"
        if type_ == "billeder" and sort == "gps":
            navn = T["dest_gps"]
        else:
            navne = {"billeder": T["dest_photos"], "videoer": T["dest_videos"], "dokumenter": T["dest_docs"]}
            navn  = navne.get(type_, T["dest_photos"])
        if hasattr(self, "_auto_dest_lbl"):
            try:
                self._auto_dest_lbl.config(
                    text=T["dest_auto"].format(navn)
                )
            except Exception:
                pass

    def _opdater_dest_mode(self):
        """Vis/skjul manuel mappe-vælger."""
        if self._dest_mode.get() == "manuel":
            self._manuel_ramme.pack(fill="x", pady=(4, 0))
        else:
            self._manuel_ramme.pack_forget()

    def _vælg_dest_mappe(self):
        """Åbn mappe-browser til destinations-valg."""
        valgt = filedialog.askdirectory(
            title=T["dlg_dest"],
            initialdir="C:\\"
        )
        if valgt:
            self._custom_dest.set(os.path.normpath(valgt))

    def _sektion(self, forælder, tekst):
        tk.Label(forælder, text=tekst, font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=DIM, anchor="w").pack(fill="x", pady=(8, 2))

    def _opdater_mode(self):
        """Skifter mellem drev-visning og mappe-visning."""
        if self._søge_mode.get() == "drev":
            self.mappe_ydre.pack_forget()
            self.drev_ramme.pack(fill="x", pady=(0, 6))
        else:
            self.drev_ramme.pack_forget()
            self.mappe_ydre.pack(fill="x", pady=(0, 6))

    def _tilføj_mappe(self):
        """Åbn mappe-browser og tilføj valgt mappe til listen."""
        start_sti = self.valgt_drev.get() if self.valgt_drev.get() else "C:\\"
        valgt = filedialog.askdirectory(
            title=T["dlg_add_folder"],
            initialdir=start_sti
        )
        if valgt and valgt not in self._valgte_mapper:
            # Normaliser stien til Windows-format
            valgt = os.path.normpath(valgt)
            self._valgte_mapper.append(valgt)
            self.mappe_liste.insert("end", f"  📁  {valgt}")
            self.ingen_mapper_lbl.pack_forget()

    def _fjern_mappe(self):
        """Fjern den valgte mappe fra listen."""
        valgt = self.mappe_liste.curselection()
        if not valgt:
            return
        idx = valgt[0]
        self.mappe_liste.delete(idx)
        del self._valgte_mapper[idx]
        if not self._valgte_mapper:
            self.ingen_mapper_lbl.pack(fill="x", pady=(4, 0))

    def _ryd_mapper(self):
        """Fjern alle mapper fra listen."""
        self.mappe_liste.delete(0, "end")
        self._valgte_mapper.clear()
        self.ingen_mapper_lbl.pack(fill="x", pady=(4, 0))

    def log(self, tekst, farve=None):
        tag = {GRØN: "grøn", RØD: "rød", GUL: "gul"}.get(farve, "hvid")
        def _():
            self.log_boks.configure(state="normal")
            self.log_boks.insert("end", tekst + "\n", tag)
            self.log_boks.see("end")
            self.log_boks.configure(state="disabled")
        self.after(0, _)

    def opdater_progress(self, n, total, filnavn):
        def _():
            pct = int((n / total) * 100) if total else 0
            self.progressbar["value"] = pct
            self.pct_lbl.config(text=f"{pct}%")
            self.status_lbl.config(text=filnavn[:70])
        self.after(0, _)

    def _skift_sprog(self):
        """Åbn sprogvælger og genstart GUI med nyt sprog."""
        picker = SprogVælger(self)
        self.wait_window(picker)
        if picker.valgt:
            set_sprog(picker.valgt)
            self.destroy()
            app = App()
            app.mainloop()

    def stop(self):
        self._stop = True
        self.stop_knap.config(state="disabled")

    # ── Start ────────────────────────────────────────
    def start(self):
        if self._kører:
            return

        mode  = self._søge_mode.get()
        type_ = self.valgt_type.get()

        # Bestem søgemapper
        if mode == "drev":
            drev      = self.valgt_drev.get()
            rødder    = [drev]
            søge_tekst = drev
            auto_drev  = drev[0]
        else:
            if not self._valgte_mapper:
                messagebox.showwarning(T["dlg_no_folders_t"], T["dlg_no_folders"])
                return
            rødder     = self._valgte_mapper
            søge_tekst = f"{len(rødder)} valgte mapper"
            auto_drev  = self._valgte_mapper[0][0]

        # Bestem destinations-mappe
        try:
            dest_mode  = self._dest_mode.get()
            custom     = self._custom_dest.get().strip()
        except Exception:
            dest_mode  = "auto"
            custom     = ""

        # Sorteringsmode for billeder
        try:
            sort_mode = self.valgt_sort.get()
        except Exception:
            sort_mode = "dato"

        if dest_mode == "manuel" and custom:
            dest = custom
        else:
            if type_ == "billeder" and sort_mode == "gps":
                dest_navn = T["dest_gps"]
            else:
                dest_navn = {
                    "billeder":   T["dest_photos"],
                    "videoer":    T["dest_videos"],
                    "dokumenter": T["dest_docs"]
                }[type_]
            dest = auto_drev + ":\\" + dest_navn

        if not messagebox.askyesno(
            T["dlg_confirm_t"],
            T["dlg_confirm"].format(søge_tekst, dest)
        ):
            return

        self._kører = True
        self._stop  = False
        self.start_knap.config(state="disabled", text=T["btn_running"])
        self.stop_knap.config(state="normal")
        self.progressbar["value"] = 0
        self.pct_lbl.config(text="0%")

        self.log_boks.configure(state="normal")
        self.log_boks.delete("1.0", "end")
        self.log_boks.configure(state="disabled")

        if mode == "mapper":
            self.log(T["log_search_folders"].format(len(rødder)))
            for m in rødder:
                self.log(f"     {m}")
            self.log("")

        def kør():
            if type_ == "billeder" and sort_mode == "gps":
                kør_billeder_gps(rødder, dest, self.log, self.opdater_progress, lambda: self._stop)
            elif type_ == "billeder":
                kør_billeder(rødder, dest, self.log, self.opdater_progress, lambda: self._stop)
            elif type_ == "videoer":
                kør_videoer(rødder, dest, self.log, self.opdater_progress, lambda: self._stop)
            elif type_ == "dokumenter":
                kør_dokumenter(rødder, dest, self.log, self.opdater_progress, lambda: self._stop)

            def færdig():
                self._kører = False
                self.start_knap.config(state="normal", text=T["btn_start"])
                self.stop_knap.config(state="disabled")
                self.progressbar["value"] = 100
                self.pct_lbl.config(text="100%")
                self.status_lbl.config(text=T["status_done"])
            self.after(0, færdig)

        threading.Thread(target=kør, daemon=True).start()

    # ── Find dubletter ───────────────────────────────
    def start_dubletter(self):
        if self._kører:
            return

        mode = self._søge_mode.get()
        if mode == "drev":
            rødder     = [self.valgt_drev.get()]
            søge_tekst = self.valgt_drev.get()
        else:
            if not self._valgte_mapper:
                messagebox.showwarning(T["dlg_no_folders_t"], T["dlg_no_folders"])
                return
            rødder     = self._valgte_mapper
            søge_tekst = f"{len(rødder)} valgte mapper"

        self._kører = True
        self._stop  = False
        self.start_knap.config(state="disabled")
        self.dublet_knap.config(state="disabled", text=T["btn_scanning"])
        self.stop_knap.config(state="normal")
        self.progressbar["value"] = 0
        self.pct_lbl.config(text="0%")

        self.log_boks.configure(state="normal")
        self.log_boks.delete("1.0", "end")
        self.log_boks.configure(state="disabled")
        self.log(T["log_search_in"].format(søge_tekst) + "\n")

        def kør():
            grupper = find_dubletter_filer(
                rødder, self.log, self.opdater_progress, lambda: self._stop
            )

            def færdig():
                self._kører = False
                self.start_knap.config(state="normal")
                self.dublet_knap.config(state="normal", text=T["btn_dupes"])
                self.stop_knap.config(state="disabled")
                self.progressbar["value"] = 100
                self.pct_lbl.config(text="100%")
                self.status_lbl.config(text=T["status_scan_done"])
                if grupper:
                    DubletVindue(self, grupper)
                else:
                    messagebox.showinfo(T["dupe_no_t"], T["dupe_no"])
            self.after(0, færdig)

        threading.Thread(target=kør, daemon=True).start()


# ───────────────────────────────────────────────────
#  START
# ───────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except Exception:
        pass

    # ── Sprog-valg ──────────────────────────────────
    saved = init_sprog()
    if not saved:
        # Første opstart: vis sprogvælger
        root = tk.Tk()
        root.withdraw()
        picker = SprogVælger(root)
        root.wait_window(picker)
        root.destroy()
        set_sprog(picker.valgt or "en")

    app = App()
    app.mainloop()
