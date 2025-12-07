import os
import logging
from paddlespeech.cli.tts import TTSExecutor
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChineseTTSEngine:
    def __init__(self):
        """
        Initialize Chinese TTS Engine with PaddleSpeech
        """
        logger.info("Initializing PaddleSpeech TTS Engine...")
        self.tts = TTSExecutor()
        
        # Voice profiles with different characteristics
        # Note: PaddleSpeech has limited parameter support
        self.voice_profiles = {
            'default': {'spk_id': 0},
            'female': {'spk_id': 0},  # Default is female
            'male': {'spk_id': 1},    # If available
        }
        
        logger.info("✓ PaddleSpeech TTS Engine initialized successfully")
    
    def synthesize(self, text, output_path, speed=1.0, voice_profile=None):
        """
        Convert Chinese text to speech with PaddleSpeech
        
        Args:
            text: Chinese text to synthesize
            output_path: Output audio file path (.wav)
            speed: Speech speed (currently not supported in this version)
            voice_profile: Use predefined voice profile
        """
        # Apply voice profile if specified
        if voice_profile and voice_profile in self.voice_profiles:
            profile = self.voice_profiles[voice_profile]
            spk_id = profile['spk_id']
        else:
            spk_id = 0  # Default speaker
        
        logger.info(f"Synthesizing: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        start_time = time.time()
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Perform TTS - CORRECT PARAMETERS for PaddleSpeech
            self.tts(
                text=text,
                output=output_path,
                am='fastspeech2_csmsc',    # Chinese acoustic model
                voc='hifigan_csmsc',       # Chinese vocoder
                lang='zh',                 # Chinese language
                spk_id=spk_id              # Speaker ID
                # Note: 'speed' parameter is not available in this version
                # You might need to use a different PaddleSpeech version for speed control
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✓ Synthesis completed in {processing_time:.2f}s: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'processing_time': processing_time,
                'text_length': len(text)
            }
            
        except Exception as e:
            logger.error(f"✗ Synthesis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def get_available_options(self):
        """Get all available configuration options"""
        return {
            'voice_profiles': list(self.voice_profiles.keys()),
            'acoustic_models': ['fastspeech2_csmsc', 'fastspeech2_aishell3'],
            'vocoders': ['hifigan_csmsc', 'pwgan_csmsc'],
            'note': 'Speed control may not be available in this PaddleSpeech version'
        }
    
    def test_synthesis(self):
        """Test the TTS engine with a simple sentence"""
        test_text = "你好，这是一个中文语音合成测试。欢迎使用PaddleSpeech。"
        output_path = "test_output.wav"
        
        logger.info("Running synthesis test...")
        result = self.synthesize(test_text, output_path)
        
        if result['success']:
            logger.info("✓ Test completed successfully!")
            return True
        else:
            logger.error("✗ Test failed!")
            return False