"""
Fine-tunes EfficientNet-B0 on Food-101 to produce food_classifier.pth.

Run this SEPARATELY from the API server, once, before your demo
(ideally on a GPU — Colab works fine for this):

    python train.py

It expects the Food-101 dataset laid out as:
    data/food-101/images/<class_name>/<image>.jpg
Download it from https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz

To keep training fast for a student project, this only trains on the
15 classes listed in ml_inference.FOOD_CLASSES rather than all 101 —
extend FOOD_CLASSES in ml_inference.py first if you want more categories,
then re-run this script.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from ml_inference import FOOD_CLASSES, _build_model, _transform

DATA_DIR = "data/food-101/images"
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 1e-4
CHECKPOINT_OUT = "food_classifier.pth"


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    full_dataset = datasets.ImageFolder(DATA_DIR, transform=_transform)

    # Keep only the classes we're actually classifying
    class_to_idx = {c: i for i, c in enumerate(FOOD_CLASSES)}
    keep_indices = [
        i for i, (_, label) in enumerate(full_dataset.samples)
        if full_dataset.classes[label] in class_to_idx
    ]
    dataset = torch.utils.data.Subset(full_dataset, keep_indices)

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = _build_model(len(FOOD_CLASSES)).to(device)

    # Freeze the backbone, train only the new classification head first —
    # faster convergence, less overfitting on a small subset of classes.
    for param in model.features.parameters():
        param.requires_grad = False

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        val_acc = _evaluate(model, val_loader, device)
        print(f"Epoch {epoch+1}/{EPOCHS} — loss: {running_loss/len(train_loader):.4f} "
              f"— val accuracy: {val_acc:.2%}")

    torch.save(model.state_dict(), CHECKPOINT_OUT)
    print(f"Saved trained model to {CHECKPOINT_OUT}")


def _evaluate(model, loader, device) -> float:
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)
    return correct / total


if __name__ == "__main__":
    main()
