import requests
from bs4 import BeautifulSoup

def fetch_news(url, tag="div", class_name="newsletter-html"):
    news = {}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("✅ - response code "+response.status_code.__str__())

        soup = BeautifulSoup(response.text, "html.parser")
        headlines = soup.find_all(tag, class_=class_name)

        if not headlines:
            return ["No headlines found"]

        for i,headline in enumerate(headlines,0):
            if(i==0):
                continue
            if(i<=2):
                news["Big Tech & Startups"]=headline.text.strip()
            elif(i<=4):
                news["Science & Futuristic Technology"]=headline.text.strip()
            elif(i<=6):
                news["Programming, Design & Data Science"]=headline.text.strip()
            else:
                raise Exception("0 headlines found")

        return [headline.text.strip() for headline in headlines] if headlines else ["No headlines found"]

    except Exception as e:
        return [f"Error fetching news: {str(e)}"]

news_url = "https://tldr.tech/tech/2025-03-11"
news_headlines = fetch_news(news_url)

for i, news in enumerate(news_headlines, 1):
    print(f"{i}. {news}")