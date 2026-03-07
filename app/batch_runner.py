"""
author: @abhiyanhaze
description: Batch runner — processes all clinical notes in data/notes/ and
             writes per-note JSON results to the output/ directory.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.utils.logger import logger

NOTES_DIR = Path(__file__).parent.parent / "data" / "notes"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _process_note(note_file: Path) -> tuple[str, list | None]:
    from app.graph.medicoder_pipeline import run

    try:
        results = run(str(note_file))
        output_path = OUTPUT_DIR / f"{note_file.name}.json"
        output_path.write_text(
            json.dumps({"note": note_file.name, "results": results}, indent=2),
            encoding="utf-8",
        )
        logger.info("Saved results", file=output_path.name, num_conditions=len(results))
        return note_file.name, results
    except Exception as e:
        logger.error("Failed to process note", file=note_file.name, error=str(e), exc_info=True)
        return note_file.name, None


def run_batch() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not NOTES_DIR.is_dir():
        logger.warning("Notes directory not found", path=str(NOTES_DIR))
        return

    note_files = [f for f in sorted(NOTES_DIR.iterdir()) if f.is_file()]
    if not note_files:
        logger.warning("No note files found", path=str(NOTES_DIR))
        return

    logger.info("Starting batch run", total=len(note_files), output_dir=str(OUTPUT_DIR))

    passed, failed = 0, 0

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_process_note, f): f for f in note_files}
        for future in as_completed(futures):
            note_file = futures[future]
            logger.info("Processing note", file=note_file.name)
            _, result = future.result()
            if result is not None:
                passed += 1
            else:
                failed += 1

    logger.info("Batch complete", passed=passed, failed=failed)


if __name__ == "__main__":
    run_batch()
    sys.exit(0)
