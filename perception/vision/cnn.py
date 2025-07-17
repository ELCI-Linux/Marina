# perception/occular/cnn.py

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class ScalableCNN(nn.Module):
    def __init__(self, input_channels=3, num_classes=10, model_scale='auto'):
        super(ScalableCNN, self).__init__()
        self.model_scale = model_scale if model_scale != 'auto' else self._auto_scale()

        if self.model_scale == 'light':
            self.feature_extractor = self._light_model(input_channels)
        elif self.model_scale == 'medium':
            self.feature_extractor = self._medium_model(input_channels)
        else:
            self.feature_extractor = self._heavy_model(input_channels)

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self._get_flattened_size(), 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, num_classes)
        )

    def _auto_scale(self):
        # Dynamically assess device memory and CPU power (simple heuristic)
        total_memory = torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 8e9
        return 'light' if total_memory < 4e9 else ('medium' if total_memory < 10e9 else 'heavy')

    def _light_model(self, input_channels):
        return nn.Sequential(
            nn.Conv2d(input_channels, 16, 3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

    def _medium_model(self, input_channels):
        return nn.Sequential(
            nn.Conv2d(input_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

    def _heavy_model(self, input_channels):
        # Use pretrained ResNet backbone
        resnet = models.resnet18(pretrained=True)
        resnet.conv1 = nn.Conv2d(input_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        modules = list(resnet.children())[:-2]  # Remove avgpool and fc
        return nn.Sequential(*modules)

    def _get_flattened_size(self):
        with torch.no_grad():
            dummy_input = torch.zeros(1, 3, 64, 64)  # Dummy input for shape inference
            features = self.feature_extractor(dummy_input)
            return features.view(1, -1).shape[1]

    def forward(self, x):
        x = self.feature_extractor(x)
        x = self.classifier(x)
        return x

if __name__ == "__main__":
    model = ScalableCNN(input_channels=3, num_classes=10)
    print(model)
    dummy = torch.randn(1, 3, 64, 64)
    out = model(dummy)
    print("Output shape:", out.shape)
