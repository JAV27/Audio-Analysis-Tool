from pyannote.audio import Model
from pyannote.audio.pipelines import VoiceActivityDetection
import numpy as np
import pandas as pd

model = Model.from_pretrained("pyannote/segmentation", use_auth_token="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")
pipeline = VoiceActivityDetection(segmentation=model)
HYPER_PARAMETERS = {
  # onset/offset activation thresholds
  "onset": 0.5, "offset": 0.5,
  # remove speech regions shorter than that many seconds.
  "min_duration_on": 0.0,
  # fill non-speech regions shorter than that many seconds.
  "min_duration_off": 0.0
}
pipeline.instantiate(HYPER_PARAMETERS)
vad = pipeline("data/trn01.wav")

starts = []
ends = []
for o in vad.get_timeline():
    start, end = list(o)
    start = np.floor(start)
    end = np.ceil(end)
    starts.append(start)
    ends.append(end)

predictions = pd.DataFrame({"Start Total Seconds": starts, "End Total Seconds": ends})
predictions["Diff"] = predictions["End Total Seconds"]-predictions["Start Total Seconds"] 
print(predictions)