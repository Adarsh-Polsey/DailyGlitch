# 🚀 Daily Glitch: Automated News & Stories

**Daily Glitch** is an AI-powered, fully automated news generator that scrapes, formats, and posts news updates to Instagram as posts and stories.

---

## ⚡ Features

- **📰 Automated News Generation** – Fetches trending news.
- **🎨 Auto-Generated Images & Stories** – Creates visuals for posts and stories.
- **📷 Auto-Posting to Instagram** – Hands-free content publishing.
- **🔐 Secure Credentials** – Configured through GitHub Secrets.
- **⏳ Fully Automated** – Fetches, formats, and posts without manual input.

---

## 🫠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/adarsh-polsey/daily_glitch.git
cd daily_glitch
```

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 4. Configure Secrets
Go to:
```
GitHub Repo → Settings → Secrets and variables → Actions → New repository secret
```
🔹 **Secret Name:** `CONFIG_JSON`
🔹 **Secret Value:** Paste your `config.json` file contents.

---

## 🚀 Running the Bot

### 5. Generate News
```bash
python3 news_post.py
```

### 6. Generate Instagram Stories
```bash
python3 story_post.py
```

### 7. Trigger GitHub Workflow
```bash
gh workflow run daily_glitch.yml
```
Or trigger it manually in **GitHub Actions**.

---

## 🤖 Automation

Daily Glitch runs on **GitHub Actions** to automate daily posts and stories.

🔹 **Scheduled Runs:** Configured in `.github/workflows/daily_glitch.yml`
🔹 **Manual Control:** Run it as needed.

---

## 🚨 Disclaimer
- **Use at your own risk.**
- The creators are not responsible for account restrictions or bans.
- Ensure compliance with platform policies.

---

## 💀 Contributing

1. Fork the repo
2. Make a PR
3. Await review

---

### 🎤 Final Note
Daily Glitch is an efficient tool for automating news posts and stories. **Star ⭐ this repo if you find it useful.**

