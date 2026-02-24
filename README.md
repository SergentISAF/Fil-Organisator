# Fil-Organisator / File Organizer

Automatically organize photos, videos and documents from your drive or specific folders.

Organisér automatisk billeder, videoer og dokumenter fra dit drev eller specifikke mapper.

## Features / Funktioner

- **Photos / Billeder** – sort by date (EXIF) or GPS location (Country/City)
- **Videos / Videoer** – sort by date → `Drive:\Videos\Year\Month\`
- **Documents / Dokumenter** – sort into Word / PDF / Excel folders
- **Duplicate scanner / Dublet-scanner** – find and delete duplicate files (moved to recycle bin)
- Scan entire drives OR specific folders
- Automatically skips system/game folders
- Progress bar + log in GUI
- Stop button to cancel at any time

## 🌐 Multi-language support (10 languages)

Language picker on first launch – switch anytime via the 🌐 button in the title bar.

| | Language | | Language |
|---|---|---|---|
| 🇩🇰 | Dansk | 🇫🇷 | Français |
| 🇬🇧 | English | 🇸🇦 | العربية |
| 🇨🇳 | 简体中文 | 🇧🇩 | বাংলা |
| 🇮🇳 | हिन्दी | 🇧🇷 | Português |
| 🇪🇸 | Español | 🇷🇺 | Русский |

## Installation

### Windows
1. Download `FilOrganisator_Setup.exe` from [Releases](../../releases)
2. Run the installer and follow the wizard
3. Launch from Start Menu or desktop shortcut

### Linux (Ubuntu)
1. Download `FilOrganisator_Linux.tar.gz` and `installer.sh` from [Releases](../../releases)
2. Open a terminal in the download folder
3. Run: `bash installer.sh`

### From source (requires Python)
```bash
pip install Pillow exifread reverse_geocoder send2trash
cd "den Simple version"
python organisator.py
```

## Build it yourself

### Windows installer
```bash
byg_installer.bat
```
Requires [Inno Setup 6](https://jrsoftware.org/isdl.php) to create the installer.

### Linux
```bash
bash byg_linux.sh
```

## Screenshots

Dark-themed GUI with sections for:
- Drive/folder selection
- File type (photos, videos, documents)
- Sort method (date or GPS location)
- Progress bar and log
- Duplicate scanner with file selection

## Dependencies

- Python 3.8+
- Pillow
- exifread
- reverse_geocoder
- send2trash

## License

Free to use and share.
