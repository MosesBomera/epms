from joblib import load
import pandas as pd
import numpy as np

cat_attribs = ['gender', 'fever', 'cough', 'runny_nose', 'headache', 'muscle_aches', 'fatigue']
num_attribs = ['age', 'weight', 'height', 'temperature', 'sp02']

# Load model
model = load('model/epms.joblib')
pipeline = load('model/pipeline.joblib')

def predict(features):
    """
        Makes a prediction given an example.

        features <dict> a dictionary containing features.
    """
    # Create a dataframe
    data = pd.DataFrame.from_dict(features)

    # Transform
    prepared = pipeline.transform(data)
    prediction = model.predict(prepared)

    # Return the prediction
    if prediction[0] == 0:
        return 'Negative'
    else:
        return 'Positive'
