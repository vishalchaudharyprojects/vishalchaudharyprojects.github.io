import csv
from loguru import logger
from pathlib import Path
from typing import List, Dict

def read_csv(path: Path) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = [{k.strip(): (v or "").strip() for k, v in row.items()} for row in reader]
            return rows
    except Exception as e:
        logger.error(f"CSV read failed for {path}: {e}")
        return []
