from flask import Flask, request, jsonify
from pytubefix import YouTube
import os
import subprocess

app = Flask(__name__)
DOWNLOAD_PATH = "/storage/emulated/0/memo/"

@app.route('/', methods=['POST'])
def download_video():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        yt = YouTube(url, use_po_token=True)
        title = yt.title.replace(" ", "_")

        # Try video in priority order
        video = yt.streams.filter(res="1080p", mime_type="video/mp4", only_video=True).first()
        if not video:
            video = yt.streams.filter(res="720p", mime_type="video/mp4", only_video=True).first()
        if not video:
            video = yt.streams.filter(res="360p", mime_type="video/mp4", only_video=True).first()

        # Get best audio
        audio = yt.streams.filter(only_audio=True, mime_type="audio/mp4").order_by('abr').desc().first()

        if not video or not audio:
            return jsonify({"error": "Suitable video or audio stream not found."}), 404

        video_path = video.download(output_path=DOWNLOAD_PATH, filename="temp_video.mp4")
        audio_path = audio.download(output_path=DOWNLOAD_PATH, filename="temp_audio.mp4")
        output_path = os.path.join(DOWNLOAD_PATH, f"{title}.mp4")

        # Merge using ffmpeg
        ffmpeg_cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        os.remove(video_path)
        os.remove(audio_path)

        return jsonify({"message": "Download complete", "file": output_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
