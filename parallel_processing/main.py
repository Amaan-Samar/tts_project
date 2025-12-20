#!/usr/bin/env python3
"""
Dialogue TTS System
Convert dialogue scripts to audio with character-specific voices
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.voice_manager import VoiceManager
from src.dialogue_processor import DialogueProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_dialogue.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Convert dialogue scripts to audio with character voices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process dialogue with config file
  python main.py --config config/characters_config.json
  
  # List character voices
  python main.py --config config/characters_config.json --list-characters
  
  # Test specific character voice
  python main.py --config config/characters_config.json --test-voice "Keonne Rodriguez"
        """
    )
    
    parser.add_argument('--config', required=True, help='JSON configuration file path')
    parser.add_argument('--list-characters', action='store_true', help='List all characters and exit')
    parser.add_argument('--test-voice', type=str, help='Test a specific character\'s voice')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        voice_manager = VoiceManager(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # List characters
    if args.list_characters:
        voice_manager.list_characters()
        return 0
    
    # Test specific voice
    if args.test_voice:
        character = voice_manager.find_character_by_name(args.test_voice)
        if character:
            logger.info(f"Testing voice for: {character.name}")
            logger.info(f"  Gender: {character.gender}")
            logger.info(f"  Speaker ID: {character.voice_profile.spk_id}")
            logger.info(f"  Aliases: {', '.join(character.aliases)}")
            
            # Test synthesis
            from paddlespeech.cli.tts import TTSExecutor
            tts = TTSExecutor()
            test_text = f"你好，我是{character.name}，这是我的声音。"
            output_file = f"test_{character.name.replace(' ', '_')}.wav"
            
            try:
                tts(
                    text=test_text,
                    output=output_file,
                    am=character.voice_profile.am,
                    voc=character.voice_profile.voc,
                    lang='zh',
                    spk_id=character.voice_profile.spk_id
                )
                logger.info(f"✓ Test audio saved to: {output_file}")
            except Exception as e:
                logger.error(f"✗ Test failed: {e}")
        else:
            logger.error(f"Character '{args.test_voice}' not found in configuration")
        return 0
    
    # Process dialogue
    try:
        # Read input text
        input_file = voice_manager.input_file
        if not input_file or not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return 1
        
        with open(input_file, 'r', encoding='utf-8') as f:
            dialogue_text = f.read()
        
        logger.info(f"Loaded dialogue from: {input_file}")
        logger.info(f"Text length: {len(dialogue_text)} characters")
        
        # Initialize dialogue processor
        processor = DialogueProcessor(voice_manager)
        
        # Parse dialogue
        segments = processor.parse_dialogue(dialogue_text)
        
        if not segments:
            logger.error("No dialogue segments found. Check format: 'Speaker：text'")
            return 1
        
        # Display parsing results
        logger.info("Parsed dialogue structure:")
        for segment in segments:
            logger.info(f"  [{segment.index}] {segment.speaker}: {segment.text[:50]}...")
        
        # Create temporary directory
        temp_dir = os.path.join(os.path.dirname(voice_manager.output_file), "temp_segments")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Process segments in parallel
        successful_segments, results = processor.process_dialogue_parallel(segments, temp_dir)
        
        # Statistics
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        total_chunks = sum(r.get('chunks', 1) for r in results if r['success'])
        
        logger.info(f"\nProcessing complete:")
        logger.info(f"  Successful segments: {successful}/{len(segments)}")
        logger.info(f"  Failed segments: {failed}")
        logger.info(f"  Total text chunks: {total_chunks}")
        
        if successful > 0:
            # Combine with pauses between speakers
            processor.combine_with_pauses(successful_segments, voice_manager.output_file)
            
            # Clean up temporary files
            if voice_manager.processing_config.get('cleanup_temp_files', True):
                processor.cleanup_temp_files(successful_segments)
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
            
            logger.info("\n" + "="*60)
            logger.info("✓ DIALOGUE PROCESSING COMPLETE")
            logger.info("="*60)
            logger.info(f"Output file: {voice_manager.output_file}")
            logger.info(f"Total duration: ~{len(successful_segments) * 5} seconds (estimated)")
            logger.info("="*60)
            
            return 0
        else:
            logger.error("✗ No segments were successfully processed")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())