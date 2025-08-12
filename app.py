from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
from crew import *
from video_processing import *

# 🌐 Page Configuration
st.set_page_config(
    page_title="Story Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("## 📚 Story Generator")
# st.markdown("### Bring history to life with AI-generated video")

st.text_input('Enter the Figure:', key="historical_figure_selector")
historical_figure = st.session_state.get("historical_figure_selector", "")
language = st.selectbox('Language:', ['English', 'Mandarin', 'Hindi', 'German', 'Italian', 'Japanese'], key="language_selector")
cols = st.columns([0.1,0.1,0.8])
with cols[0]:
    st.button("Comic Style")
with cols[1]:
    st.button("Realistic Style")


# 🚀 Generate Button
try:
    if st.button("Generate Story", key="generate_button"):
        if historical_figure and language:
            result = crew.kickoff(inputs={"topic": historical_figure, "language": language})

            if len(result.tasks_output) >= 3:
                subtitle_text = result.tasks_output[1].raw
                
                st.markdown("#### 🎬 Generated Video") 
                # Video processing
                start_path = Path.cwd()
                video_path_raw = result.tasks_output[3].raw.replace('\n', '').replace('```', '').strip().strip('"\'`')
                print(f"video_path_raw :{video_path_raw}") 
                video_path = Path(video_path_raw) 
                print(f"video path{video_path}")

                #combine subtitles with video
                subtitle_text = clean_subtitle_text(subtitle_text)
                print(f"subtitles text has been cleaned!")

                #processing audio path
                audio_file_raw = result.tasks_output[2].raw.replace('\n', '').replace('```', '').strip().strip('"\'`')
                print(f"audio_path_raw :{audio_file_raw}") 
                audio_file_path = Path(audio_file_raw) 
                print(f"audio_file_raw :{audio_file_path}")
                audio_clip = AudioFileClip(audio_file_path)
                duration = audio_clip.duration
                audio_clip.close()
                duration_seconds = duration  # total duration of your audio/video

                #generated subtitles
                vtt_content = generate_vtt(subtitle_text, duration_seconds)
                print(f"subtitles hs been generated!")


                # Save it to a .vtt file
                with open("subtitles.vtt", "w", encoding="utf-8") as f:
                    f.write(vtt_content)

                print("Subtitles saved as 'subtitles.vtt'.")
                subtitles_path=os.path.abspath("subtitles.vtt")
                print(f"path of subtitles:{subtitles_path}")

                #combine audio with video
                video_path_raw=combine_audio_video(video_path,audio_file_path)
                print(f"path of the video with audio combined:{video_path_raw}")
                video_path = Path(video_path_raw)


                relative_path = video_path.relative_to(start_path)
                clean_path = Path(str(relative_path).strip())
                    
                video_file = open(clean_path, "rb")
                video_bytes = video_file.read()
                st.video(video_bytes,subtitles=subtitles_path)
                video_file.close()
                
             
               
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
