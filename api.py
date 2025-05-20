import enum
import logging
import random
import re
from typing import Annotated

from livekit.agents import llm

logger = logging.getLogger("interviewer-assistant")
logger.setLevel(logging.INFO)


class Zone(enum.Enum):
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    OFFICE = "office"


class InterviewerFnc(llm.FunctionContext):
    def __init__(self, resume_text: str, job_description: dict) -> None:
        super().__init__()
        self.resume_text = resume_text
        self.job_description = job_description
        self.questions = self.generate_questions()
        self.current_question_index = 0
        self.current_followup_index = 0

    def generate_questions(self):
        questions = []

        skills = self.extract_keywords("skills")
        experience = self.extract_keywords("experience")
        projects = self.extract_keywords("projects")
        tech_stack = skills + self.job_description.get("required_technologies", [])

        if experience:
            exp = experience[0]
            questions.append({
                "q": f"I noticed you mentioned: '{exp}'. Can you walk me through what you did there?",
                "followups": [
                    "What were your key contributions?",
                    "What challenges did you overcome?"
                ]
            })

        if tech_stack:
            tech = random.choice(tech_stack)
            questions.append({
                "q": f"Tell me about your experience with {tech}.",
                "followups": [
                    f"What was the biggest challenge you faced using {tech}?",
                    f"How did you ensure your code was reliable and efficient with {tech}?"
                ]
            })

        if projects:
            proj = projects[0]
            questions.append({
                "q": f"Tell me more about the project: '{proj}'. What problem were you solving?",
                "followups": [
                    "Was it a team project or solo?",
                    "How did you test and deploy it?"
                ]
            })

        job_qs = [
            "This role expects quick learning of new frameworks. Share an example where you had to do that.",
            "How do you usually manage tasks and deadlines in a team setting?",
            "What tools do you use for code versioning and why?"
        ]

        for q in job_qs:
            questions.append({"q": q, "followups": []})

        return questions[:6]

    def extract_keywords(self, section_name: str):
        """Extract keywords from a section like 'skills', 'experience', 'projects'."""
        pattern = re.compile(rf"{section_name}[\s:-]+([\s\S]+?)(\n\n|\Z)", re.IGNORECASE)
        match = pattern.search(self.resume_text)
        if match:
            content = match.group(1)
            keywords = re.split(r"[\n,•\-]+", content)
            return [k.strip() for k in keywords if k.strip()]
        return []

    @llm.ai_callable(description="start the technical interview")
    def start_interview(self, candidate_name: Annotated[str, llm.TypeInfo(description="Name of the candidate")]):
        logger.info("Starting interview with %s", candidate_name)
        intro = f"Hi {candidate_name}, let's begin the interview. Tell me about yourself."
        return {
            "intro": intro,
            "questions": []
        }

    @llm.ai_callable(description="handle and respond to candidate's answer")
    def process_response(self, response: Annotated[str, llm.TypeInfo(description="Candidate's answer")]):
        feedback = ""
        q_data = self.questions[self.current_question_index]

        if len(response.strip()) < 20:
            feedback = "Can you elaborate a bit more on that?"
            return {"reply": feedback}

        feedback = random.choice([
            "That's insightful.",
            "Thanks for sharing that.",
            "Great, that makes sense.",
            "Interesting, I appreciate the details."
        ])

        if self.current_followup_index < len(q_data["followups"]):
            followup = q_data["followups"][self.current_followup_index]
            self.current_followup_index += 1
            return {"reply": f"{feedback} {followup}"}

        self.current_question_index += 1
        self.current_followup_index = 0

        if self.current_question_index < len(self.questions):
            next_q = self.questions[self.current_question_index]["q"]
            return {"reply": f"{feedback} Let's move to the next question: {next_q}"}
        else:
            return {"reply": f"{feedback} That concludes our interview. Thank you for your time!"}
