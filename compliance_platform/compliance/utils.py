import hashlib


def calculate_checksums(file_obj):
    """Calculate SHA-256 and MD5 checksums for a file."""
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(8192), b''):
        sha256.update(chunk)
        md5.update(chunk)
    file_obj.seek(0)
    return sha256.hexdigest(), md5.hexdigest()


def verify_document_checksum(document):
    """Verify a document's checksum against stored value."""
    if not document.file:
        return False, "No file attached"
    try:
        sha256, md5 = calculate_checksums(document.file)
        if sha256 == document.checksum_sha256:
            return True, "Checksum verified - document integrity confirmed"
        else:
            return False, f"Checksum mismatch! Expected: {document.checksum_sha256[:16]}... Got: {sha256[:16]}..."
    except Exception as e:
        return False, f"Verification failed: {str(e)}"
