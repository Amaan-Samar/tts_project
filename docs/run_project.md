# Chinese Document to Audio Converter - User Guide

## Overview
This tool converts Chinese text documents to audio using PaddleSpeech TTS. It supports both direct text input and file processing.

## Installation Requirements

```bash
# Clone the repository (if applicable)
git clone <repository-url>
cd chinese-tts-converter

# Install dependencies
pip install paddlepaddle paddlespeech
# Additional dependencies may be required
```

## Basic Usage

### 1. Command Line Interface

**Direct text input:**
```bash
python main.py --text "你好，这是一个测试。" --output test.wav
```

**File input:**
```bash
python main.py --file input.txt --output output.wav
```

### 2. Voice Profile Selection
The current version supports basic voice selection:

```bash
# Use female voice profile
python main.py --file document.txt --output female_output.wav --profile female

# Use male voice profile
python main.py --file document.txt --output male_output.wav --profile male

# Use default voice
python main.py --file document.txt --output default_output.wav --profile default
```

### 3. Utility Commands

**List available options:**
```bash
python main.py --list-options
```

**Run system test:**
```bash
python main.py --test
```
python main.py --file C:\Users\Amaan\Documents\github_projects\tts_project\subtitles\chinese_text.txt --output C:\Users\Amaan\Documents\github_projects\tts_project\data\Modern_Woman_HORRIFIED_When_She_Discovers_Why_Her_Grandfathers_Generation_Had_Successful_Marriages.wav --profile male