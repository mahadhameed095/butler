import os
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
SAMPLE_SYNC = os.path.join(BASE, "sample-sync.yaml")
DEFAULT_CLONE_DIR = Path.home() / ".local" / "butler-manifests"