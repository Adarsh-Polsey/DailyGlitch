import datetime
import time
import random
import json
import os
import glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from instagrapi import Client, exceptions

# Load Instagram login details
parent_dir = os.path.abspath(os.path.join(os.getcwd(), "..")) 
config_path = os.path.join(parent_dir, "config.json")

with open(config_path) as f:
    config = json.load(f)

USERNAME = config["story_username"]
PASSWORD = config["story_password"]

# Function to wrap text within a given width
def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_width = font.getbbox(test_line)[2]  

        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

# Reduce image opacity and apply blur
def process_image(num):
    img_path = f"templates/{num}.jpeg"
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image not found: {img_path}")
    
    image = Image.open(img_path).convert("RGBA")

    # 🌟 Step 1: Crop a little (remove 5% from each side)
    w, h = image.size
    crop_x = int(w * 0.05)
    crop_y = int(h * 0.05)
    image = image.crop((crop_x, crop_y, w - crop_x, h - crop_y))

    # 🌟 Step 2: Reduce Brightness (to 80%)
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(0.5)

    # 🌟 Step 3: Reduce Opacity to 50%
    alpha = image.split()[3].point(lambda p: p * 0.1)  
    image.putalpha(alpha)

    # 🌟 Step 4: Apply Gaussian Blur
    return image.filter(ImageFilter.GaussianBlur(radius=5))

# Convert image to JPEG
def convert_to_jpg(img, output_path):
    jpg_path = output_path.replace(".png", ".jpg")
    img.convert('RGB').save(jpg_path, "JPEG", quality=95)
    return jpg_path

# Create story image
def create_story_image(saga_title, path_title, content, output_path):
    num = datetime.datetime.now().day - 14
    print(f"📅 Selected Saga Number: {num}")

    try:
        img = process_image(num)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return

    draw = ImageDraw.Draw(img)
    font_path = "font/font_writing.ttf"

    try:
        font_content = ImageFont.truetype(font_path, 40)
    except IOError:
        print("❌ Error: Font file not found.")
        return

    max_width = img.width - 200
    x_start, y_offset = 100, 100

    # Draw title and content
    for i, text in enumerate([f"{saga_title} : {path_title}", content]):
        lines = wrap_text(text, font_content, max_width)
        
        if i == 0:
            title_text = lines[0]  # First line (title)
            title_width = font_content.getbbox(title_text)[2] - font_content.getbbox(title_text)[0]
            title_x = (img.width - title_width) // 2  # Center X
            draw.text((title_x, y_offset), title_text, fill="white", font=font_content)
            y_offset += font_content.getbbox(title_text)[3] - font_content.getbbox(title_text)[1] + 20  # Extra line break
        
        else:
            for line in lines:
                draw.text((x_start, y_offset), line, fill="white", font=font_content)
                y_offset += font_content.getbbox(line)[3] - font_content.getbbox(line)[1] + 10  
        os.makedirs("output", exist_ok=True)
        convert_to_jpg(img, output_path)
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"✅ Image saved: {output_path}")

# Delete old images
def delete_images(folder="output"):
    for file in glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png")):
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")

# Retry login with exponential backoff
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

        time.sleep(delay * (2 ** attempt))  

    print("❌ Failed to log in after multiple attempts.")
    return None

# Retry post upload
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

    # cl = login_with_retry()
    # if not cl:
    #     return

    # Load story data
    with open("whispers_of_the_glowing_mural.json") as f:
        story_data = json.load(f)

    num = datetime.datetime.now().day - 14
    print(f"📅 Selected Saga Number: {num}")

    filtered_story = [story for story in story_data if story["Saga"] == num]
    
    if not filtered_story:
        print(f"⚠️ No story found for Saga {num}. Skipping...")
        return

    # Extract story
    story = filtered_story[0]
    img_path = f"output/{num}.jpeg"

    # Create story image
    create_story_image(
        saga_title=story["Title"],  
        path_title=story["Paths"][0]["Title"],  
        content=story["Paths"][0]["Text"],  
        output_path=img_path
    )

    # Construct caption
    caption = (
        f"{story['Paths'][0]['Title']}\n\n{story['Paths'][0]['Text']}\n\n"
        f"#Romane #Magic #Story #Readers #College\n#Ernakulam #Kerala #India #Kochi"
    )

    # post_with_retry(cl, img_path, caption)
    # sleep_time = random.randint(30, 90)
    # print(f"⏳ Waiting {sleep_time} seconds before next post...")
    # time.sleep(sleep_time)

if __name__ == "__main__":
    process_and_post()