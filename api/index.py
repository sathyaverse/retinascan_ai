import sys
import os

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
