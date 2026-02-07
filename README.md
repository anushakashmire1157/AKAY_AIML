NutriScan AI
============

NutriScan AI is a Python project that uses the USDA API to fetch nutritional information for foods. The project uses environment variables to securely manage API keys, ensuring they are not exposed on GitHub.

Features
--------

- Fetch nutritional data for food items using the USDA API
- Secure API key handling using `.env` file
- Easy to extend and integrate with front-end interfaces

Prerequisites
-------------

- Python 3.10+ installed
- `pip` package manager installed

Installation
------------

1. Clone the repository:

    git clone https://github.com/yourusername/your-repo.git
    cd your-repo

2. Install dependencies:

    pip install -r requirements.txt

*(Make sure `python-dotenv` is included in `requirements.txt`)*

3. Create a `.env` file in the root folder:

    MY_API_KEY=your_actual_usda_api_key_here

> ⚠️ Do **not** commit `.env` to GitHub. It contains sensitive API keys.

4. Add `.env` to `.gitignore` if it’s not already there:

    .env

Usage
-----

In your main Python file (e.g., `app.py`), use:

    from dotenv import load_dotenv
    import os

    load_dotenv()
    USDA_API_KEY = os.getenv("MY_API_KEY")

    print(f"USDA API Key loaded: {USDA_API_KEY}")  # Optional test

Then run:

    python app.py

Folder Structure
----------------

NutriScan-AI/
│
├── app.py          # Main application
├── .env            # Environment variables (API key)
├── .gitignore      # Ignore .env and other files
└── README.md       # This file


Created and developed by Team AKAY
