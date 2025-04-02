import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import base64
import json

# GitHub Repo & Workflow Details
GITHUB_REPO = "Adarsh-Polsey/daily_glitch"  # Your repo
NEWS_FILE_PATH = "news_list.py"  # Path inside the repo
WORKFLOW_FILENAME = "news_update.yml"  # GitHub Actions workflow file

if os.getenv("GITHUB_ACTIONS") is None:
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_REPO_TOKEN")  # Store in .env or GitHub Secrets
else:
    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    GITHUB_TOKEN = os.environ["GITHUB_REPO_TOKEN"]

if not TOKEN or not GITHUB_TOKEN:
    raise ValueError("❌ Missing Telegram bot token or GitHub token")

# Temporary storage for news messages
news_buffer = []

def get_file_sha():
    """Fetch the current SHA of news_list.py for updating it via GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{NEWS_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["sha"]
    return None

def update_github_news(update):
    """Update news_list.py file on GitHub using API."""
    global news_buffer
    if not news_buffer:
        update.message.reply_text("⚠️ No new news to update!")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{NEWS_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Get current file SHA
    file_sha = get_file_sha()

    # Format news as Python list
    formatted_news = '\n'.join([f'"{news}"' for news in news_buffer])
    new_content = f'news_list = [\n    {formatted_news}\n]'

    # Encode content to base64 (GitHub API requires this)
    encoded_content = base64.b64encode(new_content.encode()).decode()

    data = {
        "message": "Updated news_list.py via Telegram bot",
        "content": encoded_content,
        "sha": file_sha  # Required for updating existing files
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200 or response.status_code == 201:
        update.message.reply_text("✅ News list updated on GitHub!")
        news_buffer.clear()  # Clear buffer after successful update
        trigger_github_workflow(update)
    else:
        update.message.reply_text(f"❌ Failed to update file: {response.text}")

def trigger_github_workflow(update):
    """Trigger GitHub Actions workflow via API after updating news_list.py."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILENAME}/dispatches"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {"ref": "main"}  # Adjust branch if necessary

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        update.message.reply_text("✅ GitHub Actions workflow triggered!")
    else:
        update.message.reply_text(f"❌ Failed to trigger workflow: {response.text}")

def start(update: Update, context: CallbackContext):
    """Handle /start command."""
    update.message.reply_text("Welcome! Send me your news, and I'll handle the rest.")

def store_news(update: Update, context: CallbackContext):
    """Store news messages or trigger update."""
    global news_buffer
    news_message = update.message.text.strip()

    if news_message == "/push":
        update_github_news(update)
    else:
        news_buffer.append(news_message)
        update.message.reply_text("📝 News stored! Send /push to save and trigger update.")

def main():
    """Start the Telegram bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.text & ~filters.command, store_news))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()