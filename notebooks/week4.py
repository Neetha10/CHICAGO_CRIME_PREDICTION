import joblib
import numpy as np

MODEL_PATH = "../notebooks/crime_model.pkl"
model = joblib.load(MODEL_PATH)


def predict_crime(hour, lat, lng):
    X = np.array([[hour, lat, lng]])
    result = model.predict(X)
    print(result)
    {'Drug/Vice': 0, 'Property':1, 'Violent': 2,  'Other':3 }
    if (result[0] == 0):
        return "Drug/Vice"
    elif result[0] == 1:
        return "Property"
    elif result[0] == 2:
        return "Violent"
    else:
        return "Other"


if __name__ == "__main__":
    print("Training the model...")
    joblib.dump(model, MODEL_PATH)
    print("Model saved!")