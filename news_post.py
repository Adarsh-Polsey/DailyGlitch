from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
import json
import os
import textwrap
import glob

# Load Instagram login details
with open("config.json") as f:
    config = json.load(f)

USERNAME = config["username"]
PASSWORD = config["password"]

# Category-to-image mapping
# CATEGORY_IMAGES = {
#     "AI & Digital Innovation": "templates/ai_template.jpg",
#     "Hardware & Emerging Technologies": "templates/hardware_template.jpg",
#     "BioTech & Human-Centric Tech": "templates/biotech_template.jpg",
# }

# Load news data
with open("news.json") as f:
    news_data = json.load(f)

DATE_KEY = list(news_data.keys())[0]  # Use today's date
news_dict = news_data[DATE_KEY]  # This is a dictionary, not a list

# Convert news_dict to a list
news_list = []
for category, items in news_dict.items():
    for news in items:
        news["category"] = category  # Add category field to each news item
        news_list.append(news)


# Function to wrap text
def wrap_text(text, font, max_width, draw):
    wrapped_lines = []
    words = text.split()
    line = ""

    for word in words:
        test_line = line + " " + word if line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)  # Bounding box for text
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            line = test_line
        else:
            wrapped_lines.append(line)
            line = word

    wrapped_lines.append(line)  # Add last line
    return wrapped_lines

# Function to generate image with wrapped text
# Function to generate image with wrapped text
def create_news_image(category, headline, description, p1, p2, output_path):
    # if category not in CATEGORY_IMAGES:
    #     raise ValueError(f"Invalid category: {category}")

    img = Image.open("templates/template.jpg")
    draw = ImageDraw.Draw(img)
    font_bold = "font/inter_bold.ttf"
    font_light = "font/inter_light.ttf"
    font_thin = "font/inter_thin.ttf"

    # Load fonts
    font_headline = ImageFont.truetype(font_bold, 40)
    font_description = ImageFont.truetype(font_thin, 30)
    font_p1 = ImageFont.truetype(font_light, 30)
    font_p2 = ImageFont.truetype(font_light, 30)

    max_width = img.width - 200  # Set max text width
    x_start = 100  # Fixed X position

    y_offset = 150  # Initial Y position for headline

    # ✅ Wrap and draw headline
    for line in wrap_text(headline, font_headline, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_headline)
        y_offset += font_headline.size + 10  # Move to next line

    y_offset += 20  # Extra gap after headline

    # ✅ Wrap and draw description
    for line in wrap_text(description, font_description, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_description)
        y_offset += font_description.size + 5  # Move to next line

    y_offset += 30  # Extra gap after description

    # ✅ Wrap and draw p1
    for line in wrap_text("> " + p1, font_p1, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_p1)
        y_offset += font_p1.size + 5  # Move to next line

    y_offset += 10  # Small gap after p1

    # ✅ Wrap and draw p2
    for line in wrap_text("> " + p2, font_p2, max_width, draw):
        draw.text((x_start, y_offset), line, fill="black", font=font_p2)
        y_offset += font_p2.size + 5  # Move to next line

    os.makedirs("output", exist_ok=True)
    img.save(output_path)

    print(f"✅ Image saved: {output_path}")
# Function to convert PNG to properly formatted JPEG
def convert_to_jpg(png_path):
    img = Image.open(png_path)
    rgb_img = img.convert('RGB')  # Ensure RGB mode
    jpg_path = png_path.rsplit(".", 1)[0] + ".jpg"
    rgb_img.save(jpg_path, "JPEG", quality=95)  # Ensure high quality
    return jpg_path

# Function to post carousel to Instagram
def post_to_instagram(image_paths, caption):
    cl = Client()
    cl.login(USERNAME, PASSWORD)
    print(f"📸 Uploading images: {image_paths}")

    try:
        media = cl.album_upload(image_paths, caption)
        print(f"✅ Successfully posted carousel: {media.model_dump()['pk']}")

    except Exception as e:
        print(f"❌ Failed to post: {e}")

def delete_images(folder="output"):
    # Remove all JPG and PNG files
    for file in glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png")):
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")
# Process news & post
def process_and_post():
    delete_images("output")
    category_order = ["Hardware & Emerging Technologies", "AI & Digital Innovation", "BioTech & Human-Centric Tech"]
    
    for category in category_order:
        filtered_news = [news for news in news_list if news["category"] == category]
        
        if len(filtered_news) < 2:
            print(f"⚠️ Not enough news items for {category}. Skipping...")
            continue
        
        img1_path = f"output/{category.replace(' ', '_')}_1.png"
        img2_path = f"output/{category.replace(' ', '_')}_2.png"
        
        # Generate PNG images
        create_news_image(category, filtered_news[0]["headline"], filtered_news[0]["description"], 
                          filtered_news[0]["p1"], filtered_news[0]["p2"], img1_path)
        create_news_image(category, filtered_news[1]["headline"], filtered_news[1]["description"], 
                          filtered_news[1]["p1"], filtered_news[1]["p2"], img2_path)
        
        # Convert PNG to JPEG
        img1_jpg = convert_to_jpg(img1_path)
        img2_jpg = convert_to_jpg(img2_path)

        caption = (
            f"{filtered_news[0]['headline']}\n\n{filtered_news[0]['description']}\n"
            f"{filtered_news[0]['p1']}\n{filtered_news[0]['p2']}\n\n"
            "---\n\n"
            f"{filtered_news[1]['headline']}\n\n{filtered_news[1]['description']}\n"
            f"{filtered_news[1]['p1']}\n{filtered_news[1]['p2']}\n\n"
            "#TechNews #Innovation"
        )
        
        # ✅ Pass JPGs instead of PNGs
        # post_to_instagram([img1_jpg, img2_jpg], caption)

if __name__ == "__main__":
    process_and_post()