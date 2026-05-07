import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Bedtime Story Generator",
    page_icon="🌙",
    layout="centered"
)

# ── styling ──────────────────────────────────────────────
st.markdown("""
    <style>
    .story-box {
        background-color: #1e1e2e;
        border-radius: 12px;
        padding: 24px;
        font-size: 17px;
        line-height: 1.8;
        color: #cdd6f4;
        border: 1px solid #45475a;
    }
    .story-box-old {
        background-color: #2a1e2e;
        border-radius: 12px;
        padding: 24px;
        font-size: 17px;
        line-height: 1.8;
        color: #cdd6f4;
        border: 1px solid #8b5cf6;
        opacity: 0.8;
    }
    .score-good { color: #a6e3a1; font-size: 20px; font-weight: bold; }
    .score-bad  { color: #f38ba8; font-size: 20px; font-weight: bold; }
    .feedback-box {
        background-color: #313244;
        border-radius: 8px;
        padding: 14px;
        color: #bac2de;
        font-size: 14px;
    }
    .category-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 12px;
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
    }
    </style>
""", unsafe_allow_html=True)

# ── category config ───────────────────────────────────────
CATEGORIES = {
    "Adventure": {
        "emoji": "🦁",
        "color": "#f9a825",
        "description": "brave heroes, quests, and exciting journeys",
        "style": "exciting and action-packed but always safe and age-appropriate. Include a brave hero who faces a challenge and overcomes it through courage and friendship.",
    },
    "Fantasy": {
        "emoji": "🧚",
        "color": "#ab47bc",
        "description": "magic, fairies, dragons, and wizards",
        "style": "magical and whimsical with enchanting details. Include magical creatures, spells, or enchanted places. Make the world feel wondrous and full of possibility.",
    },
    "Animal": {
        "emoji": "🐾",
        "color": "#66bb6a",
        "description": "talking animals and forest friends",
        "style": "warm and friendly with talking animals as the main characters. Animals should have relatable personalities and learn a simple life lesson by the end.",
    },
    "Funny": {
        "emoji": "😄",
        "color": "#29b6f6",
        "description": "silly characters and humor",
        "style": "light-hearted and humorous with silly situations and funny misunderstandings. Make the child giggle while still ending on a calm, sleepy note.",
    },
    "Calm": {
        "emoji": "😴",
        "color": "#78909c",
        "description": "slow, peaceful stories for sleep",
        "style": "very gentle, slow-paced, and soothing. Use soft imagery like stars, moonlight, and cozy beds. Every sentence should make the child feel more relaxed and sleepy.",
    },
}

# ── helpers ──────────────────────────────────────────────
def call_model(prompt: str, temperature: float = 0.7, max_tokens: int = 3000) -> str:
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def categorize_request(request: str) -> str:
    """Categorize the story request into one of 5 categories."""
    prompt = f"""You are a children's story classifier.
Classify the following story request into exactly one of these categories:
- Adventure (brave heroes, quests, exploring)
- Fantasy (magic, fairies, dragons, wizards)
- Animal (talking animals, forest friends)
- Funny (silly characters, humor, jokes)
- Calm (slow, peaceful, purely for sleep)

Story request: {request}

Respond with ONLY the category name, nothing else. Example: Fantasy"""

    result = call_model(prompt, temperature=0.1, max_tokens=10)
    result = result.strip()
    # make sure it's a valid category, default to Fantasy if not
    if result not in CATEGORIES:
        return "Fantasy"
    return result


def generate_story(request: str, category: str) -> str:
    """Generate a story tailored to the detected category."""
    cat = CATEGORIES[category]
    prompt = f"""You are a warm, imaginative bedtime storyteller for children aged 5 to 10.

This is a {category} story — make it {cat['style']}

Your story must:
- Use simple words a 5-year-old can understand
- Have a clear story arc: beginning (introduce characters), middle (a small problem or adventure), end (a happy, calming resolution)
- Be between 200-300 words long
- End on a peaceful, sleepy note suitable for bedtime
- Avoid any scary, violent, or inappropriate content

Story request: {request}

Tell the story now:"""
    return call_model(prompt, temperature=0.9)


def judge_story(story: str, request: str) -> tuple[int, str]:
    prompt = f"""You are an expert children's story evaluator.
Evaluate this bedtime story for children aged 5-10.

Original request: {request}

Story:
{story}

Score it 1-10 on: age appropriateness, story arc, engagement, bedtime suitability, and how well it matches the original request.

Respond in this exact format:
SCORE: [number 1-10]
FEEDBACK: [2-3 sentences on what is good and what could improve]"""

    response = call_model(prompt, temperature=0.1)
    score, feedback = 5, response
    for line in response.strip().split("\n"):
        if line.startswith("SCORE:"):
            try:
                score = int(line.replace("SCORE:", "").strip())
            except:
                score = 5
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()
    return score, feedback


