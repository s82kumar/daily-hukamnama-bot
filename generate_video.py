import os
import asyncio
import requests
import edge_tts
from google import genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx

# 1. Fetch Today's Hukamnama from BaniDB
response = requests.get("https://banidb.com").json()
verses = response["hukamnama"]

gurmukhi_text = "\n".join([v["verse"]["verse"]["unicode"] for v in verses[:4]])
english_full = " ".join([v["verse"]["translation"]["en"]["bdb"] for v in verses])

# 2. Summarize Reflection with Free Gemini API
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt = (
    f"Summarize the core spiritual message of this Daily Hukamnama into a calm, "
    f"respectful 45-second narration script for TikTok. Do not add hashtags or emojis:\n\n{english_full}"
)
narration = client.models.generate_content(
    model="gemini-2.5-flash", contents=prompt
).text.strip()

# 3. Generate Free Neural Voiceover using Edge-TTS
async def make_audio():
    communicate = edge_tts.Communicate(narration, "en-US-AndrewNeural", rate="-10%")
    await communicate.save("voice.mp3")

asyncio.run(make_audio())

# 4. Render 9:16 Vertical Video with Automatic Looping
audio = AudioFileClip("voice.mp3")
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
