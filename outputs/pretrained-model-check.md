# Pretrained model compatibility check

Checked: 2026-09-14
Source: https://huggingface.co/ruvnet/wifi-densepose-pretrained
Repository revision: b24f225f1a8dd6f9614b7813b81df2cc26398269

## Result
The published package is not a validated ready-to-use through-wall presence detector for this project. No model has been activated in the live Docker server.

- Downloaded and inspected model metadata, the presence head, and both encoder weight files.
- The v2 encoder accepts 8 standardized features and returns a unit-length 128-dimensional embedding. Its weights contain no nonfinite floating-point values.
- Its reported 82.33% result measures temporal-triplet embedding quality, not occupied-versus-empty accuracy. The publisher discloses one-room, one-recording training and retracts the older presence accuracy claim.
- The supplied presence head has 128 weights, bias 8.1883479034, and weight L2 norm 3.6677067826. If applied as a sigmoid linear classifier to the v2 encoder's unit-length embedding, its output is at least sigmoid(bias - weight_norm) = 0.9892350994. At a 0.5 threshold it always predicts present. This is a mathematical compatibility check, not a test on labeled room data. Pairing the older head with v2 is not a validated integration.
- The generic model.safetensors file contains NUL padding in the declared JSON header and failed strict JSON parsing. The v2 safetensors header parsed successfully. The v2 file SHA-256 is 183c988b918abad3cd7ae50af0fe1be9196d0353055ac6865345be2f7fdaed72; the published metrics list a different weights hash. The reason for that discrepancy is unresolved.

## Next step
Collect labeled, repeated recordings with fixed board/router positions: empty room, person standing still behind the test wall, person walking behind the test wall. Keep entire recording sessions separate between training and testing. Train a presence classifier and compare against a simple signal-feature baseline. Report false positives on empty-room sessions and missed detections on occupied sessions. Do not treat the displayed skeleton or person count as validated ground truth.

Both-node live CSI reception was verified earlier in this task. No new ground-truth labels were inferred or fabricated during this review.
