import json,subprocess,sys,re
from typing import Dict, Any, Optional
from datetime import datetime

import fetch_news

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Invalid JSON in configuration file '{config_path}'.")
        sys.exit(1)

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

def create_news_prompt(news_data: Dict[str, Any]) -> str:
    """Create the prompt for news transformation."""
    return f"""Given text is today's news. Rewrite it with dark humor, irony, and emotional triggers while keeping the facts intact.

    ### Format:
    - **One news per category.**
    - **Headline:** (Max 20 words) Catchy, darkly humorous, or thought-provoking.
    - **Description:** (80-150 words) Direct, No humour, should convey the news originally as what it is exactly.
    - **4 Points:** (Each 2 lines) Inject irony, satire, or brutal honesty.

    ### Fields:
    {{  
    "category":should be one of [Startups | Artificial Intelligence | Entrepreneurs],
    "headline",
    "description",
    "p1",
    "p2",
    "p3",
    "p4",
    }}

    ### Tone:
    - **Simple words, high impact.**
    - **Dark humor at its deepest.**
    - **Irony so sharp it cuts.**
    - **Emotional triggers that hit where it hurts.**

    ### News:
    {json.dumps(news_data, indent=2)}
    """

def extract_json_from_gemini_response(response: Dict[str, Any]) -> Optional[list]:
    """Extract the JSON content from Gemini API response."""
    news_items = []
    try:
        if "candidates" in response and response["candidates"]:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_content = candidate["content"]["parts"][0]["text"]

            # Extract all JSON blocks between triple backticks
            json_list = re.findall(r'```json\n(.*?)\n```', text_content.strip(), re.DOTALL)
            return [json.loads(item) for item in json_list]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error extracting JSON from response: {e}")
    
    return None

def format_output(news_items: list) -> Dict[str, Any]:
    """Format the news items into the desired output structure."""
    today = datetime.now().strftime("%d %B %Y")
    
    return {
        "date": today,
        "posts": news_items
    }

def save_to_file(data: Dict[str, Any], filepath: str = "news.json") -> bool:
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
        config = load_config()
        api_key = config.get("APIKEY")
        if not api_key:
            print("API key not found in configuration.")
            sys.exit(1)
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    print("Configuration loaded successfully.")
    
    # Fetch news
    try:
        news_data = fetch_news.fetch_news()
        if news_data is None:
            print("Error fetching news")
            sys.exit(1)
        print("News fetched successfully.")
    except Exception as e:
        print(f"News fetching error: {e}")
        sys.exit(1)
    
    # Create prompt and make API call
    prompt = create_news_prompt(news_data)
    # Call the API
    print("Calling Gemini API...")
    response = call_gemini_api(api_key, prompt)
    print("✅ API called successfully."+ response.__str__())
    if response is None:
        print("Failed to get a valid response from the API")
        sys.exit(1)
    
    # Extract and format the JSON content
    news_items = extract_json_from_gemini_response(response)
    if not news_items:
        print("Failed to extract news items from the API response")
        sys.exit(1)
    print("✅ News items extracted successfully. -    "+news_items.__str__())
    # Format output with date
    output_data = format_output(news_items)
    print("✅ News data formatted successfully."+output_data.__str__())
    # Save the result
    if save_to_file(output_data):
        print("News data saved to news.json")
    else:
        print("Failed to save news data")
        sys.exit(1)
    
    print("Process completed successfully")

if __name__ == "__main__":
    generate_and_save()