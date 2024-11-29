import json
from flask import Flask, render_template, request, url_for, redirect
import os
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_image_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            metadata = {}
            # Basic image metadata
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = f"{img.size[0]}x{img.size[1]}"

            # Extract all metadata from image info
            for key, value in img.info.items():
                # Special handling for AI-related metadata
                if key.lower() in ['parameters', 'prompt', 'negative_prompt', 'seed', 
                                 'model', 'pipeline', 'steps', 'cfg_scale', 'sampler']:
                    metadata[key] = value
                # Handle potential JSON metadata
                elif isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        metadata[key] = json.loads(value)
                    except:
                        metadata[key] = value
                else:
                    metadata[key] = value

            # Try to get EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif.get(tag_id)
                    if isinstance(data, bytes):
                        try:
                            data = data.decode()
                        except:
                            data = str(data)
                    metadata[f"EXIF_{tag}"] = data

            return metadata
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return {}

def compare_nested_objects(obj1, obj2, parent_key=""):
    differences = {}
    
    # Try to parse JSON strings
    def parse_json(obj):
        if isinstance(obj, str):
            try:
                return json.loads(obj)
            except:
                return obj
        return obj
    
    obj1 = parse_json(obj1)
    obj2 = parse_json(obj2)
    
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in all_keys:
            new_key = f"{parent_key}.{key}" if parent_key else key
            val1 = parse_json(obj1.get(key))
            val2 = parse_json(obj2.get(key))
            
            if val1 != val2:
                if (isinstance(val1, (dict, list)) and isinstance(val2, (dict, list))) or \
                   (isinstance(val1, str) and isinstance(val2, str) and 
                    (val1.startswith('{') or val1.startswith('[')) and 
                    (val2.startswith('{') or val2.startswith('['))):
                    nested_diff = compare_nested_objects(val1, val2, new_key)
                    differences.update(nested_diff)
                else:
                    # Convert complex objects to string representation
                    if not isinstance(val1, (str, int, float, bool, type(None))):
                        val1 = str(val1)
                    if not isinstance(val2, (str, int, float, bool, type(None))):
                        val2 = str(val2)
                    differences[new_key] = {
                        'image1': val1,
                        'image2': val2
                    }
    elif isinstance(obj1, list) and isinstance(obj2, list):
        for i, (item1, item2) in enumerate(zip(obj1, obj2)):
            if item1 != item2:
                new_key = f"{parent_key}[{i}]"
                if isinstance(item1, (dict, list)) or isinstance(item2, (dict, list)):
                    nested_diff = compare_nested_objects(item1, item2, new_key)
                    differences.update(nested_diff)
                else:
                    differences[new_key] = {
                        'image1': item1,
                        'image2': item2
                    }
    
    return differences

def compare_metadata(metadata1, metadata2):
    return compare_nested_objects(metadata1, metadata2)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get list of uploaded images
    uploaded_images = []
    default_images = [
        {
            'url': 'https://images.unsplash.com/photo-1674647325071-49a139b1f495',
            'author': 'Dmitry Bukhantsov',
            'position': 'top-left',
            'filename': 'winter_scene.jpg'
        },
        {
            'url': 'https://images.unsplash.com/photo-1674647812339-dbcf20a9d268',
            'author': 'Dmitry Bukhantsov',
            'position': 'top-right',
            'filename': 'snowy_landscape.jpg'
        },
        {
            'url': 'https://images.unsplash.com/photo-1626238247302-2f3065c90ff5',
            'author': 'Fareed Akhyear Chowdhury',
            'position': 'bottom-left',
            'filename': 'summer_beach.jpg'
        },
        {
            'url': 'https://images.unsplash.com/photo-1731534679636-86d1d0c64198',
            'author': 'Atif Haiqal',
            'position': 'bottom-right',
            'filename': 'sunset_view.jpg'
        }
    ]
    
    # Check for uploaded images
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        for i, filename in enumerate(files[:4]):  # Only take first 4 images
            position = ['top-left', 'top-right', 'bottom-left', 'bottom-right'][i]
            uploaded_images.append({
                'url': url_for('static', filename=f'uploads/{filename}'),
                'author': 'User Upload',
                'position': position,
                'filename': filename
            })
    
    # Use uploaded images if available, otherwise use defaults
    images = uploaded_images if uploaded_images else default_images
    
    # Compare metadata if images exist in uploads folder
    metadata_diff = None
    if uploaded_images:
        # Compare first two uploaded images if available
        if len(uploaded_images) >= 2:
            image1_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(uploaded_images[0]['url']))
            image2_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(uploaded_images[1]['url']))
            
            if os.path.exists(image1_path) and os.path.exists(image2_path):
                metadata1 = get_image_metadata(image1_path)
                metadata2 = get_image_metadata(image2_path)
                
                # Filter and organize metadata differences
                raw_diff = compare_metadata(metadata1, metadata2)
                metadata_diff = {}
                
                # Categorize differences
                for key, value in raw_diff.items():
                    category = 'AI Parameters'
                    if key.startswith('EXIF'):
                        category = 'EXIF Data'
                    elif key in ['format', 'mode', 'size']:
                        category = 'Basic Info'
                    elif 'parameters' in key.lower() or 'prompt' in key.lower() or 'model' in key.lower():
                        category = 'AI Parameters'
                    else:
                        category = 'Other Metadata'
                    
                    if category not in metadata_diff:
                        metadata_diff[category] = {}
                    metadata_diff[category][key] = value
    
    return render_template('index.html', images=images, metadata_diff=metadata_diff)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    # Clear existing uploads
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    for file in files[:4]:  # Only process first 4 files
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return redirect(url_for('index'))
