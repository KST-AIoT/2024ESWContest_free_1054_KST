import time
from utils import set_seed
from datamodule import Dataset
from CNN.CNN import CNN

def train_model():
    set_seed(42)
    X_train, X_valid, y_train, y_valid = Dataset()

    config = {
        'learning_rate': 0,
        'epochs' : 100,
    }


    #CNN 모델 학습
    running_start = time.time()
    CNN(config, X_train, X_valid, y_train, y_valid).run()

    print("Model Execution time : {:.4f} sec".format(
        time.time() - running_start))
    print()




    

if __name__ == "__main__":
    train_model()