#!/usr/bin/env python3
"""
Quick test script for Chinese TTS
"""

import os
from src.tts_engine import ChineseTTSEngine
from src.document_processor import DocumentProcessor

def main():
    print("Testing Chinese TTS with PaddleSpeech...")
    
    # Test sentences
    test_sentences = [
        "你好，欢迎使用中文语音合成系统。",
        "人工智能正在改变我们的生活方式。",
        "今天天气很好，适合出去散步。",
        "学习新知识让人感到充实和快乐。"
    ]
    
    # Initialize engine
    print("1. Initializing TTS engine...")
    tts_engine = ChineseTTSEngine()
    
    # Test single sentence
    print("2. Testing single sentence synthesis...")
    result = tts_engine.synthesize(
        text=test_sentences[0],
        output_path="test_single.wav"
    )
    
    if result['success']:
        print(f"✓ Single sentence test passed: {result['output_path']}")
        print(f"  Processing time: {result['processing_time']:.2f}s")
        print(f"  Text length: {result['text_length']} characters")
    else:
        print(f"✗ Single sentence test failed: {result.get('error')}")
        return
    
    # Test document processing
    print("3. Testing document processing...")
    document_text = "。".join(test_sentences)
    
    processor = DocumentProcessor(tts_engine)
    result = processor.process_document(
        document_text=document_text,
        output_path="test_document.wav",
        voice_profile="male"
    )
    
    if result['success']:
        print(f"✓ Document processing test passed: {result['output_path']}")
        print(f"  Processed {result['processed_chunks']}/{result['total_chunks']} chunks")
        print(f"  Total characters: {result['total_characters']}")
    else:
        print(f"✗ Document processing test failed: {result.get('error')}")
        return
    
    print("\n🎉 All tests completed! Check the generated .wav files.")

if __name__ == "__main__":
    main()