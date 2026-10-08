"""Cartao 2b — gate: tracking + registry do melhor modelo (stdlib only)."""
import json

from src.forecast.tracking import log_comparison, select_best_model


def _comparacao_fake():
    return {
        "n_pontos_serie": 12, "n_treino": 10, "n_teste": 2,
        "var": {"metricas": {"rmse": 10.0, "mae": 8.0, "mape": 5.0}},
        "rede_neural": {"metricas": {"rmse": 7.0, "mae": 6.0, "mape": 4.0}},
    }


def test_select_best_model_menor_rmse_vence():
    assert select_best_model(_comparacao_fake()) == "rede_neural"
    inv = _comparacao_fake()
    inv["var"]["metricas"]["rmse"] = 1.0
    assert select_best_model(inv) == "var"


def test_select_best_model_empate_prefere_var():
    c = _comparacao_fake()
    c["var"]["metricas"]["rmse"] = c["rede_neural"]["metricas"]["rmse"]
    assert select_best_model(c) == "var"


def test_log_comparison_grava_registry(tmp_path, monkeypatch):
    import src.forecast.tracking as tr
    monkeypatch.setattr(tr, "LOCAL_DIR", tmp_path)
    monkeypatch.setattr(tr, "REGISTRY_PATH", tmp_path / "best_model.json")
    payload = log_comparison(_comparacao_fake())
    assert payload["melhor_modelo"] == "rede_neural"
    reg = json.loads((tmp_path / "best_model.json").read_text(encoding="utf-8"))
    assert reg["melhor_modelo"] == "rede_neural"
    assert reg["metricas"]["rmse"] == 7.0
    runs = (tmp_path / "runs.jsonl").read_text(encoding="utf-8")
    assert "rede_neural" in runs


def test_log_comparison_com_evidencia_real():
    ev = json.loads((__import__("pathlib").Path(__file__).resolve().parent.parent
                     / "docs" / "evidencias" / "secao10_comparacao_modelos.json").read_text(encoding="utf-8"))
    assert select_best_model(ev) in ("var", "rede_neural")
    assert ev["rede_neural"]["metricas"]["rmse"] < ev["var"]["metricas"]["rmse"]
