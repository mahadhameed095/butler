from pathlib import Path
from platformdirs import user_config_dir, user_data_dir

BASE = Path(__file__).parent

CONFIG_PATH = Path(user_config_dir("butler")) / "config.json"
SAMPLE_SYNC = BASE / "sample-sync.yaml"
DEFAULT_CLONE_DIR = Path(user_data_dir("butler")) / "manifests"
DEFAULT_BUTLER_SERVER_CLONE_DIR = "~/butler/manifests"