"""Cartao 2b — tracking MLflow da comparacao VAR x rede neural + registry local.

Sem servidor MLflow: se `mlflow` nao estiver instalado, grava JSONL local em
`mlruns-local/` (mesmo contrato: params + metrics por modelo + best_model.json).
Com mlflow instalado, loga no tracking URI padrao (mlruns/) e registra o melhor
modelo (menor RMSE) como artefato + `best_model.json` para o gate de testes.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LOCAL_DIR = REPO / "mlruns-local"
REGISTRY_PATH = REPO / "mlruns-local" / "best_model.json"


def select_best_model(comparacao: dict) -> str:
    """Retorna 'var' ou 'rede_neural' — menor RMSE vence. Empate: VAR (mais simples)."""
    rmse_var = comparacao["var"]["metricas"]["rmse"]
    rmse_nn = comparacao["rede_neural"]["metricas"]["rmse"]
    return "var" if rmse_var <= rmse_nn else "rede_neural"


def _payload(comparacao: dict, melhor: str) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "n_pontos_serie": comparacao.get("n_pontos_serie"),
        "n_treino": comparacao.get("n_treino"),
        "n_teste": comparacao.get("n_teste"),
        "var": comparacao["var"]["metricas"],
        "rede_neural": comparacao["rede_neural"]["metricas"],
        "melhor_modelo": melhor,
    }


def log_comparison(comparacao: dict, tracking_uri: str | None = None) -> dict:
    """Loga a comparacao (MLflow se disponivel, senao JSONL local) e atualiza o registry."""
    melhor = select_best_model(comparacao)
    payload = _payload(comparacao, melhor)

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    with (LOCAL_DIR / "runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    REGISTRY_PATH.write_text(
        json.dumps({"melhor_modelo": melhor, "metricas": payload[melhor],
                    "atualizado_em": payload["ts"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # MLflow real (opcional): nao quebra se ausente.
    try:
        import mlflow  # type: ignore
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment("bolsa-familia-var-vs-nn")
        with mlflow.start_run():
            mlflow.log_param("n_pontos_serie", comparacao.get("n_pontos_serie"))
            mlflow.log_param("n_treino", comparacao.get("n_treino"))
            mlflow.log_param("n_teste", comparacao.get("n_teste"))
            for modelo in ("var", "rede_neural"):
                for k, v in comparacao[modelo]["metricas"].items():
                    mlflow.log_metric(f"{modelo}_{k}", float(v))
            mlflow.log_metric("melhor_e_var", 1.0 if melhor == "var" else 0.0)
            mlflow.log_dict(payload, "comparacao.json")
        payload["mlflow"] = True
    except Exception:
        payload["mlflow"] = False

    return payload
