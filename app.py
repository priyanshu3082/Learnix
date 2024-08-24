import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from workers import pdf2text, txt2questions
import requests

# Constants
UPLOAD_FOLDER = './pdf/'

# Set the environment variable directly in the script
os.environ['GOOGLE_GENERATIVE_LANGUAGE_API_KEY'] = "AIzaSyDtwXpyTqSWebj2TM6L4_9gQa6LOzmYQnw"

# Load the API Key from the environment variable
API_KEY = os.getenv('GOOGLE_GENERATIVE_LANGUAGE_API_KEY')
print(f"API Key: {API_KEY}")

if not API_KEY:
    raise ValueError("API Key not found. Please set the GOOGLE_GENERATIVE_LANGUAGE_API_KEY environment variable.")

# Init an app object
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    """ The landing page for the app """
    return render_template('index.html')


# Function to call Google Generative Language API
def generate_questions(text):
    url = f"https://generativelanguage.googleapis.com/v1beta2/text:generate?key={API_KEY}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        'prompt': {
            'text': text
        },
        'maxOutputTokens': 150,  # Adjust based on your needs
        'temperature': 0.7,  # Adjust for creativity
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"API Status Code: {response.status_code}")
    print(f"API Response: {response.json()}")  # Print the full response for debugging
    
    if response.status_code == 200:
        return response.json().get('text', '')
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


def txt2questions(text_content):
    """Generate quiz questions from the extracted text using Google API"""
    generated_text = generate_questions(text_content)
    
    # Here you can parse the generated text into a dictionary of questions
    questions = {}
    if generated_text:
        # Example of splitting questions if they are separated by new lines
        for i, question in enumerate(generated_text.split('\n')):
            questions[f'Q{i+1}'] = question.strip()
    
    return questions

def save_file(uploaded_file):
    """Save the uploaded file to the upload folder and return its path."""
    if not os.path.isdir(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
    uploaded_file.save(file_path)
    return file_path


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    UPLOAD_STATUS = False
    questions = dict()

    if request.method == 'POST':
        try:
            # Retrieve and save file
            uploaded_file = request.files['file']
            file_path = save_file(uploaded_file)
            file_exten = uploaded_file.filename.rsplit('.', 1)[1].lower()

            # Process file content and generate questions
            uploaded_content = pdf2text(file_path, file_exten)
            questions = txt2questions(uploaded_content)

            # File upload + convert success
            if uploaded_content is not None:
                UPLOAD_STATUS = True
        except Exception as e:
            print(f"Error processing file: {e}")

    return render_template('quiz.html', uploaded=UPLOAD_STATUS, questions=questions, size=len(questions))


@app.route('/result', methods=['POST', 'GET'])
def result():
    correct_q = 0
    for k, v in request.form.items():
        correct_q += 1
    return render_template('result.html', total=5, correct=correct_q)


if __name__ == "__main__":
    app.run(debug=True)
