import pytest


def _spark_disponivel() -> tuple[bool, str]:
    try:
        import importlib.util
        if importlib.util.find_spec("pyspark") is None:
            return False, "pyspark nao instalado"
        if importlib.util.find_spec("delta") is None:
            return False, "delta-spark nao instalado"
        return True, ""
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


@pytest.fixture(scope="session")
def spark():
    ok, motivo = _spark_disponivel()
    if not ok:
        pytest.skip(f"Spark indisponivel neste ambiente: {motivo}")
    try:
        from src.common.spark_session import get_spark
    except Exception as exc:
        pytest.skip(f"Spark indisponivel neste ambiente: {exc}")
        return
    try:
        session = get_spark("pytest")
    except Exception as exc:
        pytest.skip(f"Spark nao iniciou (sem Java/Hadoop?): {exc}")
        return
    yield session
    try:
        session.stop()
    except Exception:
        pass
