# pip freeze > requirements.txt
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


def fetch_transcript(video_id, language="ko"):
    """
    유튜브 video_id와 언어코드로 자막(스크립트) 텍스트를 반환
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        transcript = None

        try:
            transcript = transcript_list.find_transcript([language])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript([language])
            except Exception:
                try:
                    transcript = next(iter(transcript_list))
                except Exception:
                    return "Error: No transcript available."

        lang_info = transcript.language_code if transcript else ""

        transcript_data = transcript.fetch()
        text_list = []

        for entry in transcript_data:
            if hasattr(entry, 'text') and entry.text:
                text_list.append(entry.text)
            elif isinstance(entry, dict) and 'text' in entry:
                text_list.append(entry['text'])

        full_text = ' '.join(text_list)
        return f"[{lang_info}] {full_text}"

    except Exception as e:
        return f"Error fetching transcript: {e}"
    
def get_youtube_title_alternative(video_url):
    try:
        response = requests.get(video_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("meta", property="og:title")
        return title["content"] if title else "Error: Title not found in the page"
    except Exception as e:
        return f"Error fetching title: {e}"
    
def get_video_id(url: str) -> str:
    """
    유튜브 URL에서 video_id 추출
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [None])[0]
    elif parsed_url.hostname in ["youtu.be"]:
        return parsed_url.path.lstrip("/")
    return None

video_id = get_video_id("https://www.youtube.com/watch?v=YKrNsHX9dzY")
title = get_youtube_title_alternative("https://www.youtube.com/watch?v=YKrNsHX9dzY")
result = fetch_transcript(video_id, "ko")

print(title, result)