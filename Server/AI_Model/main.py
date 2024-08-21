import time
from utils import set_seed, save_test_result
from datamodule import Dataset
from MLP.mlp import MLP
from RandomForest.RF import RF
from KNN.KNN import KNN
def main():
    set_seed(42)
    dataset = Dataset()

    mlp_config = {
        'input_size': dataset.X_train.shape[1],      # 4개의 입력 (frequency, phase, magnitude, 온도)
        'hidden_size': 64,                           # 은닉층 유닛 수 (예시로 64개)
        'output_size': dataset.y_train.shape[1],     # 3개의 출력 (K, N, P 퍼센트)
        'epochs': 50, 
    }
    rf_config = {
        'n_estimators':100, 
        'max_depth':20,
        'random_state':0,
    }
    knn_config = {
    'n_neighbors': 5,         # 고려할 이웃의 수
    'weights': 'distance',    # 이웃의 가중치 (거리 기반)
    'algorithm': 'auto',      # 가장 적합한 알고리즘 자동 선택
    'leaf_size': 30,          # 트리 기반 알고리즘에서의 leaf 크기
    'p': 2                    # 거리 계산 방식 (유클리디안 거리)
    }

    #mlp 모델 학습
    running_start = time.time()
    result = MLP(mlp_config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start))
    print()

    #random forest 모델 학습
    running_start2 = time.time()
    result = RF(rf_config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start2))
    print()

    #knn 모델 학습
    running_start3 = time.time()
    result = KNN(knn_config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start3))
    print()

if __name__ == "__main__":
    main()