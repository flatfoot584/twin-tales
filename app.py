
# twin_tales_app/app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from fpdf import FPDF
import os
import json
import base64
import random

# -----------------------------
# 🔧 App Configuration
# -----------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# -----------------------------
# 📚 Story Management
# -----------------------------
STORY_FILE = 'story_data.json'

if os.path.exists(STORY_FILE):
    with open(STORY_FILE, 'r') as f:
        story = json.load(f)
else:
    story = {}

def save_story():
    with open(STORY_FILE, 'w') as f:
        json.dump(story, f, indent=4)

# -----------------------------
# 🏠 Homepage
# -----------------------------
@app.route('/')
def home():
    return render_template("home.html", show_nav=False)

# -----------------------------
# 📖 View Story Page
# -----------------------------
@app.route('/story/<page>')
def show_page(page):
    data = story.get(page, {"text": "The End.", "image": "", "choices": {}})
    audio_dir = 'static/audio'
    audio_files = os.listdir(audio_dir) if os.path.exists(audio_dir) else []

    character = None
    if os.path.exists("characters.json"):
        with open("characters.json", "r") as f:
            characters = json.load(f)
        character = characters.get(page)

    return render_template("page.html", text=data["text"], image=data.get("image", ""),
                           choices=data["choices"], page=page, audio_files=audio_files,
                           character=character)

# -----------------------------
# ➕ Create Story Page
# -----------------------------
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        image_filename = ""

        # Check for drawing or uploaded image
        drawing_choice = request.form.get('drawing_choice')
        if drawing_choice:
            image_filename = drawing_choice
        else:
            image_file = request.files.get('image')
            if image_file and image_file.filename != '':
                image_filename = secure_filename(image_file.filename)
                image_path = os.path.join("static/images", image_filename)
                image_file.save(image_path)

        # Save choices
        choices = {}
        if request.form.get('choice1_text') and request.form.get('choice1_dest'):
            choices[request.form['choice1_text']] = request.form['choice1_dest']
        if request.form.get('choice2_text') and request.form.get('choice2_dest'):
            choices[request.form['choice2_text']] = request.form['choice2_dest']

        story[title] = {
            "text": text,
            "choices": choices,
            "image": image_filename if image_filename else None
        }

        save_story()
        return redirect(url_for('show_page', page=title))

    drawing_files = [
        f for f in os.listdir('static/images')
        if f.startswith('drawing_') and f.endswith('.png')
    ]
    return render_template("create.html", drawings=drawing_files)

# -----------------------------
# 🎨 Drawing Canvas
# -----------------------------
@app.route('/draw')
def draw():
    return render_template("draw.html")

@app.route('/save_drawing', methods=['POST'])
def save_drawing():
    drawing_data = request.form['drawing']
    drawing_data = drawing_data.replace("data:image/png;base64,", "")
    image_data = base64.b64decode(drawing_data)

    drawing_dir = 'static/images'
    os.makedirs(drawing_dir, exist_ok=True)
    count = len([f for f in os.listdir(drawing_dir) if f.startswith('drawing_')])
    filename = f'drawing_{count+1}.png'
    path = os.path.join(drawing_dir, filename)

    with open(path, 'wb') as f:
        f.write(image_data)

    return jsonify({"success": True, "filename": filename})

@app.route('/drawings')
def drawings():
    drawing_dir = 'static/images'
    drawings = [
        f for f in os.listdir(drawing_dir)
        if f.startswith('drawing_') and f.endswith('.png')
    ]
    return render_template("gallery.html", drawings=drawings)

# -----------------------------
# ✏️ Write Your Own Story
# -----------------------------
@app.route('/write_story', methods=['GET', 'POST'])
def write_story():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        story_dir = 'written_stories'
        os.makedirs(story_dir, exist_ok=True)

        filename = f"{secure_filename(title)}.txt"
        with open(os.path.join(story_dir, filename), 'w', encoding='utf-8') as f:
            f.write(body)

        return render_template("write_story.html", message="✅ Story saved!")

    return render_template("write_story.html")

@app.route('/view_written_stories')
def view_written_stories():
    story_dir = 'written_stories'
    stories = [f for f in os.listdir(story_dir) if f.endswith('.txt')] if os.path.exists(story_dir) else []
    return render_template("view_stories.html", stories=stories)

