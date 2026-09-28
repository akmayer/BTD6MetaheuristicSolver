from collections import deque

from BTD6TopbarOCR.OCRGameInterface import GameInterface

interface = GameInterface()
# Bound history to avoid unbounded image retention.
IMAGES_OUT_OF_ROUND = deque(maxlen=64)
