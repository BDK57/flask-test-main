from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import time
import cv2
import numpy as np
import concurrent.futures

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = os.path.abspath('public/assets/uploaded_images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def create_upload_folder():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def stitch_images(imgs):
    print("Stitching images...")
    start_time = time.time()
    mode = cv2.STITCHER_PANORAMA

    if int(cv2.__version__[0]) == 3:
        stitcher = cv2.createStitcher(mode)
    else:
        stitcher = cv2.Stitcher_create(mode)

    status, stitched = stitcher.stitch(imgs)

    end_time = time.time()

    if status == 0:
        return stitched, ((end_time - start_time) / 60)
    else:
        raise Exception('Failed to stitch images. Status: %s' % status)

@app.route('/')
def start():
    return "The MBSA Server is Running"

@app.route('/mbsa')
def mbsa():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_images():
    print("Accepting images...")

    create_upload_folder()

    uploaded_files = request.files.getlist("files[]")
    uploaded_file_paths = []

    upload_session_id = str(int(time.time()))
    upload_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_session_id)
    os.makedirs(upload_folder_path)

    for file in uploaded_files:
        file_path = os.path.join(upload_folder_path, file.filename)
        file.save(file_path)
        uploaded_file_paths.append(file_path)

    try:
        imgs = [cv2.imread(img_path) for img_path in uploaded_file_paths]

        # Process and stitch images using multiprocessing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(stitch_images, imgs)
            stitched, execution_time = future.result()
        print(upload_folder_path)
        cv2.imwrite(os.path.join(upload_folder_path, 'result_new.jpg'), stitched)
        print("Image processing completed.")
        return jsonify({'folder': upload_folder_path, 'execution_time': execution_time, 'folder_name': upload_session_id})
    except Exception as e:
        error_message = str(e)
        print("Error:", error_message)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
