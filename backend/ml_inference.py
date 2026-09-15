"""
Food classification inference.

This defines the REAL model architecture (EfficientNet-B0 backbone with a
fine-tuned classification head) and preprocessing pipeline your trained
checkpoint will use. See train.py for the training script that produces
`food_classifier.pth`.

Until that checkpoint exists (e.g. the first time you run the backend, or
while your teammates work on the frontend), this module falls back to a
clearly-labeled MOCK predictor so the whole app is runnable end-to-end.
Swap CHECKPOINT_PATH once you've trained your model — nothing else in the
app needs to change.
"""
import io
import random
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

CHECKPOINT_PATH = Path(__file__).parent / "food_classifier.pth"

# These must match the class order used when you trained the model
# (see train.py -> FOOD_CLASSES). Kept in sync with nutrition.py's reference table.
FOOD_CLASSES = [
    "pizza", "hamburger", "sushi", "salad", "french_fries", "ice_cream",
    "steak", "fried_rice", "pancakes", "donuts", "chicken_curry",
    "omelette", "spaghetti_bolognese", "waffles", "sandwich",
]

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _build_model(num_classes: int) -> nn.Module:
    """Same architecture used in train.py — a pretrained EfficientNet-B0
    with its final layer replaced to output `num_classes` food categories."""
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


class FoodClassifier:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.is_trained = CHECKPOINT_PATH.exists()

        if self.is_trained:
            self.model = _build_model(len(FOOD_CLASSES))
            self.model.load_state_dict(
                torch.load(CHECKPOINT_PATH, map_location=self.device)
            )
            self.model.to(self.device)
            self.model.eval()

    def predict(self, image_bytes: bytes) -> dict:
        if not self.is_trained:
            return self._mock_predict()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        top3_probs, top3_idx = torch.topk(probs, k=3)
        top3_labels = [FOOD_CLASSES[i] for i in top3_idx.tolist()]

        return {
            "top_prediction": top3_labels[0],
            "confidence": round(top3_probs[0].item(), 3),
            "alternatives": top3_labels[1:],
        }

    def _mock_predict(self) -> dict:
        """
        DEMO MODE — used only when no trained checkpoint is present.
        Lets the rest of the app (backend routes, frontend, DB) be built and
        tested before the model finishes training. Replace by running
        train.py and saving food_classifier.pth next to this file.
        """
        choices = random.sample(FOOD_CLASSES, 3)
        return {
            "top_prediction": choices[0],
            "confidence": round(random.uniform(0.55, 0.95), 3),
            "alternatives": choices[1:],
        }


# Singleton — loaded once at server startup, reused across requests.
classifier = FoodClassifier()
