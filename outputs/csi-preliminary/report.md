# Preliminary CSI classifier evaluation

These models are trained, but are not reliable enough to activate. They have not been deployed to the dashboard.

## Results on held-out recording sessions

| Task | Accuracy | Balanced accuracy |
|---|---:|---:|
| Empty / still / walking | 23.6% | 24.2% |
| Empty / occupied | 54.4% | 41.7% |

The presence model incorrectly calls 99.3% of empty-room windows occupied and misses 17.2% of occupied windows. Always predicting occupied would score 65.4% overall accuracy on these retained windows, better than the learned binary model. Balanced accuracy for that constant baseline is 50%.

## Data and method

Nine confirmed recordings, three per condition, nominally 18 minutes. Converted to 436 non-overlapping two-second windows with sufficient usable measurements from both boards. First 10 seconds and final 6 seconds omitted to reduce transitions. Empty amplitude arrays and stale node samples excluded. No malformed JSON lines were found among these nine files.

Features: 24 signal-summary values, derived from each node's RSSI and amplitude mean, standard deviation, percentiles and zero fraction; aggregate each over a two-second window using mean and standard deviation. This uses processed amplitude arrays, not raw complex CSI. Dashboard presence, motion labels, person counts, pose, vitals, timestamps and device positions were excluded as predictors.

Model: Random Forest, 200 trees, maximum depth 8, minimum leaf size 5, balanced class weights, seed 42. No hyperparameter search. Three session-grouped folds: one whole recording from each condition held out per fold, remaining recordings used for fitting. No recording appears in both training and testing within a fold. Metrics pool the out-of-fold window predictions; neighboring windows remain correlated, so 436 windows are not 436 independent experiments. Only nine recording sessions and two dates are represented. Date, placement, Wi-Fi conditions and subject differences may confound performance. This is exploratory cross-validation, not a final untouched test set.

Saved model files were subsequently fitted on all retained windows for reproducibility. Their evaluation is the grouped cross-validation above, not a new independent evaluation of the final fitted models. Both are marked preliminary and remain undeployed.

## Next steps

1. Keep the hotspot, boards, laptop and door position fixed. Confirm the exact wall and device layout, and whether it changed between recording dates.
2. Before another long collection, compare short repeated empty/still/walking trials in a single fixed setup. Check per-node amplitude and RSSI stability; separate packet-source or receiver-gain changes from human movement if the firmware exposes that information.
3. If separation is poor even within the same setup, test movement without a wall to establish a hardware baseline, then reintroduce the wall.
4. Collect more independent sessions only after these checks, with every condition represented on each day. Preserve an untouched future test set.

## Exclusions

- empty_room_20260919_223035.jsonl: No confirmed label metadata
- person_still_20260919_223406.jsonl: No confirmed label metadata
- person_walking_20260919T170514Z.jsonl: User requested a new recording after an apparent power interruption; full duration not verified.
- rec_1789043567.jsonl: No confirmed label metadata
- rec_1789838344.jsonl: Browser-started session: condition throughout full duration not confirmed; retained for review.

The manually named empty_room_20260919_223035 and person_still_20260919_223406 recordings were not assigned ground truth from filenames alone. They can be reviewed once their conditions are confirmed.
