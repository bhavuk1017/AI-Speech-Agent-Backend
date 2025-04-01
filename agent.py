from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import os
from groq import Groq
from dotenv import load_dotenv  # Added environment loader

# Load environment variables first
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize clients
api_key=os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.examdb

def store_exam_details(student_name, subject, topic, score, cheated, entry_time):
    try:
        db.exam_results.insert_one({
            "student_name": student_name,
            "subject": subject,
            "topic": topic,
            "score": score,
            "cheated": cheated,
            "entry_time": entry_time
        })
    except Exception as e:
        print("Error storing exam details:", e)

def evaluate_answer_ai(question1, answer1, question2, answer2, question3, answer3, question4, answer4):
    prompt = f"""
    You are an educational AI assistant evaluating a student's answers.
    Evaluate these responses:

    Question 1: {question1}
    Answer 1: {answer1}

    Question 2: {question2}
    Answer 2: {answer2}

    Question 3: {question3}
    Answer 3: {answer3}

    Question 4: {question4}
    Answer 4: {answer4}

    Scoring (100 points total):
    1. Topic Understanding (25 points): Does Answer 1 show deep understanding?
    2. Real-Time Focus (25 points): Does Answer 2 mention immediate/live applications?
    3. Technology Impact (25 points): Does Answer 3 explain modern tech impact?
    4. Challenges (25 points): Does Answer 4 identify specific implementation challenges?

    Provide feedback in this format:
    Score: [total score]
    Topic Understanding: [feedback on Answer 1]
    Real-Time Applications: [feedback on Answer 2]
    Technology Impact: [feedback on Answer 3]
    Challenges: [feedback on Answer 4]
    Overall: [summary feedback]
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Score: 0\nError: {str(e)}"

@app.route('/evaluate-answer', methods=['POST'])
def evaluate():
    try:
        data = request.json
        feedback = evaluate_answer_ai(
            data['question1'], data['answer1'],
            data['question2'], data['answer2'],
            data['question3'], data['answer3'],
            data['question4'], data['answer4']
        )
        return jsonify({"feedback": feedback})
    except Exception as e:
        return jsonify({"feedback": f"Score: 0\nError: {str(e)}"}), 500

@app.route('/store-exam-result', methods=['POST'])
def store_exam_result():
    try:
        data = request.json
        store_exam_details(
            data['student_name'],
            data['subject'],
            data['topic'],
            data['score'],
            data.get('cheated', False),
            data.get('entry_time', datetime.datetime.now().isoformat())
        )
        return jsonify({"message": "Exam result stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-keywords', methods=['POST'])
def extract_keywords():
    try:
        data = request.json
        text = data['text']
        words = text.lower().split()
        stop_words = {'a', 'an', 'the', 'is', 'are', 'in', 'on', 'to', 'for', 'with', 'about', 'of'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3][:2]
        return jsonify({"keywords": keywords})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
