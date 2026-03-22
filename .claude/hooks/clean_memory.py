#!/usr/bin/env python3
from __future__ import annotations

import glob
import os
from pathlib import Path

MEMORY_DIR = Path('.claude/memory')


def clean_memory() -> None:
    print('🧹 [Biotech Alpha] Clearing workflow memory artifacts...')
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    removed = 0
    for file_path in glob.glob(str(MEMORY_DIR / '*.json')):
        path = Path(file_path)
        try:
            path.unlink()
            removed += 1
            print(f' - removed: {path.name}')
        except Exception as exc:  # pragma: no cover - defensive CLI logging
            print(f' - failed: {path.name}: {exc}')

    gitkeep = MEMORY_DIR / '.gitkeep'
    if not gitkeep.exists():
        gitkeep.write_text('', encoding='utf-8')

    print(f'✨ Memory clean complete. Removed {removed} JSON file(s).')


if __name__ == '__main__':
    clean_memory()
