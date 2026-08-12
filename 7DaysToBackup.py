import os
import sys

# Proje kök dizinini sys.path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
