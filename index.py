import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from markdownify import MarkdownConverter
import re


def download_image(image_url, destination_path):
    """
    Downloads an image from 'image_url' and saves it to 'destination_path'.
    """
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    with open(destination_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


class CustomMarkdownify(MarkdownConverter):
    def convert_pre(self, el, text, convert_as_inline=False):
        language = ""
        pre_class = el.get("class", "")
        if isinstance(pre_class, str):
            pre_class = pre_class.split()
        for class_name in pre_class:
            if class_name.startswith("language-"):
                language = class_name.replace("language-", "")
                break
        return f"```{language}\n{text}\n```\n" if language else f"```\n{text}\n```\n"


def main():
    # Hard-coded links for CS50 notes (example)
    links = [
        "https://cs50.harvard.edu/x/2024/notes/1/",
    ]

    # Base directory where all folders will be stored
    base_output_dir = "TESTEcs50_notes"
    if not os.path.exists(base_output_dir):
        os.mkdir(base_output_dir)

    for lecture_number, url in enumerate(links, start=1):
        print(f"\nProcessing URL: {url}")
        try:
            r = requests.get(url)
            # Force the encoding to UTF-8
            r.encoding = "utf-8"
            r.raise_for_status()
        except Exception as e:
            print(f"Error accessing {url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        main_tag = soup.find("main")
        if not main_tag:
            print("No <main> tag found. Skipping this page...")
            continue

        # Create a dedicated folder for this lecture
        lecture_folder_name = f"{lecture_number:02}-lecture-notes"
        lecture_folder_path = os.path.join(base_output_dir, lecture_folder_name)
        if not os.path.exists(lecture_folder_path):
            os.mkdir(lecture_folder_path)

        # Markdown file path
        md_filename = f"{lecture_folder_name}.md"
        md_filepath = os.path.join(lecture_folder_path, md_filename)

        # 1) Download images and adjust 'src' attributes
        images = main_tag.find_all("img")
        for img in images:
            src = img.get("src")
            if not src:
                continue

            img_url = urljoin(url, src)
            filename = os.path.basename(urlparse(img_url).path)
            if not filename:
                # Fallback if no valid filename can be parsed
                filename = f"image_{len(os.listdir(lecture_folder_path))}.png"

            local_image_path = os.path.join(lecture_folder_path, filename)
            try:
                download_image(img_url, local_image_path)
            except Exception as e:
                print(f"Error downloading {img_url}: {e}")
                continue

            # Adjust the 'src' to the relative path in Markdown
            relative_path = f"{filename}"
            img["src"] = relative_path

        # 2) Convert <main> content to Markdown with custom converter
        custom_converter = CustomMarkdownify()
        md_content = custom_converter.convert(str(main_tag))

        # Save the final Markdown file in UTF-8
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"Saved as: {md_filepath}")


if __name__ == "__main__":
    main()
