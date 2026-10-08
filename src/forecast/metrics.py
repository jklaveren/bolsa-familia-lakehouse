"""RMSE/MAE/MAPE — mesmas metricas usadas no backtesting do projeto
Pluviometro (BRISA), reaproveitadas aqui para comparar VAR vs. rede neural
(Secao 10.3)."""
import numpy as np


def rmse(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def report(y_true, y_pred) -> dict:
    return {"rmse": rmse(y_true, y_pred), "mae": mae(y_true, y_pred), "mape": mape(y_true, y_pred)}
