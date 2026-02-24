#!/bin/bash
# ================================================================
#  Byg Fil-Organisator til Linux (Ubuntu)
#  Kør denne fil i Ubuntu WSL:
#    bash /mnt/c/Users/Danho/PY/Organiserings\ program\ for\ Billeder,film,dokumenter/byg_linux.sh
# ================================================================

set -e

KILDE="/mnt/c/Users/Danho/PY/Organiserings program for Billeder,film,dokumenter"
SCRIPT="$KILDE/den Simple version/organisator.py"
OUTPUT="$KILDE/Færdige version/Linux"

echo ""
echo "  ================================================================"
echo "    BYGGER FIL-ORGANISATOR TIL LINUX"
echo "  ================================================================"
echo ""

# ── Trin 1: Installér systempakker ───────────────────────────────
echo "  [1/4]  Installerer systempakker (kræver sudo)..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-tk python3-dev build-essential > /dev/null
echo "         OK"
echo ""

# ── Trin 2: Installér Python-pakker ──────────────────────────────
echo "  [2/4]  Installerer Python-pakker..."
pip3 install --user pyinstaller pillow exifread reverse_geocoder --quiet
echo "         OK"
echo ""

# ── Trin 3: Byg med PyInstaller ──────────────────────────────────
echo "  [3/4]  Bygger Linux-program (dette tager 2-5 minutter)..."
cd "$KILDE"

~/.local/bin/pyinstaller \
    --onedir \
    --windowed \
    --name "FilOrganisator" \
    --collect-data reverse_geocoder \
    --hidden-import PIL._tkinter_finder \
    --hidden-import exifread \
    --noconfirm \
    --clean \
    --distpath "$KILDE/dist_linux" \
    --workpath "$KILDE/build_linux" \
    "$SCRIPT" > /dev/null 2>&1

echo "         OK"
echo ""

# ── Trin 4: Kopiér til Færdige version/Linux ─────────────────────
echo "  [4/4]  Kopierer til Færdige version/Linux..."
mkdir -p "$OUTPUT"
cp -r "$KILDE/dist_linux/FilOrganisator" "$OUTPUT/"

# Lav installer.sh til brugeren
cat > "$OUTPUT/installer.sh" << 'INSTALLER'
#!/bin/bash
# ── Fil-Organisator installer til Linux ──────────────────────────
set -e

DEST="$HOME/.local/share/FilOrganisator"
DESKTOP="$HOME/.local/share/applications/FilOrganisator.desktop"
BIN="$HOME/.local/bin/FilOrganisator"

echo ""
echo "  Installerer Fil-Organisator..."

# Kopier programfiler
mkdir -p "$DEST"
cp -r FilOrganisator/* "$DEST/"
chmod +x "$DEST/FilOrganisator"

# Opret launcher i PATH
mkdir -p "$HOME/.local/bin"
cat > "$BIN" << EOF
#!/bin/bash
cd "$DEST"
"$DEST/FilOrganisator"
EOF
chmod +x "$BIN"

# Opret .desktop genvej (vises i applikationsmenuen og skrivebordet)
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP" << EOF
[Desktop Entry]
Name=Fil-Organisator
Comment=Organisér billeder, videoer og dokumenter
Exec=$DEST/FilOrganisator
Icon=folder
Terminal=false
Type=Application
Categories=Utility;FileTools;
EOF

# Kopiér genvej til skrivebordet hvis muligt
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP" "$HOME/Desktop/FilOrganisator.desktop"
    chmod +x "$HOME/Desktop/FilOrganisator.desktop"
elif [ -d "$HOME/Skrivebord" ]; then
    cp "$DESKTOP" "$HOME/Skrivebord/FilOrganisator.desktop"
    chmod +x "$HOME/Skrivebord/FilOrganisator.desktop"
fi

echo "  Installeret! Start programmet fra applikationsmenuen"
echo "  eller kør:  FilOrganisator"
echo ""
INSTALLER

chmod +x "$OUTPUT/installer.sh"

# Ryd op i midlertidige byggefiler
rm -rf "$KILDE/dist_linux" "$KILDE/build_linux"

echo "  ================================================================"
echo "    SUCCES!"
echo "    Klar i:  Færdige version/Linux/"
echo ""
echo "    På Ubuntu-PC'en:"
echo "    1. Kopier mappen 'Linux' fra USB-drevet"
echo "    2. Åbn en terminal i mappen"
echo "    3. Kør:  bash installer.sh"
echo "  ================================================================"
echo ""
