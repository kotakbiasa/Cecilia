import asyncio
import os
from bot import logger
from yt_dlp import YoutubeDL

async def youtube_download(url: str, is_video: bool = False, quality: str = None):
    """
    Downloads a YouTube video or audio using yt-dlp.
    Runs the synchronous YoutubeDL library in a separate thread to avoid blocking asyncio.
    """
    loop = asyncio.get_running_loop()

    def run_ytdlp_sync():
        """The actual synchronous download logic."""
        try:
            # Use a template for the output file to let yt-dlp fill in the title and extension.
            # The 'epoch' is used to make the filename unique to avoid collisions.
            output_template = os.path.join('downloads', '%(title)s.%(epoch)s.%(ext)s')

            ydl_opts = {
                'outtmpl': output_template,
                'quiet': True,
                'writethumbnail': True, # Download thumbnail
                'postprocessors': [],
            }

            if is_video:
                # Format for video: select best video with specified height + best audio, merge into mp4
                quality_filter = f'[height<={quality}]' if quality and quality.isdigit() else ''
                ydl_opts['format'] = f'bestvideo[ext=mp4]{quality_filter}+bestaudio[ext=m4a]/best[ext=mp4]/best'
                ydl_opts['merge_output_format'] = 'mp4'
            else: # audio
                # Format for audio: extract audio and convert to mp3
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['extractaudio'] = True
                ydl_opts['audioformat'] = 'mp3'
                # Add a postprocessor to embed thumbnail into the audio file
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
            
            # This postprocessor will convert the thumbnail to jpg
            ydl_opts['postprocessors'].append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                
                # After download, yt-dlp gives us the final file path
                filepath = info_dict.get('requested_downloads')[0]['filepath']
                
                # Find the corresponding thumbnail file
                base_path, _ = os.path.splitext(filepath)
                thumbnail_path = f"{base_path}.jpg"
                if not os.path.exists(thumbnail_path):
                    # Fallback to webp if jpg conversion failed or didn't run
                    webp_thumb = f"{base_path}.webp"
                    thumbnail_path = webp_thumb if os.path.exists(webp_thumb) else None

            return {
                'filepath': filepath,
                'title': info_dict.get('title'),
                'artist': info_dict.get('uploader') or info_dict.get('channel'),
                'duration': info_dict.get('duration'),
                'thumbnail_path': thumbnail_path,
                'width': info_dict.get('width'),
                'height': info_dict.get('height'),
            }
        except Exception as e:
            logger.error(f"yt-dlp download failed for URL {url}: {e}", exc_info=True)
            return None

    try:
        # Run the synchronous function in an executor to avoid blocking the event loop
        result = await loop.run_in_executor(None, run_ytdlp_sync)
        return result
    except Exception as e:
        logger.error(f"Error running yt-dlp in executor: {e}")
        return None
