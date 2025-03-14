import datetime
import requests
from bs4 import BeautifulSoup

def fetch_news(tag="div", class_name="newsletter-html"):
    try:
        # Generate yesterday's date for the URL
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        url = f"https://tldr.tech/tech/{date}"

        # Fetch news page
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        headlines = soup.find_all(tag, class_=class_name)

        if not headlines:
            return {"error": "No headlines found"}

        print(f"✅ {len(headlines)} Headlines found")

        # Categorized News Storage
        news = {
            "Big Tech & Startups": [],
            "Science & Futuristic Technology": [],
            "Programming, Design & Data Science": []
        }

        # Assign Headlines to Categories
        for i, headline in enumerate(headlines):
            text = headline.text.strip()
            if i < 3:
                news["Big Tech & Startups"].append(text)
            elif i < 6:
                news["Science & Futuristic Technology"].append(text)
            else:
                news["Programming, Design & Data Science"].append(text)

        return news

    except requests.RequestException:
        return {"error": "Network error occurred"}
    except ValueError:
        return {"error": "Invalid data format"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    print(fetch_news())
