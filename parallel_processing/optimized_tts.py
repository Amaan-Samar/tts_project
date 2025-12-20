# optimized_tts.py
import os
import logging
import concurrent.futures
import multiprocessing
import threading
from queue import Queue
from typing import List, Dict, Any
from paddlespeech.cli.tts import TTSExecutor
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedTTSEngine:
    def __init__(self, max_workers=None):
        """
        Optimized TTS Engine with parallel processing
        
        Args:
            max_workers: Maximum number of parallel workers (default: CPU cores - 1)
        """
        logger.info("Initializing Optimized TTS Engine...")
        
        # Determine optimal worker count
        if max_workers is None:
            self.max_workers = max(1, multiprocessing.cpu_count() - 1)
        else:
            self.max_workers = max_workers
            
        logger.info(f"Using {self.max_workers} parallel workers")
        
        # Voice mapping based on discovery (update these based on your findings)
        # These are EXAMPLE mappings - you need to discover actual ones
        self.voice_mapping = {
            'male': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'speakers': [0, 1, 2, 3, 10, 15, 20],  # Need to verify
                'description': 'Male voices'
            },
            'female': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'speakers': [50, 60, 70, 80, 90, 99],  # Need to verify
                'description': 'Female voices'
            }
        }
        
        # Thread-local TTS instances to avoid thread safety issues
        self._thread_local = threading.local()
        
    def get_tts_instance(self):
        """Get thread-local TTS instance"""
        if not hasattr(self._thread_local, 'tts_instance'):
            self._thread_local.tts_instance = TTSExecutor()
        return self._thread_local.tts_instance
    
    def synthesize_chunk(self, chunk_info: Dict) -> Dict:
        """Synthesize a single text chunk (worker function)"""
        chunk_id, text, output_file, model_config = chunk_info.values()
        
        try:
            tts = self.get_tts_instance()
            
            start_time = time.time()
            
            tts(
                text=text,
                output=output_file,
                am=model_config['am'],
                voc=model_config['voc'],
                lang='zh',
                spk_id=model_config['spk_id']
            )
            
            processing_time = time.time() - start_time
            
            return {
                'chunk_id': chunk_id,
                'success': True,
                'output_file': output_file,
                'processing_time': processing_time,
                'text_length': len(text)
            }
            
        except Exception as e:
            logger.error(f"Chunk {chunk_id} failed: {e}")
            return {
                'chunk_id': chunk_id,
                'success': False,
                'error': str(e)
            }
    
    def parallel_synthesize(self, text_chunks: List[str], output_dir: str, 
                          voice_type: str = 'male', cleanup: bool = True) -> Dict[str, Any]:
        """
        Parallel text-to-speech synthesis
        
        Args:
            text_chunks: List of text chunks to synthesize
            output_dir: Output directory for audio files
            voice_type: 'male' or 'female'
            cleanup: Remove individual chunk files after combination
        """
        if voice_type not in self.voice_mapping:
            logger.warning(f"Voice type '{voice_type}' not found. Using 'male'.")
            voice_type = 'male'
        
        voice_config = self.voice_mapping[voice_type]
        speakers = voice_config['speakers']
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare chunk tasks with round-robin speaker assignment
        chunk_tasks = []
        temp_files = []
        
        for i, chunk in enumerate(text_chunks):
            # Assign speakers in round-robin fashion
            spk_id = speakers[i % len(speakers)]
            
            output_file = os.path.join(output_dir, f"chunk_{i:04d}.wav")
            temp_files.append(output_file)
            
            chunk_tasks.append({
                'chunk_id': i,
                'text': chunk,
                'output_file': output_file,
                'model_config': {
                    'am': voice_config['am'],
                    'voc': voice_config['voc'],
                    'spk_id': spk_id
                }
            })
        
        logger.info(f"Starting parallel synthesis of {len(chunk_tasks)} chunks with {self.max_workers} workers")
        logger.info(f"Using speakers: {speakers}")
        
        start_time = time.time()
        
        # Process chunks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.synthesize_chunk, task) for task in chunk_tasks]
            
            results = []
            successful_chunks = 0
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    successful_chunks += 1
                    logger.info(f"Chunk {result['chunk_id']} completed in {result['processing_time']:.2f}s")
                else:
                    logger.error(f"Chunk {result['chunk_id']} failed: {result.get('error')}")
        
        total_time = time.time() - start_time
        
        # Combine successful chunks
        if successful_chunks > 0:
            combined_file = os.path.join(output_dir, "combined_output.wav")
            successful_files = [r['output_file'] for r in results if r['success']]
            
            # Combine audio files (you need to implement this or use existing)
            self.combine_audio_files(successful_files, combined_file)
            
            # Cleanup individual files
            if cleanup:
                for temp_file in successful_files:
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        
        # Statistics
        avg_time_per_chunk = sum(r.get('processing_time', 0) for r in results if r['success']) / max(1, successful_chunks)
        speedup_factor = (sum(r.get('processing_time', 0) for r in results if r['success']) / max(1, successful_chunks * self.max_workers))
        
        return {
            'success': successful_chunks > 0,
            'total_chunks': len(text_chunks),
            'successful_chunks': successful_chunks,
            'failed_chunks': len(text_chunks) - successful_chunks,
            'total_time': total_time,
            'avg_time_per_chunk': avg_time_per_chunk,
            'speedup_factor': speedup_factor,
            'combined_output': combined_file if successful_chunks > 0 else None
        }
    
    def combine_audio_files(self, input_files: List[str], output_file: str):
        """Combine multiple WAV files into one"""
        import wave
        import numpy as np
        
        if not input_files:
            return
        
        # Simple combination (you might need a better implementation)
        combined_data = []
        params = None
        
        for file_path in input_files:
            with wave.open(file_path, 'rb') as wav:
                if params is None:
                    params = wav.getparams()
                data = wav.readframes(wav.getnframes())
                combined_data.append(data)
        
        with wave.open(output_file, 'wb') as output:
            output.setparams(params)
            for data in combined_data:
                output.writeframes(data)
        
        logger.info(f"Combined {len(input_files)} files into {output_file}")

class ResourceMonitor:
    """Monitor system resources during TTS processing"""
    
    @staticmethod
    def get_system_resources():
        """Get current system resource usage"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_count': psutil.cpu_count(),
            'available_memory_gb': psutil.virtual_memory().available / (1024**3)
        }
    
    @staticmethod
    def suggest_worker_count():
        """Suggest optimal worker count based on system resources"""
        import psutil
        
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative estimate
        if memory_gb < 4:
            return 2
        elif memory_gb < 8:
            return min(4, cpu_count - 1)
        elif memory_gb < 16:
            return min(6, cpu_count - 1)
        else:
            return min(8, cpu_count - 1)