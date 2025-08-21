from deepgram import DeepgramClient, SpeakOptions  
from crewai.tools import BaseTool  
from pydantic import BaseModel, Field  
from typing import Type, List  
import time  
import os  
import re  
from dotenv import load_dotenv

load_dotenv()

class MyToolInput(BaseModel):  
    """Input schema for the speech generator"""  
    text: str = Field(..., description="The text to convert to speech (will be chunked if too long)")  
  
class MyCustomTool(BaseTool):  
    name: str = "text_to_speech_generator"  
    description: str = "Converts text to speech and combines into single audio file, then returns the path of the audio file"  
    args_schema: Type[BaseModel] = MyToolInput  
  
    def _run(self, text: str) -> str:  
        print(f"[DEBUG] Starting text-to-speech conversion for text of length: {len(text)}")  
          
        # Create directory for audio files  
        os.makedirs("audio_files", exist_ok=True)  
        print("[DEBUG] Created/verified audio_files directory")  
          
        # Clean text before processing  
        cleaned_text = self._clean_text_for_tts(text)  
        print(f"[DEBUG] Text cleaned, new length: {len(cleaned_text)}")  
          
        # Split text into sentence-based chunks with smaller max length  
        chunks = self._split_text_by_sentences(cleaned_text, max_length=1000)  
        print(f"[DEBUG] Text split into {len(chunks)} chunks")  
          
        # Initialize Deepgram client  
        deepgram = DeepgramClient(api_key="NA")  
          
        # Generate audio for each chunk  
        audio_files = []  
        for i, chunk in enumerate(chunks):  
            print(f"[DEBUG] Processing chunk {i+1}/{len(chunks)} (length: {len(chunk)})")  
            filename = self._generate_audio_chunk(deepgram, chunk, i)  
            if filename:  
                audio_files.append(filename)  
                print(f"[DEBUG] Successfully generated audio: {filename}")  
            else:  
                print(f"[DEBUG] Failed to generate audio for chunk {i}")  
          
        print(f"[DEBUG] Generated {len(audio_files)} audio files out of {len(chunks)} chunks")  
          
        # Combine all audio files  
        if audio_files:  
            print("[DEBUG] Starting audio combination process")  
            combined_file = self._combine_audio_files(audio_files)  
            print(f"[DEBUG] Audio combination completed: {combined_file}")  
            return os.path.abspath(combined_file)  
        else:  
            print("[DEBUG] No audio files were generated - returning error")  
            return "Failed to generate audio files"  
  
    def _clean_text_for_tts(self, text: str) -> str:  
        """Remove markdown and other formatting that might cause TTS issues"""  
        print("[DEBUG] Cleaning text for TTS")  
          
        # Remove markdown bold/italic  
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold  
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* -> italic  
          
        # Remove extra whitespace and newlines  
        text = re.sub(r'\s+', ' ', text).strip()  
          
        print("[DEBUG] Text cleaning completed")  
        return text  
  
    def _split_text_by_sentences(self, text: str, max_length: int = 1000) -> List[str]:  
        """Split text into chunks at sentence boundaries"""  
        print(f"[DEBUG] Starting text splitting with max_length: {max_length}")  
          
        # Split text into sentences using regex  
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())  
        print(f"[DEBUG] Found {len(sentences)} sentences in the text")  
          
        chunks = []  
        current_chunk = ""  
          
        for i, sentence in enumerate(sentences):  
            print(f"[DEBUG] Processing sentence {i+1}: '{sentence[:50]}...' (length: {len(sentence)})")  
              
            # Check if adding this sentence would exceed max_length  
            if len(current_chunk) + len(sentence) + 1 <= max_length:  
                current_chunk += sentence + " "  
                print(f"[DEBUG] Added sentence to current chunk (chunk length now: {len(current_chunk)})")  
            else:  
                # Save current chunk and start new one  
                if current_chunk.strip():  
                    chunks.append(current_chunk.strip())  
                    print(f"[DEBUG] Saved chunk {len(chunks)} with length: {len(current_chunk.strip())}")  
                current_chunk = sentence + " "  
                print(f"[DEBUG] Started new chunk with this sentence")  
          
        # Add the last chunk if it has content  
        if current_chunk.strip():  
            chunks.append(current_chunk.strip())  
            print(f"[DEBUG] Added final chunk {len(chunks)} with length: {len(current_chunk.strip())}")  
          
        print(f"[DEBUG] Text splitting completed. Created {len(chunks)} total chunks")  
        return chunks  
  
    def _generate_audio_chunk(self, deepgram_client, text: str, chunk_number: int) -> str:  
        """Generate audio for a single text chunk using Deepgram SDK"""  
        print(f"[DEBUG] Making API request for chunk {chunk_number}")  
        print(f"[DEBUG] Text preview: '{text[:100]}...'")  
          
        try:  
            # Configure TTS options  
            options = SpeakOptions(  
                model="aura-2-thalia-en",  
                encoding="linear16",  
                container="wav"  
            )  
              
            # Generate speech using Deepgram SDK  
            response = deepgram_client.speak.rest.v("1").stream_memory(  
                {"text": text},   
                options  
            )  
              
            print(f"[DEBUG] API request successful")  
              
            filename = f"audio_files/chunk_{chunk_number}_{int(time.time())}.wav"  
            print(f"[DEBUG] Saving audio to: {filename}")  
              
            with open(filename, 'wb') as f:  
                f.write(response.stream_memory.getbuffer())  
              
            file_size = os.path.getsize(filename)  
            print(f"[DEBUG] Audio file saved successfully. Size: {file_size} bytes")  
            return filename  
              
        except Exception as e:  
            print(f"[DEBUG] Exception during API request: {str(e)}")  
            return None  
  
    def _combine_audio_files(self, audio_files: List[str]) -> str:  
        """Combine multiple audio files"""  
        combined_filename = f"audio_files/complete_story_{int(time.time())}.wav"  
        print(f"[DEBUG] Starting audio combination. Output file: {combined_filename}")  
        print(f"[DEBUG] Files to combine: {audio_files}")  
          
        try:  
            # Try using pydub for better quality  
            from pydub import AudioSegment  
            print("[DEBUG] Using pydub for audio combination")  
            combined = AudioSegment.empty()  
              
            for i, audio_file in enumerate(audio_files):  
                # Use full path to ensure file is found  
                full_path = os.path.abspath(audio_file)  
                print(f"[DEBUG] Processing file {i+1}/{len(audio_files)}: {full_path}")  
                  
                if os.path.exists(full_path):  
                    print(f"[DEBUG] File exists, loading audio segment")  
                    audio = AudioSegment.from_wav(full_path)  
                    combined += audio  
                    print(f"[DEBUG] Added audio segment (duration: {len(audio)}ms)")  
                else:  
                    print(f"[DEBUG] WARNING: File does not exist: {full_path}")  
              
            print(f"[DEBUG] Exporting combined audio (total duration: {len(combined)}ms)")  
            combined.export(combined_filename, format="wav")  
            print("[DEBUG] Export completed successfully")  
              
            # Clean up individual chunk files  
            print("[DEBUG] Starting cleanup of individual chunk files")  
            for audio_file in audio_files:  
                try:  
                    os.remove(audio_file)  
                    print(f"[DEBUG] Deleted chunk file: {audio_file}")  
                except OSError as e:  
                    print(f"[DEBUG] Could not delete {audio_file}: {str(e)}")  
                      
        except ImportError:  
            print("[DEBUG] pydub not available, using simple binary combination")  
            # Fallback to simple binary combination  
            self._simple_combine(audio_files, combined_filename)  
          
        print(f"[DEBUG] Audio combination completed: {combined_filename}")  
        return combined_filename  
  
    def _simple_combine(self, audio_files: List[str], output_filename: str):  
        """Simple binary combination fallback method"""  
        print(f"[DEBUG] Starting simple binary combination to: {output_filename}")  
          
        with open(output_filename, 'wb') as outfile:  
            for i, audio_file in enumerate(audio_files):  
                full_path = os.path.abspath(audio_file)  
                print(f"[DEBUG] Processing file {i+1}/{len(audio_files)}: {full_path}")  
                  
                if os.path.exists(full_path):  
                    with open(full_path, 'rb') as infile:  
                        # Skip WAV header for all files except the first one  
                        if audio_file != audio_files[0]:  
                            infile.seek(44)  # Skip 44-byte WAV header  
                            print(f"[DEBUG] Skipped WAV header for file {i+1}")  
                        else:  
                            print(f"[DEBUG] Keeping WAV header for first file")  
                          
                        data = infile.read()  
                        outfile.write(data)  
                        print(f"[DEBUG] Written {len(data)} bytes from {audio_file}")  
                else:  
                    print(f"[DEBUG] WARNING: File does not exist: {full_path}")  
          
        print("[DEBUG] Starting cleanup of individual files")  
        # Clean up individual files  
        for audio_file in audio_files:  
            try:  
                os.remove(audio_file)  
                print(f"[DEBUG] Deleted chunk file: {audio_file}")  
            except OSError as e:  
                print(f"[DEBUG] Could not delete {audio_file}: {str(e)}")  
          
        print("[DEBUG] Simple binary combination completed")
