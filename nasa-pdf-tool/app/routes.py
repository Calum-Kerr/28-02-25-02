# app/routes.py
"""
Main routes for the NASA PDF Tool.
Handles file upload, text extraction, editing, and saving of PDFs,
all built following NASA's strict coding and security guidelines.
"""

import os
import uuid
import json
import threading
from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_file, flash
from werkzeug.utils import secure_filename
from app.pdf_processing import extract_text_from_pdf, apply_text_edits_to_pdf
from app.utils import schedule_file_deletion

# Specify the template folder relative to this file (../templates)
main = Blueprint('main', __name__, template_folder='../templates')

def allowed_file(filename):
    """
    Check if the uploaded file has a valid PDF extension.
    
    :param filename: Name of the file provided by the user.
    :return: True if file is a PDF, otherwise False.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@main.route('/', methods=['GET'])
def index():
    """
    Render the index page with basic instructions.
    """
    return render_template('index.html')

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Handle the file upload process:
    - Validates the uploaded file.
    - Saves it securely with a unique identifier.
    - Extracts text and associated metadata.
    - Schedules auto-deletion for both the PDF and its extraction data.
    - Redirects the user to the editing page.
    """
    if request.method == 'POST':
        # Ensure the 'pdf_file' field is present
        if 'pdf_file' not in request.files:
            flash('No file part in the request.')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            flash('No file selected for uploading.')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure the filename and create a unique identifier
            original_filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            new_filename = f"{unique_id}.pdf"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
            
            try:
                # Save the uploaded PDF file
                file.save(file_path)
            except Exception as e:
                current_app.logger.error(f"Error saving file: {e}")
                flash("Failed to save the uploaded file.")
                return redirect(request.url)
            
            # Schedule auto-deletion of the file after the configured retention time
            schedule_file_deletion(file_path, current_app.config['FILE_RETENTION_TIME'])
            
            # Extract text and metadata from the PDF
            try:
                extraction_result = extract_text_from_pdf(file_path)
                # Save the extraction data as a JSON file for use in the editing interface
                json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}.json")
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(extraction_result, json_file)
                # Schedule deletion of the JSON file as well
                schedule_file_deletion(json_path, current_app.config['FILE_RETENTION_TIME'])
            except Exception as e:
                current_app.logger.error(f"Error extracting text: {e}")
                flash("Failed to process the uploaded PDF file.")
                return redirect(request.url)
            
            # Redirect the user to the editing page, passing the unique file id
            return redirect(url_for('main.edit', file_id=unique_id))
        else:
            flash('Invalid file type. Please upload a PDF file.')
            return redirect(request.url)
    
    # If GET, render the upload page
    return render_template('upload.html')

@main.route('/edit/<file_id>', methods=['GET'])
def edit(file_id):
    """
    Display the editing interface.
    Loads the extracted text from the corresponding JSON file
    and passes it to the edit template.
    
    :param file_id: Unique identifier for the uploaded PDF file.
    """
    json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}.json")
    
    if not os.path.exists(json_path):
        flash("The requested file does not exist or has expired.")
        return redirect(url_for('main.index'))
    
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            extraction_result = json.load(json_file)
    except Exception as e:
        current_app.logger.error(f"Error loading extraction data: {e}")
        flash("Failed to load file data for editing.")
        return redirect(url_for('main.index'))
    
    # Render the editing page, passing the file id and extracted content
    return render_template('edit.html', file_id=file_id, extraction=extraction_result)

@main.route('/save/<file_id>', methods=['POST'])
def save(file_id):
    """
    Process the edited text and generate a new PDF:
    - Retrieves edits from the form (expects JSON data in the 'edits' field).
    - Applies text edits to the original PDF using extracted metadata.
    - Returns the modified PDF as a file download.
    
    :param file_id: Unique identifier for the uploaded PDF file.
    """
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}.pdf")
    
    if not os.path.exists(pdf_path):
        flash("Original PDF file not found or has expired.")
        return redirect(url_for('main.index'))
    
    try:
        # Expecting a JSON string of edits from the form
        edits_json = request.form.get('edits')
        if not edits_json:
            flash("No edits provided.")
            return redirect(url_for('main.edit', file_id=file_id))
        
        edits = json.loads(edits_json)
    except Exception as e:
        current_app.logger.error(f"Error parsing edits: {e}")
        flash("Invalid edit data.")
        return redirect(url_for('main.edit', file_id=file_id))
    
    try:
        # Apply text edits to the PDF and obtain modified PDF bytes
        modified_pdf_bytes = apply_text_edits_to_pdf(pdf_path, edits)
    except Exception as e:
        current_app.logger.error(f"Error applying text edits: {e}")
        flash("Failed to save edited PDF.")
        return redirect(url_for('main.edit', file_id=file_id))
    
    # Serve the modified PDF for download using BytesIO
    from io import BytesIO
    pdf_io = BytesIO(modified_pdf_bytes)
    pdf_io.seek(0)
    
    # Generate a secure download filename
    download_filename = f"edited_{file_id}.pdf"
    return send_file(pdf_io, as_attachment=True, download_name=download_filename, mimetype='application/pdf')