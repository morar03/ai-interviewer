import anthropic
import os

def get_client():
    return anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

LEVEL_CONTEXT = {
    'junior': "The candidate is a junior professional (0-2 years experience). Ask simple, foundational questions. Avoid deep technical jargon. Focus on basic concepts and learning experiences.",
    'mid': "The candidate is a mid-level professional (2-5 years experience). Ask questions that explore practical experience and problem-solving. Expect some technical depth.",
    'senior': "The candidate is a senior professional (5+ years experience). Ask deep, complex questions about architecture decisions, leadership, trade-offs, and strategic thinking. Expect expert-level answers.",
}

def generate_first_question(topic, level):
    client = get_client()
    level_context = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT['mid'])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": f"""You are a professional researcher conducting an interview about "{topic}".

                Candidate level: {level_context}

                Generate the FIRST opening question for this interview.
                - Adapt the complexity to the candidate level
                - It should be open-ended and welcoming
                - It should invite the interviewee to share their general perspective
                - Return ONLY the question, nothing else"""
            }
        ]
    )
    return message.content[0].text.strip()


def generate_next_question(topic, level, qa_pairs):
    client = get_client()
    level_context = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT['mid'])

    interview_so_far = ""
    for i, (question, answer) in enumerate(qa_pairs, 1):
        interview_so_far += f"Q{i}: {question}\nA{i}: {answer}\n\n"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": f"""You are a professional researcher conducting an interview about "{topic}".

                Candidate level: {level_context}

                Interview so far:
                {interview_so_far}

                You have asked {len(qa_pairs)} question(s) so far.

                Rules:
                - You must ask AT LEAST 3 questions total
                - You must ask AT MOST 5 questions total
                - If you have asked less than 3 questions: ALWAYS continue
                - If you have asked 3-4 questions: continue ONLY if the answers lack depth or important angles are unexplored
                - If you have asked 5 questions: ALWAYS end
                - Adapt question complexity to the candidate level

                Respond in EXACTLY this format:
                CONTINUE: [YES/NO]
                QUESTION: [your next question, or leave empty if NO]"""
            }
        ]
    )

    raw = message.content[0].text.strip()
    result = {"continue": False, "question": ""}

    for line in raw.split('\n'):
        if line.startswith('CONTINUE:'):
            value = line.replace('CONTINUE:', '').strip()
            result["continue"] = value == "YES"
        elif line.startswith('QUESTION:'):
            result["question"] = line.replace('QUESTION:', '').strip()

    return result


def generate_summary(topic, level, qa_pairs):
    client = get_client()
    interview_text = ""
    for i, (question, answer) in enumerate(qa_pairs, 1):
        interview_text += f"Q{i}: {question}\nA{i}: {answer}\n\n"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are analyzing an interview about "{topic}" with a {level} level candidate.

                Full transcript:
                {interview_text}

                Provide:
                1. A brief summary (2-3 sentences) of key themes and insights
                2. Overall sentiment (Positive / Neutral / Negative)
                3. Top 5 keywords (comma separated)

                Format EXACTLY like this:
                SUMMARY: [your summary here]
                SENTIMENT: [Positive/Neutral/Negative]
                KEYWORDS: [keyword1, keyword2, keyword3, keyword4, keyword5]"""
            }
        ]
    )

    raw = message.content[0].text.strip()
    result = {"summary": "", "sentiment": "", "keywords": ""}

    for line in raw.split('\n'):
        if line.startswith('SUMMARY:'):
            result["summary"] = line.replace('SUMMARY:', '').strip()
        elif line.startswith('SENTIMENT:'):
            result["sentiment"] = line.replace('SENTIMENT:', '').strip()
        elif line.startswith('KEYWORDS:'):
            result["keywords"] = line.replace('KEYWORDS:', '').strip()

    return result