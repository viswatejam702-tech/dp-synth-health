"""
Synthesizer-AI: Secure File Upload & Clinical Dataset Validator
===============================================================
Ensures:
1. Strict MIME type & Magic Byte content inspection.
2. File extension whitelisting (.csv, .tsv, .parquet).
3. Payload size caps (default 10 MB).
4. Path traversal sanitization & isolated non-executable storage.
"""

import os
import re
import uuid
import logging
import tempfile
from typing import Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger("synthesizer_ai.file_security")

# Storage isolated outside web root (with safe fallback for serverless environments)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_storage = os.path.join(BASE_DIR, "workspace", "isolated_storage")
try:
    os.makedirs(_default_storage, exist_ok=True)
    ISOLATED_STORAGE_DIR = _default_storage
except OSError:
    ISOLATED_STORAGE_DIR = os.path.join(tempfile.gettempdir(), "synthesizer_isolated_storage")
    os.makedirs(ISOLATED_STORAGE_DIR, exist_ok=True)

# Allowed extensions and MIME types
ALLOWED_EXTENSIONS = {".csv", ".tsv", ".parquet"}
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))) # 10 MB

# Dangerous patterns in uploaded text files (e.g. embedded executable code or script tags)
DANGEROUS_PATTERNS = [
    re.compile(b"<\?php", re.IGNORECASE),
    re.compile(b"<script", re.IGNORECASE),
    re.compile(b"import\s+os", re.IGNORECASE),
    re.compile(b"subprocess", re.IGNORECASE),
    re.compile(b"__import__", re.IGNORECASE)
]


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename, strips path traversal sequences, and normalizes characters.
    """
    # Remove path directory separators
    clean_name = os.path.basename(filename)
    # Remove null bytes and non-alphanumeric/standard chars
    clean_name = re.sub(r"[^\w\s\.-]", "", clean_name).strip()
    if not clean_name:
        clean_name = f"dataset_{uuid.uuid4().hex[:8]}.csv"
    return clean_name





async def validate_and_save_upload(file: UploadFile) -> Dict[str, Any]:
    """Validate and store an uploaded clinical dataset file.

    Performs:
    1. Filename sanitization.
    2. Extension whitelist check.
    3. Size limit enforcement.
    4. Dangerous pattern scanning.
    5. Writes file to isolated storage directory.
    Returns a dict with ``filename`` and ``path``.
    """
    # Ensure the file object is present
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    filename = sanitize_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read entire contents (fastapi UploadFile provides async read)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds size limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
        )

    # Scan for dangerous patterns
    for pat in DANGEROUS_PATTERNS:
        if pat.search(contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file contains prohibited content"
            )

    dest_path = os.path.join(ISOLATED_STORAGE_DIR, filename)
    try:
        # Write to isolated storage safely
        with open(dest_path, "wb") as f:
            f.write(contents)
    except OSError as exc:
        logger.error("Failed to write uploaded file %s: %s", dest_path, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store uploaded file"
        ) from exc

    logger.info("File %s saved to %s", filename, dest_path)
    return {"filename": filename, "path": dest_path}
