import time
from utils import set_seed
from datamodule import Dataset
from RandomForest.RF import RF
from LinearRegression.LR import LR
from DecisionTree.DT import DT
from SVR.SVR import SVRModel

def main():
    set_seed(42)
    dataset = Dataset()

    dt_config = {
        'min_samples_leaf': 5,  # 각 리프 노드에 최소 5개의 샘플이 있어야 함
        'max_depth': 10,        # 트리의 최대 깊이
        'random_state': 42      # 결과 재현성을 위한 랜덤 시드
    }

    rf_config = {
        'n_estimators':100, 
        'max_depth':20,
        'random_state':0,
    }



    #decision tree 모델 학습
    running_start1 = time.time()
    result = DT(dt_config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start1))
    print()

    #선형 회귀 모델 학습
    running_start2 = time.time()
    result = LR(dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start2))
    print()

    #random forest 모델 학습
    running_start3 = time.time()
    result = RF(rf_config, dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start3))
    print()

    #support vector regression 모델 학습
    running_start4 = time.time()
    result = SVRModel(dataset).run()
    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start4))
    print()



    

if __name__ == "__main__":
    main()