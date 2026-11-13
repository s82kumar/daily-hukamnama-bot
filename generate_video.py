import os
import requests
import soundfile as sf
from google import genai
from kokoro_onnx import Kokoro
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx

# 1. Fetch Today's Hukamnama from BaniDB
response = requests.get("https://api.gurbaninow.com/v2/hukamnama/today", timeout=30)
response.raise_for_status()
verses = response.json()["hukamnama"]

gurmukhi_text = "\n".join([v["line"]["gurmukhi"]["unicode"] for v in verses[:4]])
english_full = " ".join([v["line"]["translation"]["english"]["default"] for v in verses])

# 2. Summarize Reflection with Free Gemini API
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt = (
    f"Summarize the core spiritual message of this Daily Hukamnama into a calm, "
    f"respectful 45-second narration script for TikTok. Do not add hashtags or emojis:\n\n{english_full}"
)
narration = client.models.generate_content(
    model="gemini-3.8-flash", contents=prompt
).text.strip()

# 3. Generate the narration locally with Kokoro
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
samples, sample_rate = kokoro.create(
    narration, voice="am_michael", speed=0.9, lang="en-us"
)
sf.write("voice.wav", samples, sample_rate)

# 4. Render 9:16 Vertical Video with Automatic Looping
audio = AudioFileClip("voice.wav")
video = VideoFileClip("bg.mp4").fx(vfx.loop, duration=audio.duration + 1).set_audio(audio)

gurmukhi_clip = TextClip(
    gurmukhi_text,
    fontsize=48,
    color="white",
    font="NotoSansGurmukhi-Bold.ttf",
    method="caption",
    size=(900, None),
    align="center"
).set_position(("center", 350)).set_duration(video.duration)

english_clip = TextClip(
    narration,
    fontsize=38,
    color="#FFD700",
    font="Arial",
    method="caption",
    size=(900, None),
    align="center"
).set_position(("center", 950)).set_duration(video.duration)

final_video = CompositeVideoClip([video, gurmukhi_clip, english_clip])
final_video.write_videofile("daily_hukamnama.mp4", fps=24, codec="libx264", audio_codec="aac")
