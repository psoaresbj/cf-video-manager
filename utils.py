from urllib.parse import urlparse

def extract_uid_from_url(url: str) -> str:
    path = urlparse(url).path
    return path.rstrip("/").split("/")[-1]
