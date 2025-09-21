import streamlit as st
import os
import re
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Title
st.title("QuizGenie 🎯")

# Load API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API key not found. Please check your .env file.")
    st.stop()
else:
    client = Groq(api_key=api_key)
    st.success("API key loaded successfully!")

# Supported model
MODEL = "llama-3.1-8b-instant"

# Subject input
subject = st.text_input("Enter a topic (e.g., Digital Electronics, Microcontrollers, Analog Circuits):")

# Quiz length input
quiz_length = st.radio("Select number of questions:", [5, 10], index=0)

# Initialize session state
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "quiz_complete" not in st.session_state:
    st.session_state.quiz_complete = False

# Generate quiz
if st.button("Generate Quiz"):
    if not subject:
        st.warning("Please enter a topic first!")
    else:
        with st.spinner("Generating quiz..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a quiz generator for electronics engineering. "
                                f"Generate exactly {quiz_length} MCQs with exactly 4 options each (A, B, C, D). "
                                f"Clearly mark the correct answer with '(Answer: X)'. "
                                "Do NOT add explanations."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Generate a quiz on topic: {subject}"
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1200 if quiz_length == 10 else 700,
                )

                quiz_text = response.choices[0].message.content

                # Parse questions
                questions = re.split(r"\n\d+\.", quiz_text)
                parsed_quiz = []
                for q in questions[1:]:
                    lines = [line.strip() for line in q.strip().split("\n") if line.strip()]
                    if not lines:
                        continue

                    question = lines[0]
                    options = []
                    correct = None

                    for line in lines[1:]:
                        if "(Answer:" in line:
                            correct = line.split("(Answer:")[1].replace(")", "").strip()
                            option_text = line.split("(Answer:")[0].strip()
                            options.append(option_text)
                        else:
                            options.append(line)

                    # Keep only 4 options
                    options = options[:4]

                    parsed_quiz.append({"question": question, "options": options, "answer": correct})

                st.session_state.quiz_data = parsed_quiz
                st.session_state.user_answers = {}
                st.session_state.current_q = 0
                st.session_state.quiz_complete = False

            except Exception as e:
                st.error(f"Failed to generate quiz: {e}")

# Display quiz if available
if st.session_state.quiz_data and not st.session_state.quiz_complete:
    q_index = st.session_state.current_q
    q = st.session_state.quiz_data[q_index]

    st.subheader(f"Quiz on {subject} ({quiz_length} Questions)")
    st.write(f"**Q{q_index+1}: {q['question']}**")

    st.session_state.user_answers[q_index] = st.radio(
        f"Select your answer for Q{q_index+1}:",
        q["options"],
        index=None,
        key=f"q{q_index+1}"
    )

    col1, col2 = st.columns(2)

    if q_index < len(st.session_state.quiz_data) - 1:
        if col1.button("Next Question ➡️"):
            st.session_state.current_q += 1
            st.rerun()
    else:
        if col1.button("Submit Quiz ✅"):
            st.session_state.quiz_complete = True
            st.rerun()

# Show results after submission
if st.session_state.quiz_complete:
    score = 0
    st.subheader("📊 Quiz Results")

    for i, q in enumerate(st.session_state.quiz_data):
        user_ans = st.session_state.user_answers.get(i)
        correct_ans = None

        # Convert letter (A/B/C/D) to actual option text
        if q["answer"] and q["answer"].upper() in ["A", "B", "C", "D"]:
            idx = ord(q["answer"].upper()) - 65
            if idx < len(q["options"]):
                correct_ans = q["options"][idx]

        if user_ans == correct_ans:
            score += 1
            st.success(f"✅ Q{i+1}: Correct")
        else:
            st.error(f"❌ Q{i+1}: Wrong (Correct: {correct_ans})")

    st.info(f"Your final score: {score}/{len(st.session_state.quiz_data)}")
