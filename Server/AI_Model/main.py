import time
from utils import set_seed, save_test_result
from datamodule import Dataset
from MLP.mlp import MLP


def main():
    set_seed(42)
    dataset = Dataset()

    config = {
        'input_size': dataset.X_train.shape[1],      # 4개의 입력 (frequency, phase, magnitude, 온도)
        'hidden_size': 64,                           # 은닉층 유닛 수 (예시로 64개)
        'output_size': dataset.y_train.shape[1],     # 3개의 출력 (K, N, P 퍼센트)
        'epochs': 50, 
    }
    running_start = time.time()
    result = MLP(config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start))
    print()

if __name__ == "__main__":
    main()