import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from paddlespeech.cli.tts import TTSExecutor

logger = logging.getLogger(__name__)

@dataclass
class VoiceProfile:
    am: str
    voc: str
    spk_id: int
    gender: str
    description: str = ""

class Character:
    def __init__(self, name: str, aliases: List[str], gender: str, 
                 voice_profile: VoiceProfile, description: str = ""):
        self.name = name
        self.aliases = aliases
        self.gender = gender
        self.voice_profile = voice_profile
        self.description = description
        self.all_names = set([name.lower()] + [alias.lower() for alias in aliases])
    
    def matches(self, name: str) -> bool:
        return name.lower() in self.all_names

class VoiceManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.characters: List[Character] = []
        self.default_narrator: Optional[Character] = None
        self.processing_config = {}
        self.input_file = ""
        self.output_file = ""
        
        self._load_config()
        self._initialize_tts_pool()
        
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.input_file = config.get('input_file', '')
            self.output_file = config.get('output_file', '')
            self.processing_config = config.get('processing', {})
            
            # Load characters
            for char_config in config.get('characters', []):
                voice_config = char_config.get('voice_profile', {})
                voice_profile = VoiceProfile(
                    am=voice_config.get('am', 'fastspeech2_aishell3'),
                    voc=voice_config.get('voc', 'hifigan_aishell3'),
                    spk_id=voice_config.get('spk_id', 0),
                    gender=char_config.get('gender', 'unknown'),
                    description=char_config.get('description', '')
                )
                
                character = Character(
                    name=char_config['name'],
                    aliases=char_config.get('aliases', []),
                    gender=char_config.get('gender', 'unknown'),
                    voice_profile=voice_profile,
                    description=char_config.get('description', '')
                )
                self.characters.append(character)
                logger.info(f"Loaded character: {character.name} (aliases: {character.aliases})")
            
            # Load default narrator
            narrator_config = config.get('default_narrator', {})
            if narrator_config:
                voice_config = narrator_config.get('voice_profile', {})
                voice_profile = VoiceProfile(
                    am=voice_config.get('am', 'fastspeech2_aishell3'),
                    voc=voice_config.get('voc', 'hifigan_aishell3'),
                    spk_id=voice_config.get('spk_id', 0),
                    gender=narrator_config.get('gender', 'unknown'),
                    description="Default Narrator"
                )
                self.default_narrator = Character(
                    name="Narrator",
                    aliases=["Narrator", "旁白"],
                    gender=narrator_config.get('gender', 'unknown'),
                    voice_profile=voice_profile,
                    description="Default narrator for unassigned text"
                )
                logger.info(f"Loaded default narrator: {self.default_narrator.voice_profile.spk_id}")
            
            logger.info(f"Loaded {len(self.characters)} characters from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _initialize_tts_pool(self):
        """Initialize thread-local TTS instances"""
        import threading
        self._thread_local = threading.local()
    
    def get_tts_instance(self):
        """Get thread-local TTS instance"""
        if not hasattr(self._thread_local, 'tts_instance'):
            self._thread_local.tts_instance = TTSExecutor()
        return self._thread_local.tts_instance
    
    def find_character_by_name(self, name: str) -> Optional[Character]:
        """Find character by name or alias"""
        for character in self.characters:
            if character.matches(name):
                return character
        
        # Try partial matches (for Chinese characters where name might be part of text)
        name_lower = name.lower()
        for character in self.characters:
            for alias in character.aliases:
                if alias.lower() in name_lower or name_lower in alias.lower():
                    return character
        
        return None
    
    def get_voice_profile(self, character_name: str) -> VoiceProfile:
        """Get voice profile for a character or use default narrator"""
        character = self.find_character_by_name(character_name)
        
        if character:
            logger.debug(f"Found character '{character_name}' -> {character.name} (spk_id: {character.voice_profile.spk_id})")
            return character.voice_profile
        elif self.default_narrator:
            logger.debug(f"No character found for '{character_name}', using default narrator")
            return self.default_narrator.voice_profile
        else:
            # Fallback to first character's voice
            logger.warning(f"No character or narrator found for '{character_name}', using first character")
            return self.characters[0].voice_profile if self.characters else VoiceProfile(
                am='fastspeech2_aishell3',
                voc='hifigan_aishell3',
                spk_id=0,
                gender='unknown'
            )
    
    def list_characters(self):
        """List all loaded characters"""
        print("\n" + "="*80)
        print("CHARACTER VOICE CONFIGURATION")
        print("="*80)
        for character in self.characters:
            print(f"Name: {character.name:20} | Gender: {character.gender:6} | "
                  f"Speaker ID: {character.voice_profile.spk_id:3} | "
                  f"Aliases: {', '.join(character.aliases)}")
        if self.default_narrator:
            print(f"\nDefault Narrator: {self.default_narrator.name} | "
                  f"Gender: {self.default_narrator.gender} | "
                  f"Speaker ID: {self.default_narrator.voice_profile.spk_id}")
        print("="*80)