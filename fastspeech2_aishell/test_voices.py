# test_voices.py
from paddlespeech.cli.tts import TTSExecutor

def quick_test():
    """Quick test to verify male and female voices work"""
    tts = TTSExecutor()
    test_text = "你好，这是一个语音测试。男性声音和女性声音测试。"
    
    print("Testing different voices...")
    
    # Test 1: Male voice (speaker 0)
    print("1. Generating male voice (speaker 0)...")
    tts(
        text=test_text,
        output="test_female.wav",
        am='fastspeech2_aishell3',
        voc='hifigan_aishell3',
        lang='zh',
        spk_id=0
    )
    
    # Test 2: Female voice (speaker 99)
    print("2. Generating female voice (speaker 99)...")
    tts(
        text=test_text,
        output="test_female.wav",
        am='fastspeech2_aishell3',
        voc='hifigan_aishell3',
        lang='zh',
        spk_id=99
    )
    
    # Test 3: Another female voice (speaker 10)
    print("3. Generating another female voice (speaker 10)...")
    tts(
        text=test_text,
        output="test_male.wav",
        am='fastspeech2_aishell3',
        voc='hifigan_aishell3',
        lang='zh',
        spk_id=10
    )
    
    print("\n✓ Test completed! Files created:")
    print("  - test_male.wav (Male voice)")
    print("  - test_female.wav (Female voice)")
    print("  - test_female2.wav (Another female voice)")

if __name__ == "__main__":
    quick_test()