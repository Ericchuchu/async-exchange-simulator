# Next-Second Price Direction from Order-Book Features

An assignment from the Kronos Research Quantitative Trading Program (October 2024): record market data from the WOO X staging WebSocket, build order-book and order-flow features, and classify whether the index price goes up, down or stays flat over the next second.

**Read this first.** The headline factor of the original report uses future information (details under [Known issues](#known-issues)), so the reported accuracy of about 67% is not an out-of-sample result. The code and the original report are kept as written.

## Pipeline

| Step | Script | What it does |
|---|---|---|
| 1 | recorder (not included) | Subscribed to `orderbook` (100 levels), `bbo`, `trades` and `indexprice` for SPOT_BTC_USDT, SPOT_ETH_USDT and SPOT_WOO_USDT on the WOO X staging feed and wrote JSON Lines. It was built on the WebSocket client template distributed in the program, so it is left out. The recorded session ran 2024-10-02 13:33 to 2024-10-03 02:42 UTC |
| 2 | `src/raw_data_process.py` | Aligns snapshots, BBO and aggregated trade volume to the one-second index-price grid |
| 3 | `src/data_preprocess.py` | Features, labels and the train/validation/test split |
| 4 | `src/benchmark.py`, `src/classifier.py` | Rule-based benchmark on the headline factor; "adjusted" classifier that adds an XGBoost ensemble for the cases where the factor is zero |
| 5 | `src/model_ml.py`, `src/prediction_ml.py`, `src/find_hyperparameter.py` | Soft-voting ensemble of three XGBoost classifiers; Optuna search (300 trials, train and validation F1 as two objectives) inspected with HiPlot |
| 6 | `src/model_nn.py`, `src/loss_function.py`, `src/prediction_nn.py` | MLP 6 → 64 → 128 → 3 with a custom loss (soft macro-precision + weighted cross-entropy + L1/L2). No results were reported for it, and `prediction_nn.py` imports a `train_test_valid` module that is not part of this repository |

Features: order-book imbalance (total ask size − total bid size over 100 levels), BBO size spread, one-second changes of total ask and bid size, the same changes divided by buy and sell trade volume, and the headline factor `highest_order_price_flow` (price change of the level holding the largest resting size, ask plus bid). Labels: direction of the next one-second index-price change (0 flat, 1 down, 2 up).

The recorded data (about 1.7 GB) and the fitted model are not included. `report_original.md` is the report as submitted; its figures were hosted in the private course repository and are omitted.

## Reported results

From `report_original.md`, SPOT_BTC_USDT:

| Model | Train accuracy | Test accuracy | Test precision | Test F1 |
|---|---|---|---|---|
| Benchmark (factor sign) | 0.711 | 0.674 | 0.694 | not reported correctly, see below |
| Adjusted (factor + XGBoost ensemble) | 0.848 | 0.672 | 0.688 | 0.671 |

The report itself concludes that the simple benchmark is at least as good out of sample as the adjusted model.

## Known issues

1. **Look-ahead in the headline factor.** `data_preprocess.py` computes it as `pct_change().shift(-1)`, so the value at time *t* is the change from *t* to *t+1*, the same interval as the label. The report describes it as the change from *t−1* to *t*. Both reported accuracies depend on this factor.
2. **Split.** Rows are split 70/15/15 per class in row order, so the time ranges of train, validation and test overlap across classes.
3. **Metrics.** The benchmark uses weighted averages and the adjusted model macro averages, so their precision and F1 are not comparable, and the benchmark's "Test F1 0.7120" is the training F1 printed twice (`benchmark.py`).
4. **Report vs code.** The report describes order-flow ratios over the top 10 levels; the code uses differences over all 100 levels. The loss weights `[3.8, 3.8, 1]` up-weight the flat and down classes. The recording lasted about 13 hours, not 10.
5. `raw_data_process.py` reads `./data/` while the recorder wrote `test_data/`, and the README commands of the original submission referred to a wrong script name for the hyperparameter search (`find_hyperparameter.py` is the right one).
