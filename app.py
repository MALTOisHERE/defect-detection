import json
import os
import random
import time
import math
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import datetime

from model import model_predict

app = Flask(__name__)
app.secret_key = 'supersecretkey_shine' # Make it unique!

# --- Configuration ---
UPLOAD_FOLDER = os.path.join('static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATA_FILE = os.path.join('data', 'image_data.json')

# --- Constants ---
RESULTS_PER_PAGE = 10

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Warning: {DATA_FILE} not found. Starting with empty data.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {DATA_FILE}. Check file format.")
        return []

def save_data(data):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False) # ensure_ascii=False good for potential non-English chars later
    except IOError as e:
        print(f"Error saving data to {DATA_FILE}: {e}")

@app.context_processor
def inject_current_year():
    """Injects the current year into all templates."""
    return dict(current_year=datetime.datetime.now().year)

# --- Routes ---

@app.route('/')
def index():
    image_data_list = load_data()
    next_image = None
    pending_count = 0
    for image in image_data_list:
        if not image.get('feedback_provided', False):
            pending_count += 1
            if next_image is None: # Find the first non-validated
                 next_image = image

    # Prepare stats for the index page
    total_images = len(image_data_list)
    validated_count = total_images - pending_count

    if next_image:
        # Inject some context/stats into the validation page itself
        return render_template('index.html',
                               image_data=next_image,
                               pending_count=pending_count,
                               validated_count=validated_count,
                               total_images=total_images)
    else:
        # If no image needs validation, show the 'all validated' page
        return render_template('all_validated.html', total_images=total_images)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    image_id = int(request.form.get('image_id'))
    validation_status = request.form.get('validation_status')
    inspector_comment = request.form.get('inspector_comment', '').strip()
    image_data_list = load_data()
    image_to_update = None
    image_index = -1
    for i, img in enumerate(image_data_list):
        if img.get('id') == image_id: # Use .get for safety
            image_to_update = img
            image_index = i
            break

    if not image_to_update:
        flash(f"Critical Error: Image {image_id} not found!", "danger")
        return redirect(url_for('index'))

    # --- Update Logic ---
    if validation_status == 'correct':
        image_to_update['actual_class'] = image_to_update['predicted_class']
    elif validation_status == 'incorrect':
        actual_class = request.form.get('actual_class')
        # ** NOTE: Ensure 'actual_class' from the form sends "Defect" or "No Defect" **
        if not actual_class:
            flash("Required Field: Please select the correct class when marking as incorrect.", "warning")
             # Re-render index, passing needed context data again
            pending_count = sum(1 for img in image_data_list if not img.get('feedback_provided', False))
            total_images = len(image_data_list)
            validated_count = total_images - pending_count
            return render_template('index.html',
                                   image_data=image_to_update,
                                   pending_count=pending_count,
                                   validated_count=validated_count,
                                   total_images=total_images,
                                   validation_error=True) # Flag can be used in template if needed
        image_to_update['actual_class'] = actual_class
    else:
        flash("System Error: Unknown validation status received.", "danger")
        return redirect(url_for('index'))

    image_to_update['feedback_provided'] = True
    image_to_update['inspector_comment'] = inspector_comment
    image_data_list[image_index] = image_to_update
    save_data(image_data_list)
    flash(f"Validation for image #{image_id} saved. Great catch!", "success")
    return redirect(url_for('index'))


@app.route('/results')
def view_results():
    all_data = load_data()
    page = request.args.get('page', 1, type=int)
    if page < 1: page = 1
    all_data.sort(key=lambda x: x.get('id', 0), reverse=True) # Sort newest first
    total_items = len(all_data)
    total_pages = math.ceil(total_items / RESULTS_PER_PAGE)
    if page > total_pages and total_pages > 0: page = total_pages
    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    images_on_page = all_data[start_index:end_index]

    # --- Calculate Stats for Chart/Summary ---
    validated_data = [img for img in all_data if img.get('feedback_provided')]
    validation_counts = Counter(img.get('actual_class') for img in validated_data if img.get('actual_class'))
    prediction_counts = Counter(img.get('predicted_class') for img in all_data if img.get('predicted_class'))

    # Prepare data safe for JSON serialization and chart rendering
    chart_data = {
        "validated_labels": list(validation_counts.keys()),
        "validated_values": list(validation_counts.values()),
        "predicted_labels": list(prediction_counts.keys()),
        "predicted_values": list(prediction_counts.values()),
    }
    validated_count = len(validated_data)
    pending_count = total_items - validated_count

    return render_template(
        'results.html',
        images=images_on_page,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        validated_count=validated_count,
        pending_count=pending_count,
        chart_data=chart_data
    )

@app.route('/upload', methods=['GET'], endpoint='show_upload_form')
def show_upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'], endpoint='upload_image')
def upload_image():
    if 'image_file' not in request.files:
        flash('No file selected in the request.', 'warning')
        return redirect(url_for('show_upload_form'))
    file = request.files['image_file']
    if file.filename == '':
        flash('No image file selected.', 'warning')
        return redirect(url_for('show_upload_form'))

    if file and allowed_file(file.filename):
        try:
            original_filename = secure_filename(file.filename)
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{original_filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)

            # Predict
            if model_predict("./static/images/" + unique_filename):
                predicted_class = "Defect"
            else:
                predicted_class = "No Defect"


            image_data_list = load_data()
            next_id = max((item.get('id', 0) for item in image_data_list), default=0) + 1

            new_image_entry = {
                "id": next_id,
                "filename": unique_filename,
                "predicted_class": predicted_class,
                "actual_class": None,
                "feedback_provided": False,
                "inspector_comment": None
            }
            image_data_list.append(new_image_entry)
            save_data(image_data_list)
            flash(f'\'{original_filename}\' uploaded. Prediction: {predicted_class}. Ready for inspection!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            print(f"Error during upload: {e}")
            flash('An internal error occurred during processing.', 'danger')
            return redirect(url_for('show_upload_form'))
    else:
        flash('Unsupported file format. Please use PNG, JPG, JPEG, or GIF.', 'warning')
        return redirect(url_for('show_upload_form'))

# Add this at the very end
if __name__ == '__main__':
    app.run(debug=True)
