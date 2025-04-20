from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np


MODEL_PATH = 'brain_tumor_detection_model_vgg16-v2.h5'

model = load_model(MODEL_PATH)

def model_predict(img_path):
    global model
    img = image.load_img(img_path, target_size=(224, 224))

    x = image.img_to_array(img)  
    x = x / 255
    x = np.expand_dims(x, axis=0)
   
   
    preds = model.predict(x)
    preds = np.argmax(preds, axis=1)  
    if preds == 2:
        return False
    else:
        return True