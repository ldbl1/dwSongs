# dwSongs

Build Instructions

python -m PyInstaller --noconfirm --onefile --clean --windowed --name dwSongs --icon "assets/dwSongs.ico" --add-data "assets;assets" --add-data "ffmpeg/bin;ffmpeg/bin" main.py
