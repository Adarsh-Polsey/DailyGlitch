import os
import json,subprocess,sys,re
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
import fetch_news
import news_list

if os.getenv("GITHUB_ACTIONS") is None:
   load_dotenv()
   API_KEY=os.getenv("APIKEY")
else :
    API_KEY = os.environ["APIKEY"]
if not API_KEY:
    raise ValueError("❌ Missing API key")

def call_gemini_api(api_key: str, prompt: str, model: str = "gemini-2.0-flash") -> Optional[Dict[str, Any]]:
    """Call the Gemini API with the given prompt."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        result = subprocess.run(
            ["curl", "-X", "POST", "-H", "Content-Type: application/json",
             "-d", json.dumps(data), url],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"API call failed: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse API response: {e}")
        return None

def create_news_prompt(news_data: list) -> str:
    """Create the prompt for news transformation."""
    return f"""Given text is today's news. Rewrite it with keywords, triggers, no bullshit buzzwords, sticking to raw facts. Use simple, gut-punching words for max damage.

    ### Format:
    - **One news per category.**
    - **Headline:** (Max 20 words) Negativity hooks harder than hope—go dark, catchy, twisted, or mind-fucking.
    - **Description:** (50 words) Straight, no laughs, just the cold, hard news as it is—unfiltered.
    - **2 Extended Points:** (Each 50 words) Lace in dark humor, savage irony, brutal truth—show the ugly fallout, no distortion.

    ### Fields:
    {{  
    "category": pick one [Startups | Artificial Intelligence | Entrepreneurs],
    "headline",
    "description",
    "p1",
    "p2",
    }}

    ### Tone:
    - **Simple words, big punches.**
    - **Dark humor that stabs deep.**
    - **Irony sharp enough to slit throats.**
    - **Triggers that rip open fear, greed, or despair.**

    ### News:
    {news_data}
    """

def extract_json_from_gemini_response(response: Dict[str, Any]) -> Optional[list[dict]]:
    """Extract the JSON content from Gemini API response."""
    try:
        # If the response is a list, take the first element
        if isinstance(response, list):
            response = response[0] if response else {}

        if "candidates" in response and response["candidates"]:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_content = candidate["content"]["parts"][0].get("text", "")

                # Extract all JSON blocks between triple backticks
                json_list = re.findall(r'\{.*?\}', text_content, re.DOTALL)

                parsed_json = []
                for item in json_list:
                    try:
                        # Remove trailing commas before parsing
                        item = re.sub(r',\s*([\]}])', r'\1', item)  
                        parsed_json.append(json.loads(item))
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}\nProblematic Entry:\n{item}\n")

                print("Parsed JSON:", parsed_json)
                return parsed_json if parsed_json else []
    except Exception as e:
        traceback.print_exc()
        print(f"Error extracting JSON from response: {e}")
    
    return None

def format_output(news_items: list) -> Dict[str, Any]:
    """Format the news items into the desired output structure."""
    today = datetime.now().strftime("%d %B %Y")
    
    return {
        "date": today,
        "posts": news_items
    }

def save_to_file(data: Dict[str, Any], filepath: str = "news/news.json") -> bool:
    """Save data to a JSON file."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        print(f"Failed to save to {filepath}: {e}")
        return False

def generate_and_save():
    # Load configuration
    try:
        api_key = API_KEY
        if not api_key:
            print("API key not found in configuration.")
            sys.exit(1)
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    print("Configuration loaded successfully.")
    
    # Fetch news
    try:
        news_data=news_list.news_list
        print("🟡 Fetching news... ")
        # news_data = fetch_news.fetch_news()
        if news_data is None or news_data == {'error': 'No headlines found'}:
            print("❌ No news data found")
            sys.exit(1)
    except Exception as e:
        print(f"❌ News fetching error: {e}")
        sys.exit(1)
    
    # Create prompt and make API call
    prompt = create_news_prompt(news_data)
    # Call the API
    print("🟡 Calling Gemini API...")
    response = call_gemini_api(api_key, prompt)
    if response is None:
        print("❌ Failed to get a valid response from the API")
        sys.exit(1)
    
    # Extract and format the JSON content
    news_items = extract_json_from_gemini_response(response)
    if not news_items:
        print("❌ Failed to extract news items from the API response")
        sys.exit(1)
    print("✅ News items extracted successfully.")
    # Format output with date
    output_data = format_output(news_items)
    print("✅ News data formatted successfully.")
    # Save the result
    if save_to_file(output_data):
        print("✅ News data saved to news/news.json")
    else:
        print("❌ Failed to save news data")
        sys.exit(1)
    
    print("✅ Process completed successfully")

if __name__ == "__main__":
    generate_and_save()