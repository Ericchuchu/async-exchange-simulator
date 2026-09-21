import numpy as np
import xgboost as xgb
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score,precision_score, recall_score, f1_score
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.ensemble import VotingClassifier
import joblib 

def ensemble_classifier(train, train_label, test, test_label, train_weights):

    param1 = {
        'n_estimators': 300,
        'objective': 'multi:softprob',
        'num_class': 3,
        'max_depth': 6,
        'learning_rate': 0.04,
        'min_child_weight': 0.92,
        'seed': 0
    }
    xgb_clf1 = xgb.XGBClassifier(**param1)
    xgb_clf1.fit(train, train_label, sample_weight=train_weights)

    param2 = {
        'n_estimators': 280,
        'objective': 'multi:softprob',
        'num_class': 3,
        'max_depth': 6,
        'learning_rate': 0.55,
        'min_child_weight': 0.92,
        'seed': 0
    }
    xgb_clf2 = xgb.XGBClassifier(**param2)
    xgb_clf2.fit(train, train_label, sample_weight=train_weights)

    param3 = {
        'n_estimators': 280,
        'objective': 'multi:softprob',
        'num_class': 3,
        'max_depth': 6,
        'learning_rate': 0.55,
        'min_child_weight': 0.94,
        'seed': 0
    }
    xgb_clf3 = xgb.XGBClassifier(**param3)
    xgb_clf3.fit(train, train_label, sample_weight=train_weights)

    voting_clf = VotingClassifier(
        estimators=[('xgb1', xgb_clf1), ('xgb2', xgb_clf2), ('xgb3', xgb_clf3)],
        voting='soft'
    )

    print("Training Ensemble Classifier...")
    voting_clf.fit(train, train_label, sample_weight=train_weights)
    predictions = voting_clf.predict(train)

    accuracy = accuracy_score(train_label, predictions)
    print(f"Train Accuracy: {accuracy:.4f}")

    print("Testing Ensemble Classifier...")
    predictions = voting_clf.predict(test)

    accuracy = accuracy_score(test_label, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    precision = precision_score(test_label, predictions, average='weighted')
    print(f"Precision: {precision:.4f}")

    recall = recall_score(test_label, predictions, average='weighted')
    print(f"Recall: {recall:.4f}")

    f1 = f1_score(test_label, predictions, average='weighted')
    print(f"F1 Score: {f1:.4f}")

    joblib.dump(voting_clf, 'ensemble_clf.joblib')

'''
def xgboost_classifier(train, train_label, test, test_label):
    clf = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        objective='multi:softprob',
        num_class=len(np.unique(train_label)),
        seed=0
    )

    print("Training XGBoost Classifier...")
    clf.fit(train, train_label)
    predictions = clf.predict(train)

    accuracy = accuracy_score(train_label, predictions)
    print(f"Train Accuracy: {accuracy:.4f}")

    print("Testing XGBoost Classifier...")
    predictions = clf.predict(test)

    accuracy = accuracy_score(test_label, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    precision = precision_score(test_label, predictions, average='weighted')
    print(f"Precision: {precision:.4f}")

    recall = recall_score(test_label, predictions, average='weighted')
    print(f"Recall: {recall:.4f}")

    f1 = f1_score(test_label, predictions, average='weighted')
    print(f"F1 Score: {f1:.4f}")


def linear_regression_classifier(train, train_label, test, test_label):

    clf = LogisticRegression(multi_class='ovr', solver = 'newton-cg', max_iter=1000)

    print("Training Linear Regression Classifier...")
    clf.fit(train, train_label)
    predictions = clf.predict(train)

    accuracy = accuracy_score(train_label, predictions)
    print(f"Train Accuracy: {accuracy:.4f}")

    print("Testing Linear Regression Classifier...")
    predictions = clf.predict(test)

    accuracy = accuracy_score(test_label, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    precision = precision_score(test_label, predictions, average='weighted')
    print(f"Precision: {precision:.4f}")

    recall = recall_score(test_label, predictions, average='weighted')
    print(f"Recall: {recall:.4f}")

    f1 = f1_score(test_label, predictions, average='weighted')
    print(f"F1 Score: {f1:.4f}")

def gradientboost_classifier(train, train_label, test, test_label):

    clf = GradientBoostingClassifier(n_estimators=2000)
    
    print("Training Gradient Boosting Classifier...")
    clf.fit(train, train_label)
    predictions = clf.predict(train)

    accuracy = accuracy_score(train_label, predictions)
    print(f"Train Accuracy: {accuracy:.4f}")
    
    print("Testing Gradient Boosting Classifier...")
    predictions = clf.predict(test)
    
    accuracy = accuracy_score(test_label, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    precision = precision_score(test_label, predictions, average='weighted')
    print(f"Precision: {precision:.4f}")

    recall = recall_score(test_label, predictions, average='weighted')
    print(f"Recall: {recall:.4f}")

    f1 = f1_score(test_label, predictions, average='weighted')
    print(f"F1 Score: {f1:.4f}")

def continuous_bayes_classifier_sklearn(train, train_label, test, test_label):

    clf = GaussianNB()

    print("Training Continuous Naive Bayes Classifier...")
    clf.fit(train, train_label)
    predictions = clf.predict(train)

    accuracy = accuracy_score(train_label, predictions)
    print(f"Train Accuracy: {accuracy:.4f}")

    print("Testing Continuous Naive Bayes Classifier...")
    predictions = clf.predict(test)
    
    posteriors = clf.predict_proba(test)
    for post, pred, ans in zip(posteriors, predictions, test_label):
        print(f"Posterior:")
        for c in range(len(post)):
            print(f"{c}: {post[c]}")
        print(f"Prediction: {pred}, Ans: {ans}")

    accuracy = accuracy_score(test_label, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    precision = precision_score(test_label, predictions, average='weighted')
    print(f"Precision: {precision:.4f}")

    recall = recall_score(test_label, predictions, average='weighted')
    print(f"Recall: {recall:.4f}")

    f1 = f1_score(test_label, predictions, average='weighted')
    print(f"F1 Score: {f1:.4f}")



'''