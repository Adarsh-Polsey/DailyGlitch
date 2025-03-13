import time
import random
import json
import os
import glob
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client, exceptions

# Load Instagram login details
with open("config.json") as f:
    config = json.load(f)

USERNAME = config["username"]
PASSWORD = config["password"]

# Load news data
with open("news.json") as f:
    news_data = json.load(f)

# Get the news posts list directly from the JSON structure
news_list = news_data["posts"]

# Function to wrap text
def wrap_text(text, font, max_width, draw):
    wrapped_lines = []
    words = text.split()
    line = ""

    for word in words:
        test_line = line + " " + word if line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            line = test_line
        else:
            wrapped_lines.append(line)
            line = word

    wrapped_lines.append(line)  # Add last line
    return wrapped_lines

# Function to generate image with wrapped text
def create_news_image(category, headline, description, p1, p2, p3, p4, output_path):
    img = Image.open("templates/template.jpg")
    draw = ImageDraw.Draw(img)
    font_bold = "font/inter_bold.ttf"
    font_light = "font/inter_light.ttf"
    font_thin = "font/inter_thin.ttf"

    # Load fonts
    font_headline = ImageFont.truetype(font_bold, 40)
    font_description = ImageFont.truetype(font_thin, 30)
    font_paragraph = ImageFont.truetype(font_light, 30)

    max_width = img.width - 200
    x_start = 100
    y_offset = 150

    for line in wrap_text(headline, font_headline, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_headline)
        y_offset += font_headline.size + 10

    y_offset += 20
    for line in wrap_text(description, font_description, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_description)
        y_offset += font_description.size + 5

    y_offset += 30
    for line in wrap_text("> " + p1, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_paragraph)
        y_offset += font_paragraph.size + 5

    y_offset += 10
    for line in wrap_text("> " + p2, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_paragraph)
        y_offset += font_paragraph.size + 5
        
    y_offset += 10
    for line in wrap_text("> " + p3, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_paragraph)
        y_offset += font_paragraph.size + 5
        
    y_offset += 10
    for line in wrap_text("> " + p4, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_paragraph)
        y_offset += font_paragraph.size + 5

    os.makedirs("output", exist_ok=True)
    img.save(output_path)
    print(f"✅ Image saved: {output_path}")

# Convert PNG to JPEG
def convert_to_jpg(png_path):
    img = Image.open(png_path)
    rgb_img = img.convert('RGB')
    jpg_path = png_path.rsplit(".", 1)[0] + ".jpg"
    rgb_img.save(jpg_path, "JPEG", quality=95)
    return jpg_path

# Function to delete images
def delete_images(folder="output"):
    for file in glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png")):
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")

# Function to retry login
def login_with_retry(max_retries=5, delay=5):
    cl = Client()
    for attempt in range(max_retries):
        try:
            cl.login(USERNAME, PASSWORD)
            print("✅ Successfully logged into Instagram!")
            return cl
        except exceptions.BadPassword:
            print("❌ Incorrect password. Check credentials.")
            return None
        except exceptions.LoginRequired:
            print("⚠️ Login required. Retrying...")
        except exceptions.ChallengeRequired:
            print("⚠️ Instagram challenge required. Check your account.")
            return None
        except Exception as e:
            print(f"⚠️ Login attempt {attempt + 1} failed: {e}")

        time.sleep(delay * (2 ** attempt))  # Exponential backoff

    print("❌ Failed to log in after multiple attempts.")
    return None

# Function to retry post upload
def post_with_retry(cl, image_path, caption, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            media = cl.photo_upload(image_path, caption)
            print(f"✅ Successfully posted: {media.model_dump()['pk']}")
            return True
        except exceptions.Throttled:
            print(f"⚠️ Rate limited. Waiting {delay * (2 ** attempt)} seconds...")
        except Exception as e:
            print(f"⚠️ Post attempt {attempt + 1} failed: {e}")

        time.sleep(delay * (2 ** attempt))

    print("❌ Failed to upload after multiple attempts.")
    return False

# Process news & post
def process_and_post():
    delete_images("output")
    category_order = [
      "Startups","Artificial Intelligence","Entrepreneurs"
]
    cl = login_with_retry()
    if not cl:
        return
    
    for category in category_order:
        filtered_news = [news for news in news_list if news["category"] == category]
        
        if not filtered_news:
            print(f"⚠️ No news items for {category}. Skipping...")
            continue
        
        for news in filtered_news:
            img_path = f"output/{news['headline'][:30].replace(' ', '_')}.png"
            create_news_image(
                category, 
                news["headline"], 
                news["description"], 
                news["p1"], 
                news["p2"],
                news["p3"],
                news["p4"],
                img_path
            )
            img_jpg = convert_to_jpg(img_path)

            # Create caption with all 4 paragraphs
            caption = (
                f"{news['headline']}\n\n{news['description']}\n"
                f"> {news['p1']}\n> {news['p2']}\n> {news['p3']}\n> {news['p4']}\n\n"
                f"#TechNews #Innovation #{category.replace(' & ', '').replace(' ', '')}"
            )

            post_with_retry(cl, img_jpg, caption)
            sleep_time = random.randint(60, 180)  # Random delay between 1-3 minutes
            print(f"⏳ Waiting {sleep_time} seconds before next post...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    process_and_post()