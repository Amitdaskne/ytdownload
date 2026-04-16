from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import subprocess

app = Flask(__name__, template_folder="templates")

# Render safe folder
save_path = "downloads"
os.makedirs(save_path, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

# 🔍 Fetch video details
@app.route("/info", methods=["POST"])
def info():
    url = request.form["url"]

    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)

    allowed = ["240","480","720","1080"]
    formats = []

    for f in data["formats"]:
        if f.get("height") and str(f["height"]) in allowed:
            formats.append({
                "quality": str(f["height"]) + "p",
                "id": f["format_id"]
            })

    unique = {f["quality"]: f for f in formats}.values()

    return jsonify({
        "title": data["title"],
        "thumbnail": data["thumbnail"],
        "formats": list(unique)
    })

# ⬇️ Download
@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    fmt = request.form["format"]
    mode = request.form["mode"]

    if mode == "mp3":
        command = f'''yt-dlp -x --audio-format mp3 -o "{save_path}/%(title)s.%(ext)s" "{url}"'''
    else:
        command = f'''yt-dlp -f "{fmt}+bestaudio" --merge-output-format mp4 -o "{save_path}/%(title)s.%(ext)s" "{url}"'''

    subprocess.call(command, shell=True)

    files = os.listdir(save_path)
    latest = max([os.path.join(save_path, f) for f in files], key=os.path.getctime)

    return jsonify({"file": latest})

@app.route("/getfile")
def getfile():
    path = request.args.get("path")
    return send_file(path, as_attachment=True)

# Render compatible port
import os
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
