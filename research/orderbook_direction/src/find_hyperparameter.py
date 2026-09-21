import xgboost as xgb
import optuna
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import f1_score
from data_preprocess import preprocess
import hiplot as hip

if __name__ == '__main__':

    train_data, train_labels, factor = preprocess("SPOT_BTC_USDT", 'train')
    valid_data, valid_labels, factor = preprocess("SPOT_BTC_USDT", 'valid')

    # Calculate the weights of sample
    weights_train = compute_sample_weight(class_weight='balanced', y=train_labels)
    dtrain = xgb.DMatrix(train_data, label=train_labels, weight=weights_train)

    weights_valid = compute_sample_weight(class_weight='balanced', y=valid_labels)
    dvalid = xgb.DMatrix(valid_data, label=valid_labels, weight=weights_valid)

    def objective(trial):
        param = {
            'objective': 'multi:softmax',
            'reg_alpha': 0.01,
            'reg_lambda': 0.01,
            'num_class': 3, 
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'eta': trial.suggest_float('learning_rate', 1e-3, 1e-1),
            'min_child_weight': trial.suggest_float('min_child_weight', 0.5, 1.0)  
        }
        num_boost_round = trial.suggest_int('num_boost_round', 50, 300)

        bst = xgb.train(
            params=param,
            dtrain=dtrain,
            num_boost_round=num_boost_round,
        )

        train_pred = bst.predict(dtrain)
        valid_pred = bst.predict(dvalid)

        train_accuracy = f1_score(train_labels, train_pred, average='weighted')
        valid_accuracy = f1_score(valid_labels, valid_pred, average='weighted')
        return train_accuracy, valid_accuracy

    study = optuna.create_study(directions=["maximize", "maximize"])
    study.optimize(objective, n_trials=300) 

    df = study.trials_dataframe()
    df.rename(columns={"values_0": "train_f1score", "values_1": "valid_f1score"}, inplace=True)
    df.to_csv("optimization_results.csv", index=False)

    df = df.drop(columns=['datetime_start', 'datetime_complete', 'duration', 'state', 'number'])
    hiplot_experiment = hip.Experiment.from_dataframe(df)
    html_content = hiplot_experiment.to_html("visualization.html")