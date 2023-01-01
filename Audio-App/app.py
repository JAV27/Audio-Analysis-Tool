from flask import Flask, render_template, request, flash, redirect, url_for
from packages import vad
from werkzeug.utils import secure_filename
import os 
from pydub import AudioSegment
import numpy as np
import json
import pandas as pd
from time import sleep

app = Flask(__name__)
app.secret_key = "super secret key"
UPLOAD_FOLDER = 'static/audio'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))

@app.route("/", methods=['GET', 'POST'])
def home():
    fpath = None
    regions = None
    if request.method == "POST":      
        file = request.files['file']

        if file.filename == "":
            flash("No file selected")
            return redirect(request.url)

        saved_to = os.path.join(basedir, app.config['UPLOAD_FOLDER'], file.filename) 
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename) 
        file.save(saved_to)
        audio = AudioSegment.from_file(saved_to, "wav")
        output = vad.runVAD(saved_to)
        predictions = vad.parseOutput(output)

        print(predictions)
        result = predictions.to_json(orient="records")
        parsed = json.loads(result)
        json_string = json.dumps(parsed) 
        regions = json_string
        print(regions)
        
    return render_template('home.html', fpath=fpath, regions=regions)

@app.route("/segmentation", methods=['GET'])
def segmentation():
    fpath = request.args.get("fpath")
    regions = request.args.get("regions")
    regions = regions.replace("&#34;", "\"")
    df = pd.read_json(regions, orient="records")
    filename = fpath.split("/")[-1].split(".")[0]

    # output = vad.runSD(app.config['UPLOAD_FOLDER'],fpath, df)
    predictions = vad.runSDBruteForce(app.config['UPLOAD_FOLDER'],fpath, filename)

    print("Done!")

    result = predictions.to_json(orient="records")
    parsed = json.loads(result)
    json_string = json.dumps(parsed) 
    regions = json_string
    
    sleep(6)

    return regions

if __name__ == "__main__":
    app.run(debug=True)