@app.route('/read_story/<story_name>')
def read_story(story_name):
    story_path = os.path.join("written_stories", story_name)
    if os.path.exists(story_path):
        with open(story_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template("read_story.html", content=content, story_name=story_name)
    return "Story not found", 404

# -----------------------------
# 🎤 Record Narration
# -----------------------------
@app.route('/record/<page_name>')
def record_narration(page_name):
    return render_template("record.html", page_name=page_name)

@app.route('/save_narration/<page_name>', methods=['POST'])
def save_narration(page_name):
    audio = request.files['audio']
    filename = f"{secure_filename(page_name)}.wav"
    audio_path = os.path.join("static/audio", filename)
    os.makedirs("static/audio", exist_ok=True)
    audio.save(audio_path)
    return jsonify({"success": True, "filename": filename})

# -----------------------------
# 📸 Add Characters
# -----------------------------
@app.route('/add_character', methods=['GET', 'POST'])
def add_character():
    if request.method == 'POST':
        name = request.form['name']
        page = request.form['page']
        photo = request.files['photo']

        if photo and name and page:
            filename = secure_filename(photo.filename)
            filepath = os.path.join("static/characters", filename)
            os.makedirs("static/characters", exist_ok=True)
            photo.save(filepath)

            characters = {}
            if os.path.exists("characters.json"):
                with open("characters.json", "r") as f:
                    characters = json.load(f)

            characters[page] = {"name": name, "photo": filename}
            with open("characters.json", "w") as f:
                json.dump(characters, f, indent=4)

            return redirect(url_for('show_page', page=page))

    return render_template("add_character.html")

# -----------------------------
# 🎲 Magic Story Generator
# -----------------------------
@app.route('/magic_story', methods=['GET', 'POST'])
def magic_story():
    if request.method == 'POST':
        if 'surprise' in request.form:
            name = random.choice(['Harper', 'Emerie', 'Ziggy', 'Sparkle'])
            object_ = random.choice(['crystal wand', 'glowing banana', 'fuzzy compass', 'magic sock'])
            creature = random.choice(['unicorn', 'robot-dolphin', 'silly dragon', 'talking cat'])
            place = random.choice(['Rainbow Mountain', 'Glitter Forest', 'Bubble Cavern', 'Pancake Planet'])
            problem = random.choice(['the giggle storm', 'a giant sneeze', 'tickle tornado', 'jelly flood'])

            return render_template("magic_story.html", form=True, name=name, object=object_,
                                   creature=creature, place=place, problem=problem)

        name = request.form['name']
        object_ = request.form['object']
        creature = request.form['creature']
        place = request.form['place']
        problem = request.form['problem']

        story_text = (
            f"One day, {name} found a mysterious {object_} hidden inside a tree.\n"
            f"When they picked it up, a {creature} appeared and said, \"You must bring this to the {place}!\"\n"
            f"{name} was nervous, but brave. They traveled through fog and thunder, facing the great {problem}.\n"
            f"In the end, they used the {object_} to save the day, and made a new friend: the {creature}!"
        )

        title = f"magic_story_{name}".replace(" ", "_")
        os.makedirs("written_stories", exist_ok=True)
        with open(f"written_stories/{title}.txt", "w", encoding="utf-8") as f:
            f.write(story_text)

        os.makedirs("static/storybooks", exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        for line in story_text.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf.output(f"static/storybooks/{title}.pdf")

        return render_template("magic_story.html", form=False, story=story_text, pdf_filename=title + ".pdf")

    return render_template("magic_story.html", form=True)

# -----------------------------
# 📕 Export Full Storybook
# -----------------------------
@app.route('/export_pdf')
def export_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for key, page in story.items():
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.multi_cell(0, 10, f"Page: {key}\n\n{page['text']}\n")
        for label, dest in page.get("choices", {}).items():
            pdf.cell(0, 10, f"Choice: {label} -> {dest}", ln=True)
        if page.get("image"):
            image_path = os.path.join("static/images", page["image"])
            if os.path.exists(image_path):
                pdf.image(image_path, x=10, y=None, w=100)

    output_path = "static/storybook.pdf"
    pdf.output(output_path)
    return redirect(url_for('static', filename='storybook.pdf'))

# -----------------------------
# 🚀 Run App
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

