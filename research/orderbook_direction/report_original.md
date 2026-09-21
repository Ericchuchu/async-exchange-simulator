# Original report (October 2024)

> Text kept as submitted; the title was changed and six figures that were hosted in the private course repository are omitted. See [README.md](README.md) for a look-ahead flaw in the headline factor and other corrections.

## Data scraping and preprocessing

To collect historical data, we implemented web socket technology combined with multiprocessing techniques to fetch real-time snapshots of the order book, trade data, and Best Bid and Offer (BBO) data. These were saved as JSON files for subsequent analysis.

The data scraping process lasted approximately 10 hours. Given our objective to predict price movements in the next second, we established a consistent time interval of one second for data collection.

For the order book snapshots and BBO data, we aligned our records using timestamps that correspond directly to those of the price data. For trade data, we aggregated the total volume traded in the interval between two consecutive timestamps (from t-1 to t), where t is the timestamp of the price data.

This structured approach ensures that each data point is accurately synchronized with the price movements, facilitating more precise predictive analysis.

## Factor analysis and data visualization in different classes 

Use raw data to compute some factor and visualize the distribution under different classes to see whether there is any significant differences

1. bbo bid-ask spread and bbo bid-ask size spread
   
  [figure omitted: it was hosted in the private course repository]

2. bid-ask size spread
   
   orderbook imblance :

   **total ask size - total bid size**
   
   adjusted orderbook bid-ask price change(highest order) :

   **(ask_price[argmax[ask_size] (t) / ask_price[argmax[ask_size] (t-1)) + (bid_price[argmax[bid_size] (t) / bid_price[argmax[bid_size] (t-1))**

   [figure omitted: it was hosted in the private course repository]

3. order flow

   buy order flow :

   **sum (top 10 ask size) (t) / sum (top 10 ask size) (t-1)**

   sell order flow :

   **sum (top 10 ask size) (t) / sum (top 10 ask size) (t-1)**

   net order flow :

   **buy order flow - sell order flow**

   [figure omitted: it was hosted in the private course repository]

4. order flow (adjusted by trade volume)

   buy order flow adjusted :

   **(sum (top 10 ask size) / buy volume) (t) / (sum (top 10 ask size) / buy volume) (t-1)**

   sell order flow adjusted :

   **(sum (top 10 bid size) / sell volume) (t) / (sum (top 10 bid size) / sell volume) (t-1)**

   net order flow adjusted :

   **buy order flow adjusted - sell order flow adjusted**

   [figure omitted: it was hosted in the private course repository]

**conclusion** :

After observation and calculation, I believe that all these factors are potential variables that can cause price to go up, down, or remain flat. In other words, they should show significant differences under various conditions. However, it's possible that due to small time intervals and high frequency scenarios, many factors have similar distributions with only slight deviations.

Importantly, the adjusted orderbook bid-ask price change (highest order) factor shows significant differences across different labels. This means it can effectively classify the price trend for the next second. When it's greater than 0, the price tends to rise; when it's less than 0, the price tends to fall; and when it equals 0, the price tends to remain stable.

The idea for this factor originated from the observation that many people in the crypto market rely on trading bots to place orders. I believe that the highest bid-ask order volumes are likely placed by automated trading bots. This suggests that there might be certain positive or negative conditions in the market for this particular asset, prompting the bots to place orders at these levels.

Therefore, I decided to look at the percentage change between the bid-ask price with the highest order volume from the previous second and the current bid-ask price with the highest order volume. By adding these two percentages together, we can derive this factor.

The reason for adding the percentages is to amplify the skewness of price movements. When both percentages are positive, it usually indicates positive market sentiment, and when both are negative, it typically suggests negative sentiment. Thus, adding them together can enhance the effect of classifying price movements as up or down.

## Benchmark model for classification :

In the previous statement, we identified a strong factor for predicting price movement in the next second, which we used to build a benchmark classification model.

However, this approach has a notable drawback. While it's highly accurate in predicting price increases when the factor is greater than 0, and price decreases when it's less than 0, it's less reliable in predicting flat price movements when the factor equals 0. This is because the condition where the factor equals 0 also includes a relatively high number of instances of both price increases and decreases.

To address this limitation, we're focusing on refining our model in cases where the factor equals 0. Our goal is to optimize the classifier by examining these cases more closely and potentially introducing additional criteria or factors to improve our predictions when the primary factor doesn't provide a clear directional signal.

This refinement process aims to enhance the overall accuracy of our classification model, particularly in situations where the price movement is less clear-cut. By doing so, we hope to develop a more robust and reliable predictor of price movements across all scenarios, including those that fall into the previously ambiguous 'flat' category.

## ML method for optimization :

1. datset and features :

   We allocated 70% of the data for training, 15% for validation, and 15% for testing. The labels were assigned as follows: 0 represents flat price movement, 1 represents price down, and 2 represents price up.
   Since there were more instances of label 0 (flat price movement) in our dataset, we applied a preprocessing step to address this imbalance. We assigned higher weights to the other two labels (price up and        price down) for the model to consider. This approach helps to mitigate the bias that could result from the overrepresentation of flat price movements in the data.
   
   Additionally, we ensured that the labels were evenly distributed across all three datasets (training, validation, and testing). This balanced distribution allows for a more accurate comparison of model           performance across different price movement scenarios, reducing the potential for bias in our evaluation metrics.

   To refine our model, we decided to utilize the previously mentioned less prominent factors as features. 
   
3. model selection :

   Since these factors show very similar distributions across different labels, conceptually, we considered using either tree-based machine learning methods or neural networks.
   
   After experimenting with both approaches, I found that tree-based classifiers performed better for our specific case. Ultimately, I chose an ensemble model based on XGBoost as our primary model.

4. find hyperparameter of XGBoost :

   We utilized Optuna to conduct parameter trials(300) for a single XGBoost model. Our primary goal was to observe under which conditions the F1 scores for both the validation and training data would be higher.
   To visualize the results of these trials, we employed HiPlot for 2-dimensional visualization. This allowed us to search for parameter plateaus - areas in the parameter space where performance is consistently     high.
   Based on these visualizations and the identified high-performing parameter regions, we then selected specific parameter sets to construct our ensemble model.

   the result :
   [figure omitted: it was hosted in the private course repository]

   the region we chosed :
   [figure omitted: it was hosted in the private course repository]

   this is at visualization.html

6. ensemble model :

   **First XGBoost Classifier (xgb_clf1) :**
   
   n_estimators: 300 , learning_rate: 0.04, min_child_weight: 0.92 


   **Second XGBoost Classifier (xgb_clf2) :**

   n_estimators: 280 , learning_rate: 0.55 , min_child_weight: 0.92 


   **Third XGBoost Classifier (xgb_clf3) :**

   n_estimators: 280 , learning_rate: 0.55 , min_child_weight: 0.94 


   Common parameters across all classifiers:
   
   * objective: 'multi:softprob' (for multi-class probability prediction)
   
   * num_class: 3 (indicating three possible classes)
   
   * max_depth: 6 (maximum depth of each tree)
   
   * seed: 0 (for reproducibility)

7. adjusted classification model (after optimization) :

   This classifier function implements a two-stage classification process:
   
   **First Stage: Factor-based Classification**

   * Set eplison as 0
   
   * uses the 'factor' (likely the strong predictor mentioned earlier) to make initial predictions.
   
   * the factor is greater than epsilon, it predicts class 2 (likely price up).
   
   * If the factor is less than -epsilon, it predicts class 1 (likely price down).
   
   **Second Stage: Machine Learning Classification**
   
   * For cases where the factor is between -epsilon and epsilon (considered 'flat'), it uses the voting classifier.
   
   * It identifies these 'flat' cases using a mask.
   
   * If there are any 'flat' cases, it applies the voting classifier only to these data points.
   
   * The predictions from the voting classifier are then inserted back into the overall predictions array.

## Performance comparation :

1. benchmark model :
   * Train Accuracy: 0.7113143754150818
   * Test Accuracy: 0.6739895789325447
   * Train Precision: 0.7154640871990605
   * Test Precision: 0.693871644248123
   * Train Recall: 0.7113143754150818
   * Test Recall: 0.6739895789325447
   * Train F1 Score: 0.7119840651652064
   * Test F1 Score: 0.7119840651652064

2. adjusted classification model :
   * Train Accuracy: 0.8481555273803055
   * Test Accuracy: 0.6715955499225461
   * Train Precision: 0.8630832465462955
   * Test Precision: 0.6881441149687689
   * Train Recall: 0.8521364109601288
   * Test Recall: 0.6681599821066446
   * Train F1 Score: 0.8480425485357346
   * Test F1 Score: 0.6711704390544613
  
# Conclusion :

In summary, the benchmark model performed better on out-of-sample data, while the adjusted classification model showed superior performance on the training data. This discrepancy suggests potential areas for improvement, which can be attributed to several factors:

1. Insufficient Parameter Trials:
   The current 300 trials for parameter optimization may be inadequate to effectively identify parameter plateaus. Increasing the number of trials could lead to more robust parameter selections and potentially      improve out-of-sample performance.
   
3. Limited Dataset Size:
   Using only 10 hours of data may result in a dataset that's too small, making the model prone to overfitting. A larger dataset spanning a longer time period could provide more diverse market conditions and        lead to better generalization.
   
5. Feature Limitations:
   The current model, with its limited number of features, may be too sensitive to noise in the training data. This sensitivity could explain the model's strong performance on training data but weaker               performance on out-of-sample data.

         


   

















   

