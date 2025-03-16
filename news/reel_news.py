import time
import random
import json
import os
import glob
import traceback
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from instagrapi import Client, exceptions
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, TextClip, concatenate_videoclips
import numpy as np
import convert_with_gemini

if os.getenv("GITHUB_ACTIONS") is None:
   load_dotenv()
   USERNAME = os.getenv("NEWS_USERNAME")
   PASSWORD = os.getenv("NEWS_PASSWORD")
else :
    USERNAME = os.environ["NEWS_USERNAME"]
    PASSWORD = os.environ["NEWS_PASSWORD"]
if not USERNAME or not PASSWORD:
    raise ValueError("❌ Missing authentication credentials")

print(f"✅ Using username: {USERNAME}")

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
def create_news_image(category, headline, description, p1, p2, output_path):
    img = Image.open("news/templates/template.jpg")
    draw = ImageDraw.Draw(img)
    font_head = "news/font/font_headline.ttf"
    font_desc = "news/font/font_description.ttf"
    font_para = "news/font/font_paragraph.ttf"

    # Load fonts
    font_headline = ImageFont.truetype(font_head, 40)
    font_description = ImageFont.truetype(font_desc, 30)
    font_paragraph = ImageFont.truetype(font_para, 30)

    max_width = img.width - 200
    x_start = 100
    y_offset = 350

    for line in wrap_text(headline, font_headline, max_width, draw):
        draw.text((x_start, y_offset), line, fill="white", font=font_headline,align="center")
        y_offset += font_headline.size + 10

    y_offset += 20
    for line in wrap_text(description, font_description, max_width, draw):
        draw.text((x_start, y_offset), line, fill="white", font=font_description)
        y_offset += font_description.size + 5

    y_offset += 30
    for line in wrap_text("  " + p1, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="white", font=font_paragraph)
        y_offset += font_paragraph.size + 5

    y_offset += 10
    for line in wrap_text("  " + p2, font_paragraph, max_width, draw):
        draw.text((x_start, y_offset), line, fill="white", font=font_paragraph)
        y_offset += font_paragraph.size + 5

    os.makedirs("news/output", exist_ok=True)
    img.save(output_path)
    print(f"✅ Image saved: {output_path.split('/')[-1]}")

# Convert PNG to JPEG
def convert_to_jpg(png_path):
    img = Image.open(png_path)
    rgb_img = img.convert('RGB')
    jpg_path = png_path.rsplit(".", 1)[0] + ".jpg"
    rgb_img.save(jpg_path, "JPEG", quality=95)
    return jpg_path

# Function to delete images
def delete_files(folder="news/output"):
    for file in glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png")) + glob.glob(os.path.join(folder, "*.mp4")):
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

# Function to generate video from images
def generate_video_from_images(image_path, output_path):
    try:
        final_resolution = (1080, 1920)
        audio_path = "news/templates/background.mp3"
        bg_path = "news/templates/background.jpg"
        video_duration = 20
        fps = 10
        num_frames = video_duration * fps
        zoom_factor = 0.06

        # Load background
        background_clip = ImageClip(bg_path, duration=video_duration).resized(final_resolution)

        # Load main image
        original_clip = ImageClip(image_path).resized(width=1080)

        # Generate zoomed frames
        zoomed_clips = []
        for i in range(num_frames):
            scale = 1 + zoom_factor * (i / num_frames) 
            zoomed_frame = original_clip.resized(new_size=(original_clip.w * scale, original_clip.h * scale))
            zoomed_clips.append(zoomed_frame.with_duration(1 / fps))
        zoomed_video = concatenate_videoclips(zoomed_clips)
        zoomed_video = zoomed_video.with_position(("center", "center"))

        # Add background music
        audio = AudioFileClip(audio_path).with_duration(video_duration)

        # Combine all elements
        final_clip = CompositeVideoClip([background_clip, zoomed_video]).with_audio(audio)

        # Export the video
        final_clip.write_videofile(output_path, codec="libx264", fps=fps, audio_codec="mp3")

        # Cleanup
        final_clip.close()
        print(f"✅ Video saved: {output_path.split('/')[-1]}")

    except Exception as e:
        traceback.print_exc()
        print(f"❌ Error generating video: {e}")

import json

def save_to_file(data: list, filepath: str = "news/captions.py") -> bool:
    """Save data as a Python list inside a .py file."""
    try:
        with open(filepath, "w") as f:
            f.write(f"data = {json.dumps(data, indent=4)}\n")
        return True
    except IOError as e:
        print(f"Failed to save to {filepath}: {e}")
        return False

# Process news & post
def process_and_post():
    delete_files("news/output")
    delete_files("news/output/reels")
    os.makedirs("news/output/reels", exist_ok=True)
    category_order = ["Startups", "Artificial Intelligence", "Entrepreneurs"]
    
    
    # Fetching news and convert to humour
    try:
        convert_with_gemini.generate_and_save()
        print("✅ News fetched and converted to humour.")
    except Exception as e:
        print(f"❌ Error fetching news or converting to humour: {e}")
        return
    
        # Load news data
    with open("news/news.json") as f:
        news_data = json.load(f)
    news_list = news_data["posts"][0]
    # print(news_list)
    captions_list=[]
    # Process news
    for category in category_order:
        filtered_news = []
        filtered_news = [news for news in news_list if news["category"] == category]
        if not filtered_news:
            print(f"⚠️ No news items for {category}. Skipping...")
            continue
        
        for i, news in enumerate(filtered_news):
            img_path = f"news/output/{news['headline'][:30].replace(' ', '_')}.png"
            create_news_image(
                category, 
                news["headline"], 
                news["description"], 
                news["p1"], 
                news["p2"],
                img_path
            )
            img_jpg = convert_to_jpg(img_path)
            generate_video_from_images(img_jpg, f"news/output/reels/{news['headline'][:30].replace(' ', '_')}.mp4")
            

            # Create caption with all 4 paragraphs
            caption = (
                f"{news['headline']}\n\n{news['description']}\n"
                f"  {news['p1']}\n  {news['p2']}\n"
                f"#TechNews #Innovation #Startups #Entrepreneurs #AI\n#Technology #chips #Humour #News"
            )
            captions_list.append(caption)
            save_to_file(captions_list)



if __name__ == "__main__":
    process_and_post()