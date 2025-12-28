import os

# Read the OpenAI API key from the environment. Export in your terminal before running:
# export OPENAI_API_KEY="sk-..."
OPENAI_API_KEY = 'Your key here'

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Export it in your shell before running, e.g.:\n"
        "export OPENAI_API_KEY='sk-...'\n"
    )
