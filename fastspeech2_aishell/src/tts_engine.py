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
        Using fastspeech2_aishell3 for multiple speakers (male/female)
        """
        logger.info("Initializing PaddleSpeech TTS Engine...")
        self.tts = TTSExecutor()
        
        # Voice profiles for fastspeech2_aishell3 model
        # This model has 174 speakers including male and female voices
        self.voice_profiles = {
            'default': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 0,        # female voice
                'description': 'Default female voice'
            },
            'female13': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 0,        # female voice
                'description': 'Male voice (Speaker 0)'
            },
            'male2': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 1,        # Another male voice
                'description': 'Male voice (Speaker 1)'
            },
            'female': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 99,       # Female voice
                'description': 'Female voice (Speaker 99)'
            },
            'male': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 10,       # Another female voice
                'description': 'Female voice (Speaker 10)'
            },
            'female3': {
                'am': 'fastspeech2_aishell3',
                'voc': 'hifigan_aishell3',
                'spk_id': 20,       # Another female voice
                'description': 'Female voice (Speaker 20)'
            },
            # Alternative model (single female speaker)
            'csmsc_female': {
                'am': 'fastspeech2_csmsc',
                'voc': 'hifigan_csmsc',
                'spk_id': 0,
                'description': 'Standard female voice (CSMSC model)'
            }
        }
        
        logger.info("✓ PaddleSpeech TTS Engine initialized successfully")
        logger.info(f"Available voice profiles: {', '.join(self.voice_profiles.keys())}")
    
    def synthesize(self, text, output_path, speed=1.0, voice_profile='default'):
        """
        Convert Chinese text to speech with PaddleSpeech
        
        Args:
            text: Chinese text to synthesize
            output_path: Output audio file path (.wav)
            speed: Speech speed (currently not supported in this version)
            voice_profile: Voice profile name from voice_profiles dict
        """
        # Get voice profile settings
        if voice_profile in self.voice_profiles:
            profile = self.voice_profiles[voice_profile]
            am_model = profile['am']
            vocoder = profile['voc']
            spk_id = profile['spk_id']
            description = profile['description']
        else:
            # Default to male voice
            profile = self.voice_profiles['default']
            am_model = profile['am']
            vocoder = profile['voc']
            spk_id = profile['spk_id']
            description = profile['description']
            logger.warning(f"Voice profile '{voice_profile}' not found. Using default.")
        
        logger.info(f"Synthesizing: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        logger.info(f"Using: {description} (Model: {am_model}, Speaker ID: {spk_id})")
        
        start_time = time.time()
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Perform TTS
            self.tts(
                text=text,
                output=output_path,
                am=am_model,
                voc=vocoder,
                lang='zh',
                spk_id=spk_id
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✓ Synthesis completed in {processing_time:.2f}s: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'processing_time': processing_time,
                'text_length': len(text),
                'model_used': am_model,
                'speaker_id': spk_id,
                'voice_profile': voice_profile
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
        profiles_info = {}
        for name, profile in self.voice_profiles.items():
            profiles_info[name] = {
                'model': profile['am'],
                'speaker_id': profile['spk_id'],
                'description': profile['description']
            }
        
        return {
            'voice_profiles': profiles_info,
            'available_models': ['fastspeech2_aishell3', 'fastspeech2_csmsc', 'fastspeech2_mix'],
            'available_vocoders': ['hifigan_aishell3', 'hifigan_csmsc', 'pwgan_csmsc'],
            'note': 'fastspeech2_aishell3 has 174 speakers (male and female)'
        }
    
    def list_speakers(self):
        """List available speakers with their IDs"""
        print("\n" + "="*60)
        print("AVAILABLE VOICE PROFILES")
        print("="*60)
        for name, profile in self.voice_profiles.items():
            print(f"{name:15} | Model: {profile['am']:25} | Speaker: {profile['spk_id']:3} | {profile['description']}")
        print("="*60)
    
    def test_synthesis(self, voice_profile='default'):
        """Test the TTS engine with a simple sentence"""
        test_text = "你好，这是一个中文语音合成测试。欢迎使用PaddleSpeech。"
        output_path = f"test_output_{voice_profile}.wav"
        
        logger.info(f"Running synthesis test with '{voice_profile}' profile...")
        result = self.synthesize(test_text, output_path, voice_profile=voice_profile)
        
        if result['success']:
            logger.info(f"✓ Test completed successfully! Output: {output_path}")
            logger.info(f"  Model: {result['model_used']}, Speaker: {result['speaker_id']}")
            return True
        else:
            logger.error(f"✗ Test failed: {result.get('error', 'Unknown error')}")
            return False