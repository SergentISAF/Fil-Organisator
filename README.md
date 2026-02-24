# Fil-Organisator

Organisér automatisk billeder, videoer og dokumenter fra dit drev eller specifikke mapper.

## Funktioner

- **Billeder** – sortér efter dato (EXIF) eller GPS-lokation (Land/By)
- **Videoer** – sortér efter dato → `Drev:\Film\År\Måned\`
- **Dokumenter** – sortér i Word / PDF / Excel mapper
- **Dublet-scanner** – find og slet duplikerede filer (flyttes til papirkurven)
- Scanner hele drev ELLER specifikke mapper
- Springer system/spil-mapper over automatisk
- Progress-bar + log i GUI
- Stop-knap til at afbryde

## Installation

### Windows
1. Download `FilOrganisator_Setup.exe` fra [Releases](../../releases)
2. Kør installeren og følg guiden
3. Start fra Startmenuen eller skrivebordet

### Linux (Ubuntu)
1. Download `Linux`-mappen fra [Releases](../../releases)
2. Åbn en terminal i mappen
3. Kør: `bash installer.sh`

### Fra kildekode (kræver Python)
```bash
pip install Pillow exifread reverse_geocoder send2trash
cd "den Simple version"
python organisator.py
```

## Byg selv

### Windows installer
```bash
byg_installer.bat
```
Kræver [Inno Setup 6](https://jrsoftware.org/isdl.php) for at lave installeren.

### Linux
```bash
bash byg_linux.sh
```

## Skærmbillede

Programmet har et mørkt GUI-tema med sektioner for:
- Valg af drev/mapper
- Filtype (billeder, videoer, dokumenter)
- Sorteringsmetode
- Progress og log

## Afhængigheder

- Python 3.8+
- Pillow
- exifread
- reverse_geocoder
- send2trash

## Sprog

Programmet er på dansk (GUI og kode).
