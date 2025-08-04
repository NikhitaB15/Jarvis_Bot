import pyttsx3

def configure_voice(engine, config):
    """Configure voice settings"""
    engine.setProperty('rate', config['voice']['rate'])
    engine.setProperty('volume', config['voice']['volume'])
    
    voices = engine.getProperty('voices')
    if len(voices) > config['voice']['voice_id']:
        engine.setProperty('voice', voices[config['voice']['voice_id']].id)