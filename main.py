import asyncio
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from api import InterviewerFnc
import json

load_dotenv()

with open("resume.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()

with open("job_description.json", "r") as f:
    job_description = json.load(f)


async def entrypoint(ctx: JobContext):
    candidate_name = "Candidate"
    for line in resume_text.splitlines():
        if "name" in line.lower():
            candidate_name = line.split(":")[-1].strip()
            break

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are an AI interviewer for a technical role. Use the candidate's resume and the job description to guide the interview. "
            "Start with a friendly but formal tone, greet the candidate using their name, and begin with 'Tell me about yourself'. "
            "Ask 5–6 technical questions directly related to the resume, with 2–3 follow-ups for each. Avoid filler. Stay on-topic."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    fnc_ctx = InterviewerFnc(resume_text, job_description)

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )
    assistant.start(ctx.room)

    await asyncio.sleep(1)
    await assistant.say(f"Hi {candidate_name}, let's begin the interview. Tell me about yourself.", allow_interruptions=True)

    # Wait for candidate's intro
    first_response = await assistant.listen(timeout=60)
    await assistant.say("Thank you for sharing. Let's begin with some technical questions.", allow_interruptions=True)

    # Interactive question loop
    while fnc_ctx.current_question_index < len(fnc_ctx.questions):
        q_data = fnc_ctx.questions[fnc_ctx.current_question_index]

        if fnc_ctx.current_followup_index == 0:
            await assistant.say(q_data["q"], allow_interruptions=True)
        else:
            await assistant.say(q_data["followups"][fnc_ctx.current_followup_index - 1], allow_interruptions=True)

        candidate_response = await assistant.listen(timeout=90)

        try:
            reply_data = await fnc_ctx.process_response(candidate_response)
            await assistant.say(reply_data["reply"], allow_interruptions=True)
        except Exception as e:
            await assistant.say("Sorry, I encountered an issue. Let's move on.", allow_interruptions=True)
            fnc_ctx.current_question_index += 1
            fnc_ctx.current_followup_index = 0

    await assistant.say("That concludes our interview. Best of luck!", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
