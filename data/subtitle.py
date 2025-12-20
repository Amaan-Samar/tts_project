import yt_dlp

def download_subtitles(video_url, output_path='subtitles'):
    """
    Download subtitles from a YouTube video
    
    Args:
        video_url: YouTube video URL
        output_path: Directory to save subtitles (default: 'subtitles')
    """
    
    ydl_opts = {
        'skip_download': True,  # Don't download the video
        'writesubtitles': True,  # Download subtitles
        'writeautomaticsub': True,  # Download auto-generated subs if manual ones aren't available
        'subtitleslangs': ['en'],  # Specify languages (e.g., ['en', 'es', 'fr'])
        'subtitlesformat': 'srt',  # Format: srt, vtt, or best
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Output template
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading subtitles from: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            print(f"✓ Subtitles downloaded successfully!")
            print(f"Video title: {info.get('title', 'Unknown')}")
            
    except Exception as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    video_url = "https://youtu.be/Fshsk8MCAf4?si=Boo7ZIcfqfFdgEzY"
    download_subtitles(video_url)
    
    # To download multiple languages:
    # ydl_opts['subtitleslangs'] = ['en', 'es', 'fr']
    
    # To get all available subtitles:
    # ydl_opts['allsubtitles'] = True
    # Remove or comment out 'subtitleslangs' line when using allsubtitles