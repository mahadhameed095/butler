import subprocess
from pathlib import Path
from contextlib import contextmanager
import shutil
import tempfile

class GitError(Exception):
    pass


def git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {args[0]} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()

@contextmanager
def staged_directory(dest: Path):
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        stg_path = Path(tmp) / dest.name
        if dest.exists():
            shutil.copytree(dest, stg_path)
        else:
            stg_path.mkdir()
        try:
            yield stg_path
            old = dest.parent / f"{dest.name}.old"
            if dest.exists():
                dest.rename(old)
            try:
                stg_path.rename(dest)
                if old.exists():
                    shutil.rmtree(old)
            except Exception:
                if old.exists():
                    old.rename(dest)
                raise
        except Exception:
            raise