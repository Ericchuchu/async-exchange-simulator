import numpy as np
import pandas as pd
from data_preprocess import preprocess
from sklearn.metrics import accuracy_score,precision_score, recall_score, f1_score

def classify(factor, label):
    predictions = np.zeros_like(label)
    
    eplison = 0
    predictions[factor > eplison] = 2
    predictions[factor < -eplison] = 1
    predictions[(factor <= eplison) & (factor >= -eplison)] = 0
    
    return predictions

if __name__ == '__main__':
    symbol = 'SPOT_BTC_USDT' 
    train_input_data, train_label, train_factor = preprocess(symbol, 'train', training_process=False)
    test_input_data, test_label, test_factor = preprocess(symbol, 'test', training_process=False)

    train_predictions = classify(train_factor, train_label)
    test_predictions = classify(test_factor, test_label)

    train_accuracy = accuracy_score(train_label, train_predictions)
    test_accuracy = accuracy_score(test_label, test_predictions)

    train_precision = precision_score(train_label, train_predictions, average='weighted')
    test_precision = precision_score(test_label, test_predictions, average='weighted')

    train_recall = recall_score(train_label, train_predictions, average='weighted')
    test_recall = recall_score(test_label, test_predictions, average='weighted')

    train_f1 = f1_score(train_label, train_predictions, average='weighted')
    test_f1 = f1_score(test_label, test_predictions, average='weighted')
    
    print(f'Train Accuracy: {train_accuracy}')
    print(f'Test Accuracy: {test_accuracy}')
    print(f'Train Precision: {train_precision}')
    print(f'Test Precision: {test_precision}')
    print(f'Train Recall: {train_recall}')
    print(f'Test Recall: {test_recall}')
    print(f'Train F1 Score: {train_f1}')
    print(f'Test F1 Score: {train_f1}')