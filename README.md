
# Conversational-AI using LiveKit OpenAI

.env

```
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
OPENAI_API_KEY=
RESUME_PATH=./data/resume.txt
JOB_DESC_PATH=./data/job_description.json
```

## First create a virtual environment 

```
python -m venv .venv
.venv\Scripts\activate     //windows
pip install -r requirements.txt
python main.py download-files
python main.py start
```
Now go to livekit playground or create your own frontend using livekit.
