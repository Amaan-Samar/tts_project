#!/usr/bin/env python3
"""
Chinese Document to Audio Converter
Main entry point for the application
"""

import os
import argparse
import logging
# from tts_engine import ChineseTTSEngine
from src.tts_engine import ChineseTTSEngine
from src.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Convert Chinese documents to audio using PaddleSpeech',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert file with male voice
  python main.py --file "document.txt" --output "output.wav" --profile male
  
  # Convert file with female voice
  python main.py --file "document.txt" --output "output.wav" --profile female
  
  # List available voice profiles
  python main.py --list-profiles
  
  # Test all voices
  python main.py --test-all
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', type=str, help='Direct text input')
    input_group.add_argument('--file', type=str, help='Input text file path')
    
    # Output options
    parser.add_argument('--output', type=str, default='output/document_audio.wav', 
                       help='Output audio file path (default: output/document_audio.wav)')
    
    # Voice control options
    parser.add_argument('--profile', type=str, default='default',
                       help='Voice profile to use (default: male)')
    
    # Additional options
    parser.add_argument('--list-profiles', action='store_true',
                       help='List all available voice profiles and exit')
    parser.add_argument('--test', action='store_true',
                       help='Run a quick test with default voice')
    parser.add_argument('--test-all', action='store_true',
                       help='Test all available voice profiles')
    
    args = parser.parse_args()
    
    # Initialize TTS engine
    try:
        tts_engine = ChineseTTSEngine()
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")
        return 1
    
    # List available profiles
    if args.list_profiles:
        tts_engine.list_speakers()
        return 0
    
    # Test all voices
    if args.test_all:
        logger.info("Testing all voice profiles...")
        success_count = 0
        for profile in tts_engine.voice_profiles.keys():
            if tts_engine.test_synthesis(voice_profile=profile):
                success_count += 1
        logger.info(f"✓ {success_count}/{len(tts_engine.voice_profiles)} voice profiles tested successfully")
        return 0 if success_count > 0 else 1
    
    # Run single test
    if args.test:
        logger.info(f"Running TTS test with '{args.profile}' profile...")
        success = tts_engine.test_synthesis(voice_profile=args.profile)
        return 0 if success else 1
    
    # Read input text
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Read {len(text)} characters from {args.file}")
        except Exception as e:
            logger.error(f"Error reading file {args.file}: {e}")
            return 1
    else:
        text = args.text
        logger.info(f"Processing {len(text)} characters from command line")
    
    # Validate text
    if not text or not text.strip():
        logger.error("No text to process")
        return 1
    
    # Initialize document processor
    processor = DocumentProcessor(tts_engine)
    
    # Process document
    try:
        logger.info(f"Starting document processing with '{args.profile}' voice profile...")
        
        result = processor.process_document(
            document_text=text,
            output_path=args.output,
            voice_profile=args.profile
        )
        
        if result['success']:
            logger.info("="*60)
            logger.info("✓ Document processing completed successfully!")
            logger.info(f"Output: {result['output_path']}")
            logger.info(f"Voice Profile: {args.profile}")
            logger.info(f"Statistics: {result['processed_chunks']}/{result['total_chunks']} chunks processed")
            logger.info(f"Total characters: {result['total_characters']}")
            logger.info("="*60)
            return 0
        else:
            logger.error(f"✗ Document processing failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        return 1

if __name__ == "__main__":
    exit(main())