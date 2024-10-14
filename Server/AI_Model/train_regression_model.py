import time
from regression_datamodule import Dataset
from CNN_regression.CNN_regression import train_cnn_regression
from CNN_regression.CNN_regression import train_cnn_lite_regression
import torch
import random 
import numpy as np

'''
모델을 학습시키는 함수
: 데이터셋을 불러오고, 전처리 후, CNN 모델을 학습시킴

'''
def train_regression_model():
    set_seed(42)
    X_train, y_train = Dataset().get_data()                             # 데이터셋에서 훈련 데이터를 가져옴
    X_train = torch.tensor(X_train, dtype=torch.float32)                # 데이터를 텐서로 변환 (float 타입)
    y_train = torch.tensor(y_train, dtype=torch.float32)                   # 라벨 데이터를 텐서로 변환 (float 타입)

    config = {
        'learning_rate': 0.01,  # 학습률 낮춤
        'epochs': 100,  # 에포크 수 증가
    }

    # CNN 모델 학습
    running_start = time.time()                                         # 학습 시작 시간 기록
    model = train_cnn_regression(config, X_train, X_train, y_train, y_train)      

    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start))
    print()


    # CNN lite 모델 학습
    running_start2 = time.time()
    lite_model = train_cnn_lite_regression(config, X_train, X_train, y_train, y_train)
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start2))
    print()


'''
랜덤시드 설정 함수
'''
def set_seed(seed):
    random.seed(seed)                                                   # 파이썬 기본 random 모듈 시드 설정
    np.random.seed(seed)                                                # numpy 모듈의 시드 설정

if __name__ == "__main__":
    train_regression_model()
