import torch
import torch.nn as nn
import torch.optim as optim

class CNN(nn.Module):
    def __init__(self, config):
        super(CNN, self).__init__()
        self.config = config
        self.conv1 = nn.Conv1d(in_channels=2, out_channels=16, kernel_size=3, padding='same')
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding='same')
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
        self.conv3 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding='same')
        self.conv4 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding='same')
        self.global_avg_pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(128, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 8)  # 26개의 클래스를 예측

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = torch.relu(self.conv3(x))
        x = torch.relu(self.conv4(x))
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    

def train_cnn(config, X_train, X_valid, y_train, y_valid):
    model = CNN(config)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])

    for epoch in range(config['epochs']):
        model.train()
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_outputs = model(X_valid)
            val_loss = criterion(val_outputs, y_valid)

        print(f'Epoch {epoch+1}/{config["epochs"]}, Training Loss: {loss.item():.4f}, Validation Loss: {val_loss.item():.4f}')

    save_model(model, './CNN/cnn_model.pth')
    return model

def save_model(model, path):
    torch.save(model.state_dict(), path)
    print(f'Model saved to {path}')
