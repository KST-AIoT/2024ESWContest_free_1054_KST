import tensorflow as tf
import numpy as np
import random
from pathlib import Path
from typing import Union, Dict, Tuple, Optional

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

def calculate_score(labels, preds):
    label_correct = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
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

def save_test_result(result: Dict[str, Union[Tuple[float, float, float, int], Tuple[float, int]]], 
                    std_name: Optional[str] = None, 
                    std_id: Optional[str] = None):
    output_path = Path('./pa2_test_{}_{}.txt'.format(std_name, std_id))
    with open(output_path, mode='w', encoding="utf-8") as f:
        for model_type in ['naive_bayes', 'decision_tree', 'mlp', 'custom_mlp']:
            label_name = [0,1,2,3,4,5]
            tmp = result[model_type]
            if tmp is None:
                continue
            
            headers = ["precision", "recall", "f1-score", "# docs"]
            name_width = max(10 for cn in label_name)
            width = max(name_width, len('micro avg'))
            head_fmt = '{:>{width}s} ' + ' {:>9}' * len(headers)
            report = head_fmt.format('', *headers, width=width) + '\n\n'
            row_fmt = '{:>{width}s} ' + ' {:>9.2f}' * 3 + ' {:>9}\n'
            for label in label_name:
                report += row_fmt.format(
                    str(label), 
                    tmp[label][0], 
                    tmp[label][1], 
                    tmp[label][2], 
                    tmp[label][3], 
                    width=width
                )
            row_fmt_accuracy = '{:>{width}s} ' + \
                                ' {:>9.2}' * 2 + ' {:>9.2f}' + \
                                ' {:>9}\n'
            report += row_fmt_accuracy.format(
                'accuracy', 
                '', 
                '', 
                tmp['accuracy'][0], 
                tmp['accuracy'][1], 
                width=width
            )

            f.write('Model Type : {}\n'.format(model_type))
            f.write(report + '\n')
