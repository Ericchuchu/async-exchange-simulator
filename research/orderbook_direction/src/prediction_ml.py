from data_preprocess import preprocess
from model_ml import ensemble_classifier
import xgboost as xgb
from sklearn.utils.class_weight import compute_sample_weight

if __name__ == '__main__':
    symbol = "SPOT_BTC_USDT"
    train_data, train_labels, factor = preprocess(symbol, 'train')
    test_data, test_labels, factor = preprocess(symbol, 'test')

    # Calculate the weights of sample
    weights_train = compute_sample_weight(class_weight='balanced', y=train_labels)
    weights_test = compute_sample_weight(class_weight='balanced', y=test_labels)

    ensemble_classifier(train_data, train_labels, test_data, test_labels, weights_train)
