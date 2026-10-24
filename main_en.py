"""English entry point for the Nook build."""
import os

# Set before importing application modules: i18n reads this at import time.
os.environ["NOOK_LANGUAGE"] = "en"

from main import main

if __name__ == "__main__":
    main()
в