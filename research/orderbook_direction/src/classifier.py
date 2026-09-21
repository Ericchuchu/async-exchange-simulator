import numpy as np
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score
from data_preprocess import preprocess

def classify(voting_clf, input_data, factor, epsilon=0):

    # First stage : factor classification
    predictions = np.zeros_like(factor)
    predictions[factor > epsilon] = 2
    predictions[factor < -epsilon] = 1
    
    # Second stahe : ML method 
    mask_flat = (factor <= epsilon) & (factor >= -epsilon)
    if np.any(mask_flat):
        flat_indices = np.where(mask_flat)[0]
        flat_input_data = input_data[mask_flat]
        
        flat_predictions = voting_clf.predict(flat_input_data)
        predictions[flat_indices] = flat_predictions
    
    return predictions

if __name__ == '__main__':
    symbol = 'SPOT_BTC_USDT'
    train_input_data, train_label, train_factor = preprocess(symbol, 'train', training_process=False)
    test_input_data, test_label, test_factor = preprocess(symbol, 'test', training_process=False)
    
    voting_clf = joblib.load('ensemble_clf.joblib')

    train_predictions = classify(voting_clf, train_input_data, train_factor)
    test_predictions = classify(voting_clf, test_input_data, test_factor)
    
    train_accuracy = np.mean(train_predictions == train_label)
    test_accuracy = np.mean(test_predictions == test_label)

    train_precision = precision_score(train_label, train_predictions, average='macro')
    test_precision = precision_score(test_label, test_predictions, average='macro')

    train_recall = recall_score(train_label, train_predictions, average='macro')
    test_recall = recall_score(test_label, test_predictions, average='macro')

    train_f1 = f1_score(train_label, train_predictions, average='macro')
    test_f1 = f1_score(test_label, test_predictions, average='macro')
    
    print(f'Train Accuracy: {train_accuracy}')
    print(f'Test Accuracy: {test_accuracy}')
    print(f'Train Precision: {train_precision}')
    print(f'Test Precision: {test_precision}')
    print(f'Train Recall: {train_recall}')
    print(f'Test Recall: {test_recall}')
    print(f'Train F1 Score: {train_f1}')
    print(f'Test F1 Score: {test_f1}')