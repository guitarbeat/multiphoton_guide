import numpy as np
from scipy.optimize import curve_fit

# Define the exponential function
def exp_func(x, a, b, c):
    return a * np.exp(b * x) + c

# Data points from the SOP values
x = np.array([0, 2000, 4000, 6000, 8000])
y = np.array([0.0, 0.2, 2.3, 4.8, 7.5])

# Fit the data
popt, pcov = curve_fit(exp_func, x, y, p0=[0.1, 0.001, 0.0], maxfev=10000)
a, b, c = popt

# Calculate R-squared
y_pred = exp_func(x, a, b, c)
ss_total = np.sum((y - np.mean(y)) ** 2)
ss_residual = np.sum((y - y_pred) ** 2)
r_squared = 1 - (ss_residual / ss_total)

# Print results
print(f"Exponential fit: y = {a:.4f} * exp({b:.6f} * x) + {c:.4f}")
print(f"R²: {r_squared:.6f}")
print("\nData points vs predicted values:")
for i in range(len(x)):
    print(f"x = {x[i]:5}: Actual = {y[i]:.4f}, Predicted = {y_pred[i]:.4f}, Diff = {abs(y[i] - y_pred[i]):.4f}") 