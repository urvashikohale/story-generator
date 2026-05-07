import os
from openai import OpenAI
from dotenv import load_dotenv

"""
What I would build next with 2 more hours:
- Add story categories (adventure, fantasy, bedtime calm-down) and tailor 
  the storyteller prompt differently for each category
- Add a voice output feature using text-to-speech so parents can play the 
  story aloud to their child
- Allow the child to make choices mid-story (interactive branching stories)
- Save favorite stories to a local file so they can be read again
"""

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_model(prompt: str, max_tokens=3000, temperature=0.7) -> str:
    """Send a prompt to GPT-3.5-turbo and return the response."""
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def generate_story(user_request: str) -> str:
    """Generate a bedtime story using a structured storytelling prompt."""
    prompt = f"""You are a warm, imaginative bedtime storyteller for children aged 5 to 10.

Your stories must:
- Use simple words a 5-year-old can understand
- Have a clear story arc: a beginning (introduce characters), middle (a small problem or adventure), and end (a happy, calming resolution)
- Be engaging, fun, and end on a peaceful note suitable for bedtime
- Be between 200-300 words long
- Avoid any scary, violent, or inappropriate content

Story request: {user_request}

Tell the story now:"""

    return call_model(prompt, temperature=0.9)


def judge_story(story: str, user_request: str) -> tuple[int, str]:
    """Use an LLM judge to evaluate the story and return a score and feedback."""
    prompt = f"""You are an expert children's story evaluator. 
Evaluate the following bedtime story for children aged 5-10.

Original request: {user_request}

Story to evaluate:
{story}

Score the story from 1-10 on these criteria:
1. Age appropriateness (simple words, safe content)
2. Story arc quality (clear beginning, middle, end)
3. Engagement (fun, imaginative, interesting)
4. Bedtime suitability (calm, positive ending)
5. How well it matches the original request

Respond in this exact format:
SCORE: [number 1-10]
FEEDBACK: [2-3 sentences explaining what is good and what could be improved]"""

    response = call_model(prompt, temperature=0.1)

    # Parse score and feedback from judge response
    lines = response.strip().split("\n")
    score = 5  # default
    feedback = response

    for line in lines:
        if line.startswith("SCORE:"):
            try:
                score = int(line.replace("SCORE:", "").strip())
            except:
                score = 5
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()

    return score, feedback


def improve_story(story: str, feedback: str, user_request: str) -> str:
    """Rewrite the story based on judge feedback."""
    prompt = f"""You are a warm, imaginative bedtime storyteller for children aged 5 to 10.

You wrote this story based on the request: {user_request}

Original story:
{story}

A story expert gave this feedback:
{feedback}

Please rewrite the story, keeping what was good and fixing the issues mentioned.
Keep it between 200-300 words, age appropriate, and end peacefully for bedtime.

Improved story:"""

    return call_model(prompt, temperature=0.9)


def main():
    print("\n🌙 Welcome to the Bedtime Story Generator! 🌙\n")
    user_input = input("What kind of story do you want to hear? ")

    print("\n✨ Generating your story...\n")
    story = generate_story(user_input)
    print("--- YOUR STORY ---")
    print(story)

    print("\n🔍 Checking story quality...\n")
    score, feedback = judge_story(story, user_input)
    print(f"Judge Score: {score}/10")
    print(f"Judge Feedback: {feedback}")

    # If score is below 7, automatically improve the story
    if score < 7:
        print("\n🔄 Improving the story based on feedback...\n")
        story = improve_story(story, feedback, user_input)
        print("--- IMPROVED STORY ---")
        print(story)

        # Judge one more time
        score, feedback = judge_story(story, user_input)
        print(f"\nFinal Judge Score: {score}/10")

    # Allow user feedback loop
    while True:
        print("\n")
        user_feedback = input("Would you like any changes to the story? (or type 'done' to finish): ")
        if user_feedback.lower() == "done":
            break

        print("\n✨ Updating your story...\n")
        story = improve_story(story, user_feedback, user_input)
        print("--- UPDATED STORY ---")
        print(story)

    print("\n🌙 Sweet dreams! Goodnight! 🌙\n")


if __name__ == "__main__":
    main()