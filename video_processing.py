import os
from datetime import timedelta
from moviepy import AudioFileClip
import re

# Converts seconds to VTT timestamp: HH:MM:SS.mmm
def seconds_to_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

# Generates .vtt content from subtitle text and audio/video duration
def generate_vtt(subtitle_text, total_duration):
    # Step 1: Split the subtitle text into chunks (by sentence here)
    chunks = subtitle_text.strip().split('. ')
    if chunks[-1] and not chunks[-1].endswith('.'):
        chunks[-1] += '.'  # add period back if not present

    vtt_lines = ["WEBVTT\n"]
    num_chunks = len(chunks)
    time_per_chunk = total_duration / num_chunks

    for i, chunk in enumerate(chunks):
        start_time = seconds_to_timestamp(i * time_per_chunk)
        end_time = seconds_to_timestamp((i + 1) * time_per_chunk)
        vtt_lines.append(f"{start_time} --> {end_time}\n{chunk.strip()}\n")

    return '\n'.join(vtt_lines)



def clean_subtitle_text(text:str):
    # Replace tabs with a single space
    text = text.replace('\t', ' ')
    
    # Replace newlines with a single space
    text = text.replace('\n', ' ')
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing spaces
    return text.strip()

from moviepy import VideoFileClip, AudioFileClip


def combine_audio_video(video_path, audio_path, output_path="output.mp4"):
    video = VideoFileClip(video_path)  
    audio = AudioFileClip(audio_path)  
      
    # Combine them  
    final_video = video.with_audio(audio)  
      
    # Write the video file  
    final_video.write_videofile(output_path)  
      
    # Return the absolute path of the created file  
    return os.path.abspath(output_path)





