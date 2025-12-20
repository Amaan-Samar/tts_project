import re
import os
import logging
import concurrent.futures
from typing import List, Dict, Any, Tuple
import wave
import numpy as np
from .voice_manager import VoiceManager

logger = logging.getLogger(__name__)

class DialogueSegment:
    """Represents a segment of dialogue spoken by a character"""
    def __init__(self, speaker: str, text: str, index: int):
        self.speaker = speaker
        self.text = text.strip()
        self.index = index
        self.audio_file = ""
        self.voice_profile = None
    
    def __repr__(self):
        return f"DialogueSegment(speaker={self.speaker}, text={self.text[:50]}..., index={self.index})"

class DialogueProcessor:
    def __init__(self, voice_manager: VoiceManager):
        self.voice_manager = voice_manager
        self.max_workers = voice_manager.processing_config.get('max_workers', 4)
        self.chunk_size = voice_manager.processing_config.get('chunk_size', 200)
        self.pause_duration_ms = voice_manager.processing_config.get('pause_between_speakers_ms', 300)
    
    def parse_dialogue(self, text: str) -> List[DialogueSegment]:
        """
        Parse dialogue text into segments
        
        Expected format:
        娜奥米：你好，这是一个对话。
        基翁：是的，这是一个测试。
        """
        segments = []
        
        # Pattern to match speaker names followed by colon (Chinese/English colon)
        # Supports: "Speaker：", "Speaker:", "Speaker :"
        pattern = r'^([^：:\n]+)[：:]\s*(.+?)(?=(?:\n[^：:\n]+[：:])|\n*$|\Z)'
        
        # Find all matches
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        
        index = 0
        for match in matches:
            speaker = match.group(1).strip()
            dialogue_text = match.group(2).strip()
            
            # Remove extra whitespace and normalize line breaks
            dialogue_text = re.sub(r'\s+', ' ', dialogue_text)
            
            if dialogue_text:  # Only add if there's actual text
                segment = DialogueSegment(speaker, dialogue_text, index)
                index += 1
                segments.append(segment)
                logger.debug(f"Parsed segment: {speaker} -> {dialogue_text[:50]}...")
        
        # Handle text before first speaker (if any)
        first_match = re.search(pattern, text)
        if first_match:
            start_pos = first_match.start()
            if start_pos > 0:
                intro_text = text[:start_pos].strip()
                if intro_text:
                    segment = DialogueSegment("Narrator", intro_text, 0)
                    segments.insert(0, segment)
                    logger.debug(f"Added intro narration: {intro_text[:50]}...")
        
        logger.info(f"Parsed {len(segments)} dialogue segments")
        return segments
    
    def chunk_dialogue_text(self, text: str, max_length: int = None) -> List[str]:
        """Split long dialogue text into manageable chunks"""
        if max_length is None:
            max_length = self.chunk_size
        
        # Split by Chinese sentence endings
        sentences = re.split(r'([。！？!?\.])', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            sentence = sentence.strip()
            
            if not sentence:
                continue
            
            # If adding this sentence would exceed max length
            if len(current_chunk) + len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # Sentence itself is too long, split by commas
                    comma_splits = re.split(r'[，,；;]', sentence)
                    for split in comma_splits:
                        split = split.strip()
                        if split:
                            if len(split) > max_length:
                                # Very long segment, split by length
                                for j in range(0, len(split), max_length):
                                    chunk = split[j:j+max_length]
                                    if chunk.strip():
                                        chunks.append(chunk.strip())
                            else:
                                if len(current_chunk) + len(split) > max_length:
                                    if current_chunk:
                                        chunks.append(current_chunk)
                                        current_chunk = split
                                    else:
                                        chunks.append(split)
                                else:
                                    current_chunk = split if not current_chunk else current_chunk + " " + split
            else:
                current_chunk = sentence if not current_chunk else current_chunk + " " + sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def synthesize_segment(self, segment: DialogueSegment, output_dir: str) -> Dict[str, Any]:
        """Synthesize a single dialogue segment"""
        try:
            # Get voice profile for this speaker
            voice_profile = self.voice_manager.get_voice_profile(segment.speaker)
            segment.voice_profile = voice_profile
            
            # Create output filename
            audio_file = os.path.join(output_dir, f"segment_{segment.index:04d}.wav")
            segment.audio_file = audio_file
            
            # Get TTS instance
            tts = self.voice_manager.get_tts_instance()
            
            # Split long text into chunks
            text_chunks = self.chunk_dialogue_text(segment.text)
            
            if len(text_chunks) == 1:
                # Single chunk, synthesize directly
                tts(
                    text=segment.text,
                    output=audio_file,
                    am=voice_profile.am,
                    voc=voice_profile.voc,
                    lang='zh',
                    spk_id=voice_profile.spk_id
                )
                logger.debug(f"Synthesized segment {segment.index}: {segment.speaker}")
                
                return {
                    'segment_id': segment.index,
                    'speaker': segment.speaker,
                    'success': True,
                    'audio_file': audio_file,
                    'chunks': 1
                }
            else:
                # Multiple chunks, synthesize and combine
                chunk_files = []
                for i, chunk in enumerate(text_chunks):
                    chunk_file = os.path.join(output_dir, f"segment_{segment.index:04d}_chunk_{i:03d}.wav")
                    
                    tts(
                        text=chunk,
                        output=chunk_file,
                        am=voice_profile.am,
                        voc=voice_profile.voc,
                        lang='zh',
                        spk_id=voice_profile.spk_id
                    )
                    chunk_files.append(chunk_file)
                
                # Combine chunks
                self.combine_audio_files(chunk_files, audio_file)
                
                # Clean up chunk files
                for chunk_file in chunk_files:
                    try:
                        os.remove(chunk_file)
                    except:
                        pass
                
                logger.debug(f"Synthesized segment {segment.index}: {segment.speaker} ({len(text_chunks)} chunks)")
                
                return {
                    'segment_id': segment.index,
                    'speaker': segment.speaker,
                    'success': True,
                    'audio_file': audio_file,
                    'chunks': len(text_chunks)
                }
            
        except Exception as e:
            logger.error(f"Failed to synthesize segment {segment.index} ({segment.speaker}): {e}")
            return {
                'segment_id': segment.index,
                'speaker': segment.speaker,
                'success': False,
                'error': str(e)
            }
    
    def process_dialogue_parallel(self, segments: List[DialogueSegment], 
                                 output_dir: str) -> Tuple[List[DialogueSegment], List[Dict]]:
        """Process all dialogue segments in parallel"""
        logger.info(f"Processing {len(segments)} segments with {self.max_workers} workers")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        successful_segments = []
        
        # Process segments in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_segment = {
                executor.submit(self.synthesize_segment, segment, output_dir): segment
                for segment in segments
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per segment
                    results.append(result)
                    
                    if result['success']:
                        successful_segments.append(segment)
                        logger.info(f"✓ Segment {segment.index}: {segment.speaker} ({result.get('chunks', 1)} chunks)")
                    else:
                        logger.error(f"✗ Segment {segment.index}: {segment.speaker} failed")
                
                except concurrent.futures.TimeoutError:
                    logger.error(f"✗ Segment {segment.index}: {segment.speaker} timed out")
                    results.append({
                        'segment_id': segment.index,
                        'speaker': segment.speaker,
                        'success': False,
                        'error': 'Timeout'
                    })
                except Exception as e:
                    logger.error(f"✗ Segment {segment.index}: {segment.speaker} error: {e}")
                    results.append({
                        'segment_id': segment.index,
                        'speaker': segment.speaker,
                        'success': False,
                        'error': str(e)
                    })
        
        # Sort successful segments by index
        successful_segments.sort(key=lambda x: x.index)
        
        return successful_segments, results
    
    def combine_with_pauses(self, segments: List[DialogueSegment], output_file: str):
        """Combine audio files with pauses between speakers"""
        if not segments:
            logger.error("No segments to combine")
            return
        
        logger.info(f"Combining {len(segments)} segments with pauses...")
        
        # Create pause audio (silence)
        pause_file = os.path.join(os.path.dirname(output_file), "pause.wav")
        self.create_silence_audio(pause_file, self.pause_duration_ms)
        
        # List all audio files in order with pauses
        audio_files = []
        current_speaker = None
        
        for i, segment in enumerate(segments):
            # Add pause if speaker changed (but not before first segment)
            if current_speaker is not None and segment.speaker != current_speaker:
                audio_files.append(pause_file)
            
            audio_files.append(segment.audio_file)
            current_speaker = segment.speaker
        
        # Combine all files
        self.combine_audio_files(audio_files, output_file)
        
        # Clean up pause file
        try:
            os.remove(pause_file)
        except:
            pass
        
        logger.info(f"Combined audio saved to: {output_file}")
    
    def create_silence_audio(self, output_file: str, duration_ms: int):
        """Create a silent audio file for pauses"""
        import wave
        import struct
        
        sample_rate = 24000  # PaddleSpeech default
        num_samples = int(sample_rate * duration_ms / 1000)
        
        with wave.open(output_file, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write silent frames
            silent_data = struct.pack('<h', 0) * num_samples
            wav_file.writeframes(silent_data)
    
    def combine_audio_files(self, input_files: List[str], output_file: str):
        """Combine multiple WAV files into one"""
        import wave
        
        if not input_files:
            return
        
        data = []
        params = None
        
        for file_path in input_files:
            if not os.path.exists(file_path):
                logger.warning(f"Audio file not found: {file_path}")
                continue
            
            try:
                with wave.open(file_path, 'rb') as wav_file:
                    if params is None:
                        params = wav_file.getparams()
                    data.append(wav_file.readframes(wav_file.getnframes()))
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
        
        if not data:
            raise ValueError("No valid audio data to combine")
        
        with wave.open(output_file, 'wb') as output:
            output.setparams(params)
            for frames in data:
                output.writeframes(frames)
    
    def cleanup_temp_files(self, segments: List[DialogueSegment]):
        """Clean up temporary audio files"""
        for segment in segments:
            if segment.audio_file and os.path.exists(segment.audio_file):
                try:
                    os.remove(segment.audio_file)
                except:
                    pass