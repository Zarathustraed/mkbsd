import os
import json
import asyncio
import aiohttp
from aiohttp import ClientSession
from urllib.parse import urlparse

# Path to the JSON file
JSON_FILE = 'media-1a-i-p~s.json'

# Create the downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"📁 Created directory: {DOWNLOAD_DIR}")

def sanitize_filename(s):
    # Replace illegal characters in filenames
    return "".join(c for c in s if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

def parse_artist_and_image_name(url):
    # Extract artist and image name from the URL
    path = urlparse(url).path
    parts = path.strip('/').split('/')
    if len(parts) >= 2:
        # The artist's info is in the second last part
        artist_part = parts[-2]
        # The artist name follows 'a~' and may include an underscore and a hash
        artist = artist_part.split('_')[0].replace('a~', '')
        # The image name is the last part
        image_filename = parts[-1]
        image_name_with_ext = os.path.splitext(image_filename)[0]
        # Replace '~' with spaces in the image name
        image_name = image_name_with_ext.replace('~', ' ')
        return artist, image_name
    else:
        return 'unknown_artist', 'unknown_image'

async def download_image(session, url, filepath):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.83 Safari/537.36',
            'Referer': 'https://panelsapp.com/',  # Assuming this is the referer
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Failed to download {url}: HTTP {response.status}")
                return
            content = await response.read()
            with open(filepath, 'wb') as f:
                f.write(content)
            print(f"🖼️ Saved image to {filepath}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

async def main():
    # Load the JSON file
    with open(JSON_FILE, 'r') as f:
        json_data = json.load(f)
    data = json_data.get('data', {})
    if not data:
        print('⛔ JSON does not have a "data" property at its root.')
        return

    conn = aiohttp.TCPConnector(limit_per_host=5)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = []
        for entry in data.values():
            # Determine if the image is HD or SD
            if 'dhd' in entry:
                image_url = entry['dhd']
                resolution = 'HD'
            elif 'dsd' in entry:
                image_url = entry['dsd']
                resolution = 'SD'
            else:
                continue  # Skip if neither 'dhd' nor 'dsd' is present

            artist, image_name = parse_artist_and_image_name(image_url)
            artist = sanitize_filename(artist)
            image_name = sanitize_filename(image_name)
            # Get the file extension
            ext = os.path.splitext(urlparse(image_url).path)[-1] or '.jpg'
            filename = f"{artist} - {image_name} ({resolution}){ext}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            # Schedule the download
            tasks.append(download_image(session, image_url, filepath))
        # Run the download tasks concurrently
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
