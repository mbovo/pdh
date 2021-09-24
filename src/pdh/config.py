import yaml
import os
import sys
from rich import print

CONFIG_KEYS = ["apikey", "uid", "email"]


def load_yaml(fileName: str) -> dict:
    cfg = {}
    p = os.path.expanduser(fileName)
    try:
        with open(p, "r") as f:
            cfg = yaml.safe_load(f.read())
    except FileNotFoundError as e:
        print(f"[red]{e}[/red]")
    return cfg


def save_yaml(fileName: str, cfg: dict) -> bool:
    try:
        with open(os.path.expanduser(fileName), "w") as f:
            yaml.safe_dump(cfg, f)
    except Exception as e:
        print(f"[red]{e}[/red]")
        return False
    return True


def valid_config(cfg: dict) -> bool:
    for k in CONFIG_KEYS:
        if k not in cfg.keys():
            return False
    return True


def load_and_validate(fileName: str) -> dict:
    cfg = load_yaml(fileName)
    if not valid_config(cfg):
        print("[red]Invalid or missing config, try pdh config[/red]")
        sys.exit(1)
    return cfg


def setup_config(fileName: str) -> None:
    print("Setup [green]PDH[/green]:")
    cfg = {}
    for k in CONFIG_KEYS:
        print(f"Add Pagerduty {k}:")
        cfg[k] = input(":>")
    save_yaml(fileName, cfg)
