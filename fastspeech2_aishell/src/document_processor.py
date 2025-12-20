import os
import re
import logging
import wave
from typing import List, Dict, Any
from .tts_engine import ChineseTTSEngine

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, tts_engine=None):
        self.tts_engine = tts_engine or ChineseTTSEngine()
        
    def chunk_text(self, text: str, max_length: int = 200) -> List[str]:
        """
        Split Chinese text into natural-sounding chunks
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split by sentence endings (。！？!?.)
        sentences = re.split(r'([。！？!?\.])', text)
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            sentence = sentence.strip()
            
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) <= max_length:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # Single sentence is too long
                    if len(sentence) > max_length:
                        comma_splits = re.split(r'[，,；;]', sentence)
                        if len(comma_splits) > 1:
                            chunks.extend([s.strip() for s in comma_splits if s.strip()])
                        else:
                            for j in range(0, len(sentence), max_length):
                                chunk = sentence[j:j+max_length]
                                if chunk.strip():
                                    chunks.append(chunk.strip())
                    else:
                        current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
            
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def combine_audio_files(self, file_list: List[str], output_path: str):
        """Combine multiple WAV files into one"""
        if not file_list:
            raise ValueError("No audio files to combine")
        
        data = []
        params = None
        
        for file_path in file_list:
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
        
        with wave.open(output_path, 'wb') as output:
            output.setparams(params)
            for frames in data:
                output.writeframes(frames)
        
        logger.info(f"Combined {len(file_list)} files into {output_path}")
    
    def process_document(self, document_text: str, output_path: str, 
                        voice_profile: str = None,
                        cleanup: bool = True) -> Dict[str, Any]:
        """
        Process entire document to audio
        
        Args:
            document_text: Full document text
            output_path: Output audio file path
            voice_profile: Predefined voice profile
            cleanup: Remove temporary chunk files
        """
        logger.info(f"Starting document processing: {output_path}")
        
        # Create output directory
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Split document into chunks
        chunks = self.chunk_text(document_text)
        
        if not chunks:
            return {
                'success': False,
                'error': 'No text chunks generated',
                'output_path': None
            }
        
        temp_files = []
        processed_chunks = 0
        total_chars = 0
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk[:30]}...")
            
            temp_file = f"temp_chunk_{i:04d}.wav"
            
            result = self.tts_engine.synthesize(
                text=chunk,
                output_path=temp_file,
                voice_profile=voice_profile
            )
            
            if result['success']:
                temp_files.append(temp_file)
                processed_chunks += 1
                total_chars += len(chunk)
                logger.info(f"✓ Chunk {i+1} processed successfully")
            else:
                logger.error(f"✗ Failed to process chunk {i+1}: {result.get('error', 'Unknown error')}")
        
        # Combine audio files if we have successful chunks
        if temp_files:
            try:
                self.combine_audio_files(temp_files, output_path)
                
                # Cleanup temporary files
                if cleanup:
                    for temp_file in temp_files:
                        try:
                            os.remove(temp_file)
                        except OSError as e:
                            logger.warning(f"Could not remove temp file {temp_file}: {e}")
                
                logger.info(f"Document processing completed: {output_path}")
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'total_chunks': len(chunks),
                    'processed_chunks': processed_chunks,
                    'total_characters': total_chars,
                    'failed_chunks': len(chunks) - processed_chunks
                }
                
            except Exception as e:
                logger.error(f"Failed to combine audio files: {e}")
                return {
                    'success': False,
                    'error': f'Audio combination failed: {e}',
                    'output_path': None
                }
        else:
            logger.error("No chunks were successfully processed")
            return {
                'success': False,
                'error': 'All chunks failed to process',
                'output_path': None
            }