import json
import subprocess

with open("config.json") as f:
    config = json.load(f)

APIKEY = config["APIKEY"]

news = subprocess.check_output(["python", "fetch_news.py", "https://tldr.tech/tech/2025-03-11"]).decode("utf-8")
gpt_news = subprocess.check_output(["curl", "-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps({"prompt": "summarize this news in 4 paragraphs", "text": news}), "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={APIKEY}"]).decode("utf-8")

with open("news.json", "w") as f:
    json.dump(json.loads(gpt_news), f, indent=4)
