import tensorflow as tf
import numpy as np
import random
from pathlib import Path
from typing import Union, Dict, Tuple, Optional

#랜덤시드 설정
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

#분류 모델 성능 평가(정확도, 정밀도, 재현율, F1점수)
def calculate_score(labels, preds):
    label_correct = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0} #각 클래스마다 올바르게 예측한 개수 저장
    correct = 0

    if len(labels.shape) > 1:
        labels = np.argmax(labels, axis=-1)
    for label, pred in zip(labels, preds):
        if pred == label:
            correct += 1
            label_correct[label] += 1

    result = {
        'accuracy': ((correct / len(labels)) * 100, len(labels)),
    }
    label2idx = {label: idx for idx, label in enumerate([0,1,2,3,4,5])}
    for k, v in label2idx.items():
        precision = (label_correct[v] / (preds==v).sum()) if (preds==v).sum() != 0 else 0.
        recall = (label_correct[v] / (labels==v).sum()) if (labels==v).sum() != 0 else 0.
        f1 = (2 * (precision * recall) / (recall + precision)) if recall + precision != 0 else 0.
        result[k] = (precision * 100, recall * 100, f1 * 100, (labels==v).sum())

    micro_avg_pre = (sum(list(label_correct.values())) / len(labels))
    micro_avg_rec = (sum(list(label_correct.values())) / len(labels))
    micro_avg_f1 = 2 * (micro_avg_pre * micro_avg_rec) / (micro_avg_rec + micro_avg_pre)
    result['micro avg'] = (micro_avg_pre * 100, micro_avg_rec * 100, micro_avg_f1 * 100, len(labels))

    return result
