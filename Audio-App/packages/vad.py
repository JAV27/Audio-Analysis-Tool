from distutils.command.upload import upload
from app import segmentation
from pyannote.audio import Pipeline, Model, Inference
from pyannote.audio.pipelines import VoiceActivityDetection, SpeakerSegmentation, SpeakerDiarization
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from flask import Response
from pydub import AudioSegment
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from pyannote.core import Segment
from os.path import exists

def runVAD(saved_to):
    model = Model.from_pretrained("pyannote/segmentation", use_auth_token="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")
    pipeline = VoiceActivityDetection(segmentation=model)
    HYPER_PARAMETERS = {
        # onset/offset activation thresholds
        "onset": 0.5, "offset": 0.5,
        # remove speech regions shorter than that many seconds.
        "min_duration_on": 0.0,
        # fill non-speech regions shorter than that many seconds.
        "min_duration_off": 1
    }
    pipeline.instantiate(HYPER_PARAMETERS)
    vad = pipeline(saved_to)

    return vad

def runSD(upload_folder, saved_to, predictions):
    # Chop up audio file into just speaking regions
    audio = AudioSegment.from_file(saved_to, "wav")
    predictions["Start ms"] = predictions["Start Total Seconds"]*1000
    predictions["End ms"] = predictions["End Total Seconds"]*1000

    just_talking = None
    for i,row in predictions.iterrows():
        clip = audio[row["Start ms"]:row["End ms"]]
        if just_talking is None:
            just_talking = clip
        else:
            just_talking += clip

    file_handle = just_talking.export(upload_folder + "justtalking.wav", format="wav")

    # Run SD
    test_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="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")
    diarization = test_pipeline(upload_folder + "justtalking.wav")

    # Label original regions with speakers
    total_time = 0
    cur_index = 0
    
    for segment, _, label in diarization.itertracks(yield_label=True):
        original = predictions[cur_index]
        start, end = segment




        print(segment, start, end, label[-2:])
        
    return diarization

def runSDBruteForce(upload_folder, saved_to, filename):

    if exists(upload_folder + filename + ".csv"):
        df = pd.read_csv(upload_folder + filename + ".csv", index_col=0)
        print("Already Exists!")
        return df

    audio = AudioSegment.from_file(saved_to, "wav")

    # Run SD
    test_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="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")

    print("Running Diarization...")

    diarization = test_pipeline(saved_to)

    def parse(dia):
        start, end = dia[0]
        speaker = dia[2]
        label = int(speaker.split("_")[1])

        return (start, end, label)

    for_pd = list(map(parse, list(diarization.itertracks(yield_label=True))))

    df = pd.DataFrame(for_pd, columns=["Start Total Seconds", "End Total Seconds", "Label"])

    df["Diff"] = df["End Total Seconds"]-df["Start Total Seconds"]

    df.to_csv(upload_folder + filename + ".csv")

    return df


def parseOutput(output):
    starts = []
    ends = []
    for o in output.get_timeline():
        start, end = list(o)
        start = np.floor(start)
        end = np.ceil(end)
        starts.append(start)
        ends.append(end)
    
    predictions = pd.DataFrame({"Start Total Seconds": starts, "End Total Seconds": ends})
    predictions["Diff"] = predictions["End Total Seconds"]-predictions["Start Total Seconds"]
    
    return predictions

def formatForPlot(df, duration):
    y = np.zeros(duration)

    for index, val in df.iterrows():
        start = int(val["Start Total Seconds"])
        y[start:start+int(val["Diff"])] = 1

    return y

def removeSmallBreaks(arr, n):
    counter = 0
    new_arr = np.copy(arr)
    for i in range(len(new_arr)):
        if i >= 200 and i <= 300:
            print(f"i: {i}")
            print(f"Counter: {counter}")
        if new_arr[i] == 0:
            counter += 1
        
        if i+1 < len(new_arr):
            if new_arr[i+1] == 1:
                if counter < n:
                    new_arr[i-counter+1:i+1] = 1
            
                counter = 0
        else:
            if counter < n:
                new_arr[i-counter+1:i+1] = 1
                counter = 0
    return new_arr

def createVADGraph(y):
    # plt.plot(range(len(y)), y)
    # plt.savefig("fig.png")
   fig = Figure()
   axis = fig.add_subplot(1, 1, 1)
   xs = np.random.rand(100)
   ys = np.random.rand(100)
   axis.plot(xs, ys)
   output = io.BytesIO()
   FigureCanvas(fig).print_png(output)

   return Response(output.getvalue(), mimetype='image/png')

