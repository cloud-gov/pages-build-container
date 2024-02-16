import tempfile
import hashlib

from pathlib import Path


def patch_dir(monkeypatch, module, dir_constant):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        monkeypatch.setattr(module, dir_constant, tmpdir_path)
        yield tmpdir_path


def create_file(file_path, contents='', mode='w'):
    with file_path.open(mode) as f:
        f.write(contents)


def generate_file_hash(filename):
    hash_md5 = hashlib.md5()  # nosec

    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()
