
import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, render_template, request
import requests
from googleapiclient.discovery import build

app = Flask(__name__)
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
YT_API_KEY = os.getenv("YT_API_KEY")
# ====== CONFIG ======
HF_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"

# ====== FUNCTIONS ======
def detect_mood(text):
    response = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={"inputs": text}
    )

    data = response.json()
    print("HF RAW RESPONSE:", data)

    # Case 1: Model still loading or API error
    if isinstance(data, dict):
        # examples: {"error": "..."} or {"estimated_time": ...}
        return "neutral"

    # Case 2: Normal response [[{label, score}]]
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
        return data[0][0]["label"]

    # Fallback
    return "neutral"


def get_songs(mood, language):
    mood_keywords = {
        "happy": "happy upbeat",
        "sad": "sad emotional",
        "angry": "power rage",
        "relaxed": "relaxing calm",
        "energetic": "energetic workout"
    }

    mood_text = mood_keywords.get(mood, "popular")

    # ❌ DO NOT use "playlist"
    query = f"{mood_text} {language} songs"

    youtube = build("youtube", "v3", developerKey=YT_API_KEY)

    request_yt = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=5,

        # ✅ CRITICAL FIXES
        videoCategoryId="10",          # Music only
        videoEmbeddable="true",        # ONLY embeddable videos
        safeSearch="strict"
    )

    response = request_yt.execute()

    songs = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")

        if not video_id:
            continue

        title = snippet.get("title", "Unknown title")
        thumbnail = (
            snippet.get("thumbnails", {})
            .get("medium", {})
            .get("url", "https://via.placeholder.com/320x180?text=No+Thumbnail")
        )

        songs.append({
            "title": title,
            "video_id": video_id,
            "thumbnail": thumbnail
        })

    return songs




# ====== ROUTES ======
@app.route("/", methods=["GET", "POST"])
def index():
    mood = None
    songs = []

    if request.method == "POST":
        mood = request.form.get("mood")
        language = request.form.get("language", "english")

        print("MOOD:", mood)
        print("LANGUAGE:", language)

        songs = get_songs(mood, language)

    return render_template("index.html", mood=mood, songs=songs)






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
