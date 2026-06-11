import os
from pathlib import Path

from .utils import logger


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
) -> bool:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.warning("YouTube upload dependencies are not installed. Skipping upload.")
        logger.warning("Install: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        return False

    secrets_path = Path("client_secrets.json")
    token_path = Path("youtube_token.json")
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    if not secrets_path.exists():
        logger.warning("client_secrets.json not found. Skipping YouTube upload.")
        return False

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), scopes)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    logger.info(f"Uploading to YouTube: {os.path.basename(video_path)}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

    logger.info(f"YouTube upload completed: https://youtube.com/watch?v={response.get('id')}")
    return True
