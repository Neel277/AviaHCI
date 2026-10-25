"""Machine-readable provenance records for AviaHCI analyses."""

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from aviahci import __version__


def sha256_file(path, chunk_size=1024 * 1024):
    """Calculate a file's SHA-256 digest without loading it all into memory."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Cannot hash missing input file: {path}")

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_provenance(input_paths, parameters, output_path):
    """Build a JSON-serializable record of an analysis and its inputs."""
    inputs = []

    for item in input_paths:
        path = Path(item).resolve()
        inputs.append({
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    return {
        "schema_version": 1,
        "software": {
            "name": "AviaHCI",
            "version": __version__,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "parameters": parameters,
        "output": {
            "path": str(Path(output_path).resolve()),
        },
        "interpretation_notes": [
            "Presence-background model scores are not calibrated occupancy probabilities.",
            "Spatial validation estimates performance under the configured split strategy.",
            "Background-sampling results depend on the supplied background candidate pool.",
        ],
    }


def write_provenance(record, output_path):
    """Write provenance JSON beside the requested results file."""
    output_path = Path(output_path)
    provenance_path = output_path.with_suffix(
        output_path.suffix + ".provenance.json"
    )
    provenance_path.parent.mkdir(parents=True, exist_ok=True)

    with provenance_path.open("w", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")

    return provenance_path