def improve_story(story: str, feedback: str, request: str, category: str) -> str:
    cat = CATEGORIES[category]
    prompt = f"""You are a warm, imaginative bedtime storyteller for children aged 5 to 10.

You wrote this {category} story for: {request}
The story should be {cat['style']}

Original story:
{story}

Feedback:
{feedback}

Rewrite the story keeping what was good and fixing the issues. Keep it 200-300 words, age appropriate, ending peacefully.

Improved story:"""
    return call_model(prompt, temperature=0.9)


# ── session state ─────────────────────────────────────────
defaults = {
    "story": None,
    "score": None,
    "feedback": None,
    "request": None,
    "category": None,
    "previous_story": None,
    "previous_score": None,
    "show_original": False,
    "has_changes": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── UI ────────────────────────────────────────────────────
st.title("🌙 Bedtime Story Generator")
st.caption("AI-powered stories for children aged 5–10")
st.divider()

user_input = st.text_input(
    "What kind of story would you like?",
    placeholder="e.g. A dragon who is afraid of the dark..."
)

if st.button("✨ Generate Story", use_container_width=True):
    if not user_input.strip():
        st.warning("Please enter a story idea first!")
    else:
        st.session_state.request = user_input
        st.session_state.previous_story = None
        st.session_state.previous_score = None
        st.session_state.has_changes = False
        st.session_state.show_original = False

        with st.spinner("Detecting story type..."):
            category = categorize_request(user_input)
            st.session_state.category = category

        with st.spinner(f"Writing your {category} story..."):
            story = generate_story(user_input, category)

        with st.spinner("Checking story quality..."):
            score, feedback = judge_story(story, user_input)

        if score < 7:
            with st.spinner(f"Score was {score}/10 — improving the story..."):
                story = improve_story(story, feedback, user_input, category)
                score, feedback = judge_story(story, user_input)

        st.session_state.story = story
        st.session_state.score = score
        st.session_state.feedback = feedback

# ── display story ─────────────────────────────────────────
if st.session_state.story:
    st.divider()

    # show category badge
    if st.session_state.category:
        cat = CATEGORIES[st.session_state.category]
        st.markdown(
            f'<div class="category-badge">{cat["emoji"]} {st.session_state.category} Story</div>',
            unsafe_allow_html=True
        )

    # before/after toggle
    if st.session_state.has_changes:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button(
                "📖 Updated Story",
                use_container_width=True,
                type="primary" if not st.session_state.show_original else "secondary"
            ):
                st.session_state.show_original = False
                st.rerun()
        with col_b:
            if st.button(
                "📜 Original Story",
                use_container_width=True,
                type="primary" if st.session_state.show_original else "secondary"
            ):
                st.session_state.show_original = True
                st.rerun()

    # show correct story
    if st.session_state.show_original and st.session_state.previous_story:
        st.subheader("📜 Original Story")
        st.markdown(
            f'<div class="story-box-old">{st.session_state.previous_story}</div>',
            unsafe_allow_html=True
        )
        st.divider()
        st.subheader("⚖️ Original Judge Score")
        prev_score = st.session_state.previous_score
        color_class = "score-good" if prev_score >= 7 else "score-bad"
        st.markdown(
            f'<p class="{color_class}">Score: {prev_score}/10</p>',
            unsafe_allow_html=True
        )
        st.progress(prev_score / 10)

    else:
        st.subheader("📖 Your Story")
        st.markdown(
            f'<div class="story-box">{st.session_state.story}</div>',
            unsafe_allow_html=True
        )
        st.divider()
        st.subheader("⚖️ Judge's Verdict")
        score = st.session_state.score
        color_class = "score-good" if score >= 7 else "score-bad"
        st.markdown(
            f'<p class="{color_class}">Score: {score}/10</p>',
            unsafe_allow_html=True
        )
        st.progress(score / 10)
        st.markdown(
            f'<div class="feedback-box">{st.session_state.feedback}</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.subheader("💬 Request Changes")
    change_request = st.text_input(
        "Want to change anything?",
        placeholder="e.g. Make it funnier, add a friend for the dragon..."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Apply Changes", use_container_width=True):
            if change_request.strip():
                st.session_state.previous_story = st.session_state.story
                st.session_state.previous_score = st.session_state.score

                with st.spinner("Updating your story..."):
                    new_story = improve_story(
                        st.session_state.story,
                        change_request,
                        st.session_state.request,
                        st.session_state.category
                    )
                    new_score, new_feedback = judge_story(
                        new_story,
                        st.session_state.request
                    )

                st.session_state.story = new_story
                st.session_state.score = new_score
                st.session_state.feedback = new_feedback
                st.session_state.has_changes = True
                st.session_state.show_original = False
                st.rerun()
            else:
                st.warning("Please type what you'd like to change!")

    with col2:
        if st.button("🌙 Done — Sweet Dreams!", use_container_width=True):
            st.balloons()
            st.success("Sweet dreams! 🌙 Goodnight!")
            for key in defaults:
                st.session_state[key] = defaults[key]

    # success message below buttons
    if st.session_state.has_changes and not st.session_state.show_original:
        st.success("✅ Story updated! Use the toggle above to compare with the original.")