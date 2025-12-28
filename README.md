InfinityTutor
==============
InfinityTutor is a lightweight CLI tutor that uses OpenAI’s Chat Completions API to teach topics, remember progress, and quiz you interactively.

Prerequisites
- Python 3.10+ recommended
- An OpenAI API key
- `pip` (and optionally `python -m venv` for a virtual environment)

Setup
1) Clone the repo and `cd` into it.
2) (Optional) Create a virtual environment: `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
3) Install dependencies: `pip install -r requirements.txt`.
4) Configure your API key: edit `config/key.py` and set `OPENAI_API_KEY` to your key (or change it to read from an environment variable). Keep this file out of version control.

Run
- Start the tutor: `python main.py`.
- Type questions or topics to learn; type `exit` or `quit` to stop.

How it works
- Conversation memory is persisted at `memory/state.json`; interaction logs are written to `memory/logbook.log`.
- The teaching persona and rules live in `core/prompts.py`.
- OpenAI requests are handled in `core/openai_client.py`.

Troubleshooting
- If you see “Sorry, I had trouble reaching the model,” check your network and API key.
- Delete `memory/state.json` if you want to reset stored progress.
