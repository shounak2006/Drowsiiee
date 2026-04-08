import numpy as np
import matplotlib.pyplot as plt

# Example inputs (must be collected from your system)
# y_true: 1 = drowsy, 0 = alert
# ear_scores: EAR values per frame

y_true = np.array(y_true)
ear_scores = np.array(ear_scores)

thresholds = np.arange(0.15, 0.40, 0.01)

fprs, tprs = [], []

for t in thresholds:
    preds = (ear_scores < t).astype(int)

    tp = np.sum((preds == 1) & (y_true == 1))
    fp = np.sum((preds == 1) & (y_true == 0))
    tn = np.sum((preds == 0) & (y_true == 0))
    fn = np.sum((preds == 0) & (y_true == 1))

    fpr = fp / (fp + tn + 1e-9)
    tpr = tp / (tp + fn + 1e-9)

    fprs.append(fpr)
    tprs.append(tpr)

# Plot
plt.figure()
plt.plot(fprs, tprs, marker='o')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve — EAR Threshold Calibration")

# Highlight threshold ~0.25
idx = np.argmin(np.abs(thresholds - 0.25))
plt.scatter(fprs[idx], tprs[idx], color='red', label='Threshold=0.25')

plt.legend()
plt.grid()
plt.savefig("roc_curve.png", dpi=300)
plt.show()