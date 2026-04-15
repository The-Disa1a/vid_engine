# vid_engine/context.py

# API Keys (To be populated by Colab)
PEXELS_API_KEYS = []
PIXABAY_API_KEYS =[]
GIPHY_API_KEYS = []
GEMINI_API_KEYS =[]

# Global Trackers
CURRENT_PEXELS_INDEX = 0
CURRENT_PIXABAY_INDEX = 0
CURRENT_GIPHY_INDEX = 0
CURRENT_GEMINI_INDEX = 0

# Models & Voice Configurations
GEMINI_MODELS =[]
GEMMA_MODELS =[]
VOICE = "en-US-AndrewMultilingualNeural"
TTS_RATE = "+5%"
TTS_PITCH = "-7Hz"
TTS_VOLUME = "+150%"

# Video Configurations
VIDEO_FORMAT = "Portrait"
ADV_OUTPUT = False
FONT_SCALE = 0.06
BGM_VOLUME = 0.08

# Hardware Setup
HAS_GPU = False
VIDEO_CODEC = "libx264"

# Global tracker to protect final exports from cleanup
SUCCESSFUL_VIDEOS =[]

# System Prompts
SYS_PROMPT_SUPERVISOR = ""
SYS_PROMPT_GIF = ""
SYS_PROMPT_BGV = ""
