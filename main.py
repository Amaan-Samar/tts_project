#!/usr/bin/env python3
"""
Chinese Document to Audio Converter
Main entry point for the application
"""

import os
import argparse
import logging
from src.tts_engine import ChineseTTSEngine
from src.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Convert Chinese documents to audio using PaddleSpeech')
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', type=str, help='Direct text input')
    input_group.add_argument('--file', type=str, help='Input text file path')
    
    # Output options
    parser.add_argument('--output', type=str, default='output/document_audio.wav', 
                       help='Output audio file path (default: output/document_audio.wav)')
    
    # Voice control options (limited in this version)
    parser.add_argument('--profile', type=str, 
                       choices=['default', 'female', 'male'],
                       help='Use predefined voice profile')
    
    # Additional options
    parser.add_argument('--list-options', action='store_true',
                       help='List all available options and exit')
    parser.add_argument('--test', action='store_true',
                       help='Run a quick test and exit')
    
    args = parser.parse_args()
    
    # Initialize TTS engine
    try:
        tts_engine = ChineseTTSEngine()
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")
        return 1
    
    # List available options
    if args.list_options:
        options = tts_engine.get_available_options()
        print("\nAvailable Options:")
        print(f"Voice Profiles: {', '.join(options['voice_profiles'])}")
        print(f"Acoustic Models: {', '.join(options['acoustic_models'])}")
        print(f"Vocoders: {', '.join(options['vocoders'])}")
        print(f"Note: {options['note']}")
        return 0
    
    # Run test
    if args.test:
        logger.info("Running TTS test...")
        success = tts_engine.test_synthesis()
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
        logger.info("Starting document processing...")
        
        result = processor.process_document(
            document_text=text,
            output_path=args.output,
            voice_profile=args.profile
        )
        
        if result['success']:
            logger.info("Document processing completed successfully!")
            logger.info(f"Output: {result['output_path']}")
            logger.info(f"Statistics: {result['processed_chunks']}/{result['total_chunks']} chunks processed")
            logger.info(f"Total characters: {result['total_characters']}")
            return 0
        else:
            logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        return 1

if __name__ == "__main__":
    exit(main())