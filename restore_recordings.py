"""Download and verify the historical CSI recordings. Run from any directory."""
from pathlib import Path
import hashlib
import urllib.request
import zipfile

root = Path(__file__).resolve().parent
dest = root / 'work' / 'ruview-data'
dest.mkdir(parents=True, exist_ok=True)
archive = dest / 'recordings.zip'
url = 'https://github.com/irfan347/wifi-csi-fyp/releases/download/data-v1/recordings.zip'
expected = '73aebe684e447f85d3bf458086f0a8bac4874e45743e14feea6398ebff3af12d'
print('Downloading 494 MB archive; allow at least 3.5 GB free disk space.')
urllib.request.urlretrieve(url, archive)
with archive.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual != expected:
    raise RuntimeError('Checksum mismatch: archive will not be extracted.')
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        target = (dest / member.filename).resolve()
        if not target.is_relative_to(dest.resolve()) or not member.filename.startswith('recordings/'):
            raise RuntimeError('Unexpected archive path')
        if target.exists():
            raise RuntimeError(f'Refusing to overwrite existing file: {target}')
    z.extractall(dest)
print('Recordings restored. Archive retained for backup.')
