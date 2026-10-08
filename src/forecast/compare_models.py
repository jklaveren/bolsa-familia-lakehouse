"""Comparacao VAR vs. rede neural simples (Secao 10.3 do design doc).

Mesmo split treino/teste, mesmas metricas (RMSE/MAE/MAPE), reportadas lado a
lado — sem alegar qual "e melhor" sem o numero que sustente a afirmacao.
Serie curta (~poucos pontos trimestrais): e esperado, e sera reportado com
transparencia, que o VAR performe igual ou melhor que a rede neural nessa
escala (ver "Limitacao honesta" na Secao 10.3 do documento).
"""
import argparse
import json

import numpy as np
import pandas as pd

from src.forecast.metrics import report
from src.forecast.series import build_national_series

np.random.seed(42)


def split_train_test(df: pd.DataFrame, n_test: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(df) <= n_test + 2:
        raise ValueError(
            f"Serie tem so {len(df)} pontos — poucos para reservar {n_test} para teste "
            "com um minimo razoavel de treino. Rode com mais competencias ingeridas."
        )
    return df.iloc[:-n_test], df.iloc[-n_test:]


def run_var(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    from statsmodels.tsa.api import VAR

    cols = ["valor_total", "beneficiarios_unicos"]
    model = VAR(train[cols])

    # Serie curta (poucos pontos trimestrais): o maxlags "ideal" costuma
    # exceder o que da pra estimar com poucas observacoes e 2 variaveis.
    # Tenta do maior valor plausivel pro menor ate achar um que rode.
    maxlags_tentativa = max(1, min(4, len(train) // 3))
    lag_order = None
    for tentativa in range(maxlags_tentativa, 0, -1):
        try:
            selected = model.select_order(maxlags=tentativa)
            lag_order = selected.aic or 1
            break
        except ValueError:
            continue
    if lag_order is None:
        lag_order = 1

    fitted = model.fit(lag_order)
    forecast = fitted.forecast(train[cols].values[-lag_order:], steps=len(test))
    pred_valor_total = forecast[:, cols.index("valor_total")]

    metrics = report(test["valor_total"].values, pred_valor_total)
    return {"lag_order": lag_order, "predicoes": pred_valor_total.tolist(), "metricas": metrics}


def run_rede_neural(train: pd.DataFrame, test: pd.DataFrame, lag_order: int) -> dict:
    import tensorflow as tf
    from sklearn.preprocessing import StandardScaler

    tf.random.set_seed(42)
    tf.get_logger().setLevel("ERROR")

    serie = train["valor_total"].values
    scaler = StandardScaler()
    serie_scaled = scaler.fit_transform(serie.reshape(-1, 1)).flatten()

    X, y = [], []
    for i in range(lag_order, len(serie_scaled)):
        X.append(serie_scaled[i - lag_order : i])
        y.append(serie_scaled[i])
    X, y = np.array(X), np.array(y)

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(lag_order,)),
            tf.keras.layers.Dense(8, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=200, verbose=0)

    historico = list(serie_scaled[-lag_order:])
    preds_scaled = []
    for _ in range(len(test)):
        x = np.array(historico[-lag_order:]).reshape(1, lag_order)
        pred = model.predict(x, verbose=0)[0, 0]
        preds_scaled.append(pred)
        historico.append(pred)

    preds = scaler.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten()
    metrics = report(test["valor_total"].values, preds)
    return {"lag_order": lag_order, "predicoes": preds.tolist(), "metricas": metrics}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-test", type=int, default=3)
    args = parser.parse_args()

    df = build_national_series()
    print(f"Serie: {len(df)} pontos, {df.index.min().date()} a {df.index.max().date()}")

    train, test = split_train_test(df, args.n_test)
    print(f"Treino: {len(train)} pontos | Teste: {len(test)} pontos")

    resultado_var = run_var(train, test)
    resultado_nn = run_rede_neural(train, test, lag_order=resultado_var["lag_order"])

    print("\n=== Resultado (mesmo split treino/teste, mesmas metricas) ===")
    print(f"VAR (lag={resultado_var['lag_order']}): {resultado_var['metricas']}")
    print(f"Rede neural (lag={resultado_nn['lag_order']}): {resultado_nn['metricas']}")

    saida = {
        "n_pontos_serie": len(df),
        "n_treino": len(train),
        "n_teste": len(test),
        "valores_reais_teste": test["valor_total"].tolist(),
        "var": resultado_var,
        "rede_neural": resultado_nn,
    }
    with open("docs/evidencias/secao10_comparacao_modelos.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, indent=2, ensure_ascii=False, default=str)
    print("\nResultado salvo em docs/evidencias/secao10_comparacao_modelos.json")

    # Cartao 2b: tracking MLflow (ou JSONL local) + registry do melhor modelo.
    try:
        from src.forecast.tracking import log_comparison, select_best_model
        log_comparison(saida)
        print(f"Tracking OK — melhor modelo: {select_best_model(saida)} (ver mlruns-local/best_model.json)")
    except Exception as exc:
        print(f"Tracking pulado: {exc}")


if __name__ == "__main__":
    main()
