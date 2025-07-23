import os
import io
import json
import tempfile
import pprint
from typing import Type, List, Any, Optional
from pydantic import BaseModel, Field
from PIL import Image
from moviepy import ImageSequenceClip, AudioFileClip
from crewai.tools import BaseTool
from crewai.llm import LLM
from google import genai
from google.genai import types

GEMINI_API_KEY = "NA"  

# Initialize Gemini client for image generation
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini client: {e}. Please ensure GEMINI_API_KEY is valid.")
    gemini_client = None


class AudioStoryVideoInput(BaseModel):
    """Input schema for AudioStoryVideoTool."""
    audio_file_path: str = Field(..., description="Path to the audio file to get duration from")
    story_text: str = Field(..., description="The complete story text to be divided into 10 sections")


class AudioStoryVideoTool(BaseTool):
    name: str = "Audio_Story_Video_Generator"
    description: str = "Analyzes audio duration, divides story into 36 sections, generates images for each section, and creates a synchronized video"
    args_schema: Type[BaseModel] = AudioStoryVideoInput
    
    # Define internal_llm as a proper field
    internal_llm: Optional[Any] = Field(default=None, description="Internal LLM instance for story processing")
    
    def __init__(self, internal_llm: Any = None, **kwargs):
        # Pass internal_llm as a keyword argument to super().__init__()
        super().__init__(internal_llm=internal_llm, **kwargs)
        
        if self.internal_llm is None:
            print("Warning: 'internal_llm' not provided. Please provide an LLM instance.")

    def _get_audio_duration(self, audio_file_path: str) -> float:
        """
        Calculate the duration of an audio file in seconds.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            float: Duration in seconds
        """
        try:
            audio_clip = AudioFileClip(audio_file_path)
            duration = audio_clip.duration
            audio_clip.close()
            print(f"Audio duration: {duration:.2f} seconds")
            return duration
        except Exception as e:
            print(f"Error reading audio file: {e}")
            raise

    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Extracts JSON from LLM response, handling various formatting issues.
        """
        response_text = response_text.strip()
        
        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:].strip()
        
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # Find JSON array boundaries
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON array found in response")
        
        json_str = response_text[start_idx:end_idx + 1]
        return json_str

    def _generate_story_sections_and_prompts(self, story_text: str) -> tuple[List[str], List[str]]:
        """
        Uses LLM to divide story into 36 sections and generate image prompts.
        
        Args:
            story_text: The complete story text
            
        Returns:
            tuple: (image_prompts, story_sections)
        """
        if not self.internal_llm:
            raise ValueError("Internal LLM not provided. Cannot generate prompts.")
        
        print("Generating 36 story sections and image prompts...")
        
        prompt_instruction = f"""
        You are an expert visual storyteller. Your task is to:
        1. Divide the following story into EXACTLY 36 logical, sequential sections
        2. Create a image generation prompt for each section
        
        Requirements:
        - Each image prompt should be vivid, and suitable for AI image generation
        - Read the whole story once this will help you to maintain consistency
        - Maintain visual consistency across all prompts (character appearance, style, etc.)
        - Keep in mind that the AI image generator do not know the previous prompt which you have written, so in order to maintain consistency you have to write the prompt yourself in a way that maintain consistency.
        - For instance,If you are defining a character in a story,define it the same everytime in prompt.
        
        Return your response as a JSON array with exactly 36 objects, each containing:
        - "image_prompt": detailed prompt for image generation
        - "story_section": the corresponding part of the story
        
        Do not include any text before or after the JSON array.
        
        Example format:
        [
            {{
                "image_prompt": "A young person sitting at a desk with books, looking determined.",
                "story_section": "The first part of the story text here..."
            }},
            {{
                "image_prompt": "The same person walking through a city street, confident expression.",
                "story_section": "The second part of the story text here..."
            }}
        ]
        The example of the good quality prompt are:
        1."A group of six workers, dressed in dark, worn clothing and carrying tools and backpacks, are seen slowly walking on a desolate, fog-covered beach. The massive, rusted body of a huge submarine looms behind them, casting an imposing silhouette against the thick, sepia-toned fog. The muted light and desaturated tones heighten the eerie, apocalyptic atmosphere. The beach is muddy and strewn with debris, contributing to the scene’s feeling of decay and abandonment. The video is captured using a digital full-frame camera with a wide-angle lens, shot on digital film, under natural, fog-diffused lighting. The fog thickens as the workers navigate around the submarine , further enveloping the massive structure. The workers pause, examining the wreckage more closely, their silhouettes blurred by the mist. The camera pans out, revealing more of the fog-covered coastline and emphasizing the immense size of the shipwreck compared to the diminutive human figures."
        2."rockefeller center is overrun by golden retrievers! everywhere you look, there are golden retrievers. it’s a nighttime winter wonderland in nyc, and there is a grand christmas tree visible. taxis and other nyc elements are visible in the background"
       
        
        Story to process:
        {story_text}
        """
        
        
        # Generate response using CrewAI LLM call method
        response = self.internal_llm.call(prompt_instruction)
        
        print(f"LLM response received (first 200 chars): {response}...")
        
        # Extract and parse JSON
        json_string = self._extract_json_from_response(response)
        parsed_data = json.loads(json_string)
        
        # Validate structure
        # if not isinstance(parsed_data, list) or len(parsed_data) != 36:
        #     raise ValueError(f"Expected 36 sections, got {len(parsed_data)}")
        
        # Extract prompts and sections
        image_prompts = []
        story_sections = []
        
        for i, item in enumerate(parsed_data):
            if not isinstance(item, dict) or 'image_prompt' not in item or 'story_section' not in item:
                raise ValueError(f"Invalid structure in item {i}")
            
            image_prompts.append(item['image_prompt'])
            story_sections.append(item['story_section'])
        
        print(f"Successfully generated {len(image_prompts)} image prompts")
        return image_prompts, story_sections
            
        

    def _generate_image_from_prompt(self, prompt: str, scene_number: int) -> str:
        """
        Generate an image from a text prompt using Gemini.
        
        Args:
            prompt: Text prompt for image generation
            scene_number: Scene number for naming
            
        Returns:
            str: Path to the generated image file
        """
        if not gemini_client:
            raise ValueError("Gemini client not initialized")
        
        
        print(f"Generating image for scene {scene_number}: {prompt[:50]}...")
        
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT']
            )
        )
        
        # Extract image from response
        image_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_part = part
                break
            
        if not image_part:
            raise ValueError("No image generated in response")
        
        # Process and save image
        img_data = image_part.inline_data.data
        image = Image.open(io.BytesIO(img_data))
        
        # Convert image format if needed
        if image.mode in ('P', 'PA'):
            image = image.convert('RGB')
        elif image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # Resize to standard video resolution
        image = image.resize((1280, 720))
            
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_scene_{scene_number}.png')
        image.save(temp_file.name, 'PNG')
        temp_file.close()
        
        print(f"Image for scene {scene_number} saved to: {temp_file.name}")
        return temp_file.name
            
        

    def _create_synchronized_video(self, image_paths: List[str], total_duration: float) -> str:
        """
        Create a video from images synchronized with audio duration (video only, no audio).
        
        Args:
            image_paths: List of paths to image files
            total_duration: Total duration in seconds
            
        Returns:
            str: Path to the generated video file
        """
        
        # Calculate duration per image
        duration_per_image = total_duration / len(image_paths)
        print(f"Each image will be displayed for {duration_per_image:.2f} seconds")
        
        # Create output directory
        output_dir = "generated_story_videos"
        os.makedirs(output_dir, exist_ok=True)
        video_filename = os.path.join(output_dir, "synchronized_story_video.mp4")
        
        # Create image durations list
        durations = [duration_per_image] * len(image_paths)
        
        # Create video clip from images
        print(f"Creating video from {len(image_paths)} images...")
        video_clip = ImageSequenceClip(image_paths, durations=durations)
        
        # Set the duration to match the total duration
        #video_clip = video_clip.set_duration(total_duration)
        
        # Write video file (video only, no audio)
        video_clip.write_videofile(video_filename, fps=24, codec="libx264")
        
        # Clean up clip
        video_clip.close()
        
        print(f"Video created successfully: {os.path.abspath(video_filename)}")
        return os.path.abspath(video_filename)
        
        

    def _run(self, audio_file_path: str, story_text: str) -> str:
        """
        Main execution method that orchestrates the entire process.
        
        Args:
            audio_file_path: Path to the audio file
            story_text: Complete story text
            
        Returns:
            str: Path to the generated video file
        """
        temp_image_files = []
        
        try:
            # Step 1: Get audio duration
            print("Step 1: Analyzing audio duration...")
            audio_duration = self._get_audio_duration(audio_file_path)
            
            # Step 2: Generate story sections and image prompts
            print("Step 2: Generating story sections and image prompts...")
            image_prompts, story_sections = self._generate_story_sections_and_prompts(story_text)
            
            # Step 3: Generate images for each section
            print("Step 3: Generating images for each section...")
            for i, prompt in enumerate(image_prompts, 1):
                try:
                    image_path = self._generate_image_from_prompt(prompt, i)
                    temp_image_files.append(image_path)
                except Exception as e:
                    print(f"Failed to generate image for section {i}: {e}")
                    continue
            
            if not temp_image_files:
                return "Error: No images were successfully generated"
            
            if len(temp_image_files) != 36:
                print(f"Warning: Only {len(temp_image_files)} images generated instead of 36")
            
            # Step 4: Create synchronized video (video only)
            print("Step 4: Creating synchronized video...")
            video_path = self._create_synchronized_video(temp_image_files, audio_duration)
            
            return video_path
            
        except Exception as e:
            error_msg = f"Error in video generation process: {str(e)}"
            print(error_msg)
            return error_msg
            
        finally:
            # Clean up temporary image files
            for image_file in temp_image_files:
                try:
                    os.unlink(image_file)
                    print(f"Cleaned up temporary file: {image_file}")
                except OSError as e:
                    print(f"Error cleaning up file {image_file}: {e}")
