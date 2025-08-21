import streamlit as st    
from pathlib import Path    
from crew import *    
from video_processing import *    
import os    
  
# 🌐 Page Configuration    
st.set_page_config(    
    page_title="Story Generator 📚",    
    page_icon="📚",    
    layout="wide",    
    initial_sidebar_state="collapsed"    
)    
  
# Custom CSS for styling    
st.markdown("""    
    <style>    
    .main-header {    
        text-align: center;    
        color: #0066cc;    
        margin-bottom: 1rem;    
        font-size: 2rem;    
        font-weight: 600;    
    }    
    .subheader {    
        text-align: center;    
        color: #ffffff;    
        font-size: 1.1rem;    
        margin-bottom: 1.5rem;    
    }    
    .stButton button {    
        background-color: #0066cc;    
        color: white;    
        border-radius: 5px;    
        padding: 0.5rem 1rem;    
        border: none;    
        transition: all 0.2s ease;    
    }    
    .stButton button:hover {    
        background-color: #0052a3;    
    }    
    .section-header {    
        color: #ffffff;    
        font-size: 1.1rem;    
        margin: 1rem 0;    
        font-weight: 500;    
    }    
    .stSelectbox label, .stTextInput label {    
        color: #ffffff;    
        font-weight: 400;    
    }    
    .content-container {    
        max-width: 1200px;    
        margin: 0 auto;    
    }    
    </style>    
""", unsafe_allow_html=True)    
  
# Header Section    
st.markdown('<h1 class="main-header">📚 Story Generator</h1>', unsafe_allow_html=True)    
st.markdown('<p class="subheader">Bring figures to life with AI-generated video storytelling</p>', unsafe_allow_html=True)    
  
# Main Content Container    
with st.container():    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)    
  
    left_spacer, main_content, right_spacer = st.columns([1, 2, 1])    
  
    with main_content:    
        # Text Input    
        historical_figure = st.text_input(    
            'Enter the Figure:',    
            placeholder="e.g., Leonardo da Vinci, Marie Curie",    
            key="historical_figure_selector"    
        )    
  
        # Language Selection    
        language = st.selectbox(    
            'Select Narration Language',    
            ['English', 'Mandarin', 'Hindi', 'German', 'Italian', 'Japanese'],    
            key="language_selector"    
        )    
  
        # Style Selection    
        st.markdown('<p class="section-header">Choose Visualization Style</p>', unsafe_allow_html=True)    
        style_cols = st.columns(2)    
        with style_cols[0]:    
            st.button("🎨 Comic Style", use_container_width=True)    
        with style_cols[1]:    
            st.button("🎭 Realistic Style", use_container_width=True)    
  
        # 🚀 Generate Button    
        try:    
            if st.button("✨ Generate Story", type="primary", use_container_width=True):    
                if historical_figure and language:    
                    with st.spinner("Generating video... Please wait"):    
                        result = crew.kickoff(inputs={"topic": historical_figure, "language": language})    
  
                        if len(result.tasks_output) >= 3:    
                            subtitle_text = result.tasks_output[1].raw    
  
                            st.markdown("#### 🎬 Generated Video")     
                            # Video processing    
                            start_path = Path.cwd()    
                            video_path_raw = result.tasks_output[3].raw.replace('\n', '').replace('```', '').strip().strip('"\'`')    
                            video_path = Path(video_path_raw)     
  
                            # Clean subtitles    
                            subtitle_text = clean_subtitle_text(subtitle_text)    
  
                            # Process audio path    
                            audio_file_raw = result.tasks_output[2].raw.replace('\n', '').replace('```', '').strip().strip('"\'`')    
                            audio_file_path = Path(audio_file_raw)     
                            audio_clip = AudioFileClip(audio_file_path)    
                            duration = audio_clip.duration    
                            audio_clip.close()    
  
                            # Generate subtitles file    
                            vtt_content = generate_vtt(subtitle_text, duration)    
                            with open("subtitles.vtt", "w", encoding="utf-8") as f:    
                                f.write(vtt_content)    
                            subtitles_path = os.path.abspath("subtitles.vtt")    
  
                            # Combine audio + video    
                            video_path_raw = combine_audio_video(video_path, audio_file_path)    
                            video_path = Path(video_path_raw)    
  
                            relative_path = video_path.relative_to(start_path)    
                            clean_path = Path(str(relative_path).strip())    
  
                            video_file = open(clean_path, "rb")    
                            video_bytes = video_file.read()    
                              
                            # Store video data in session state for persistence  
                            st.session_state.video_bytes = video_bytes  
                            st.session_state.video_filename = f"{historical_figure.replace(' ', '_')}_story.mp4"  
                              
                            st.video(video_bytes, subtitles=subtitles_path)    
                            video_file.close()    
  
            # Display download button if video exists in session state  
            if "video_bytes" in st.session_state:  
                st.download_button(  
                    label="📥 Download Video",  
                    data=st.session_state.video_bytes,  
                    file_name=st.session_state.video_filename,  
                    mime="video/mp4",  
                    on_click="ignore",  
                    type="secondary",  
                    use_container_width=True  
                )  
  
        except Exception as e:    
            st.error(f"An error occurred: {str(e)}")


