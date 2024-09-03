import time
from utils import set_seed
from datamodule import Dataset
from CNN.CNN import train_cnn
import torch

def train_model():
    set_seed(42)
    X_train, y_train = Dataset().get_data()  # get_data()에서 두 개의 값만 반환합니다.
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.long)

    config = {
        'learning_rate': 0.0008,  # 학습률 낮춤
        'epochs': 1000,  # 에포크 수 증가
    }

    # CNN 모델 학습 (검증 데이터 없이 학습)
    running_start = time.time()
    model = train_cnn(config, X_train, X_train, y_train, y_train)  # 훈련 데이터만 사용

    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start))
    print()

if __name__ == "__main__":
    train_model()
