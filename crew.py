from crewai import Agent
from dotenv import load_dotenv
from crewai import Task
from crewai import Crew, Process
from crewai.llm import LLM
import os
from crewai_tools import SerperDevTool
import text_to_speech
import warnings
import video_generation_tool
import image_to_video_generator


# Ignore all warnings
warnings.filterwarnings("ignore")

# Use CrewAI's LLM wrapper with proper LiteLLM format
from crewai.llm import LLM

llm = LLM(
    model="gemini/gemini-1.5-flash",  
    api_key="NA",
    temperature=0.5
)
video_tool = image_to_video_generator.AudioStoryVideoTool(internal_llm=llm)
os.environ["SERPER_API_KEY"] = "NA"
search_web_tool = SerperDevTool()


researcher = Agent(
    role="Historical Figure Researcher",
    goal="Research on the topic: {topic} ,fousing on {topic}'s early life ,career ,inspiring lessons and events,incidents of his/her life.",
    verbose=True,
    memory=False,
    backstory=(
        "You are a content researcher for story writing, specializing in biographical narratives designed for listening. "
        "Your expertise are historical research by searching on the web  "
        "You source should be information from reliable biographical sources : Wikipedia, Biography.com and your own memory "
             
    ),
    llm=llm,
    tools=[search_web_tool],
    allow_delegation=False
)

writer = Agent(
    role="Historical Story Writer",
    goal="Create deeply engaging, historically accurate story about {topic}'s early life and career in language:{language} ",
    verbose=True,
    memory=False,
    backstory=(
        "You are a master,multilingual storyteller specializing in biographical narratives . "
        "Your expertise combines historical research with the art of crafting calming, immersive stories. "
        "You understand how to use gentle language, soothing imagery. "
        "You source should be information from reliable biographical sources : Wikipedia, Biography.com, "
        "and historical archives, then transform dry facts into warm, human stories that celebrate "
        "the subject's journey while maintaining a tranquil tone."
        "Do not write anythhing negative about the personality"
             
    ),
    llm=llm,
    allow_delegation=False
)
vedio_generator = Agent(
    role="video Generator",
    goal="Generate the video file on the topic provided ",
    verbose=True,
    memory=False,
    backstory=(
        "You are an experienced video generator. You extract the story text and audio file path "  
        "from previous tasks and use the AudioStoryVideoTool to create synchronized videos."  
    ),
    llm=llm,
    tools=[video_tool],
    allow_delegation=False
)
voice_generator = Agent(
    role="Voice Generator",
    goal="Generate the audio file for the content provided to you by writer agent ",
    verbose=True,
    memory=False,
    backstory=(
        "You are a experienced voice generator who can tell the story in natural voice in language :{language}."
        "You have to return only the audio file path only"      
    ),
    llm=llm,
    tools=[text_to_speech.MyCustomTool()],
    allow_delegation=False
)

search_task = Task(  
    description= "Search for information about {topic} "
        "Prioritize Wikipedia, Biography.com, and other authoritative biographical sources. "  ,
    expected_output="A list of URLs ",  
    agent=researcher,  
    tools=[search_web_tool],  
) 
writer_task = Task(
    description=(
        "Generate a calming, immersive 3 minutes story comprising of paragraphs about the early life and career of {topic} in the language:{language}. "
        "sentences must be SHORT and of EQUAL LENGTH"
        "Keep every sentence of EQUAL LENGTH."
        "Story should not be longer than 3 minutes"
        "Focus on creating a narrative that is both engaging and soothing. "
        # "Structure the story with a gentle flow that gradually becomes more relaxing as it progresses. "
        "Include specific biographical details, formative experiences, and character-building moments. "
        "Ensure the tone is warm, contemplative maintaining historical accuracy. "
        "The story should be approximately 400-500 words to achieve the target duration when narrated."
    ),
    expected_output="A complete story of length enough for 3 minute audio in the language:{language} but it should be romanized(use english alphabets to represent them), and do not give any instruction or sentence other than the story,every sentence in the story should be of equal length ,story should be structured as follows: "
        "Gentle opening that sets the scene "
        "Early childhood and formative experiences "
        "Inspirational Events and incidents from the life of the {topic} "
        "Key career moments and achievements "
        "Reflective conclusion with lasting impact "
        "Ending that ties themes together",
    agent=writer,
)
voice_generation_task = Task(  
    description=  "Generate an audio file from the text provided by the writer agent. "
        "Use a natural-sounding voice, clear pronunciation, and appropriate pacing. "
        "Do not add or change any part of the original text." ,
    expected_output="The path (only) of the generated audio file.",  
    agent=voice_generator,  
    tools=[text_to_speech.MyCustomTool()],  
    context=[writer_task] 
)  
vedio_generation_task = Task(  
    description=   "Generate a video using the AudioStoryVideoTool on the topic: {topic}. "  
        "Extract the story text from the writer task output and the audio file path from the voice generation task output. "  
        "Use the AudioStoryVideoTool with these two inputs: "  
        "1. story_text: The complete story from the writer agent "  
        "2. audio_file_path: The audio file path from the voice generator agent "  
        "Call the tool with both parameters to generate the synchronized video." ,
    expected_output="The path (only) of the generated video file using the tool on the topic provided.",  
    agent=vedio_generator,  
    tools=[image_to_video_generator.AudioStoryVideoTool(internal_llm=llm)],
    context=[writer_task,voice_generation_task] 
) 
crew = Crew(
    agents=[researcher,writer,voice_generator,vedio_generator],
    tasks=[search_task,writer_task,voice_generation_task,vedio_generation_task],
    process=Process.sequential,
)
