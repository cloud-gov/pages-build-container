import tempfile

from pathlib import Path


def patch_dir(monkeypatch, module, dir_constant):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        monkeypatch.setattr(module, dir_constant, tmpdir_path)
        yield tmpdir_path


def create_file(file_path, contents='', mode='w'):
    with file_path.open(mode) as f:
        f.write(contents)
