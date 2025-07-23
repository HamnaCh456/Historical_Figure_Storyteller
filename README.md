# 🌐 Historical Story Video Generator

**Bring historical figures to life through calming AI-generated storytelling videos with narration and subtitles.**

---

## 🎓 What It Does

This project builds an **AI-powered storytelling pipeline** that:

1. **Searches** for biographical information on historical figures.
2. **Generates** a calming and informative story.
3. **Converts** the story into natural speech audio.
4. **Creates** images based on story sections.
5. **Combines** audio and images into a synchronized video.
6. **Generates subtitles** and overlays them on the final video.

---

## ⚙️ How It Works

The pipeline is orchestrated using [CrewAI](https://docs.crewai.com/) and consists of **multi-agent collaboration** with these agents:

### Agents & Roles

* **🥝 Researcher Agent**: Searches biographical content using SerperDev (Google-like search).
* **🌍 Writer Agent**: Crafts a short, warm, equal-length-sentence story (in a selected language).
* **🎧 Voice Generator Agent**: Uses [Deepgram](https://deepgram.com/) API (via custom tool) to generate narration.
* **🎥 Video Generator Agent**: Uses `moviepy` to:

  * Generate synchronized video from AI-generated images and audio
  * Overlay subtitle tracks

### Key Technologies

| Component          | Library/API                      |
| ------------------ | -------------------------------- |
| Search             | SerperDevTool                    |
| Language Model     | Gemini 1.5 via LiteLLM wrapper   |
| Text-to-Speech     | Deepgram API (custom tool)       |
| Image Generation   | Gemini-based LLM prompt-to-image |
| Video Editing      | moviepy                          |                   |
| Crew Orchestration | CrewAI                           |

---

## 🔧 Usage Instructions

### 1. Clone the repo

```bash
git clone https://github.com/HamnaCh456/StoryVideo_Generator.git


### 2. Setup environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Set API Keys

Create a `.env` file in the root directory and add:

```
GEMINI_API_KEY=your_gemini_key
SERPER_API_KEY=your_serper_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### 4. Run the App

```bash
streamlit run main.py
```

---

## 📅 Workflow Summary

1. User enters a historical figure and target language
2. Researcher agent fetches relevant links
3. Writer agent generates a story
4. TTS tool produces an audio file
5. Video agent generates:

   * Image for each section
   * Synchronizes audio & visuals
   * Generates subtitles
6. Final video is displayed with subtitles in Streamlit UI

---

## 🎉 Example Output

* Input: *"Leonardo da Vinci" in Italian*
* Output: A 3-minute storytelling video in Romanized Italian with soft music, visuals, and subtitles

---

## 🌟 Features

* 🌐 Multilingual Support
* 💬 Subtitles (VTT format)
* 🎤 Natural narration
* 📄 Modular agent-based design

---

## 📖 Code Structure

```
|-- main.py                        # Streamlit UI
|-- crew.py                        # Multi-agent pipeline
|-- text_to_speech.py              # Deepgram-powered TTS tool
|-- video_processing.py            # Subtitle + audio-video combining
|-- audio_story_video_tool.py      # Image + video synthesis from story

