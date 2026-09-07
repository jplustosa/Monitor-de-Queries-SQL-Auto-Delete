from pathlib import Path

import app


def test_extract_query_supports_utf8(tmp_path: Path):
    path = tmp_path / "query.txt"
    path.write_text("SELECT 1 FROM DUAL", encoding="utf-8")

    assert app.extrair_query_do_arquivo(path) == "SELECT 1 FROM DUAL"


def test_extract_query_supports_cp1252(tmp_path: Path):
    path = tmp_path / "query.txt"
    path.write_bytes("SELECT 'ação' FROM DUAL".encode("cp1252"))

    assert app.extrair_query_do_arquivo(path) == "SELECT 'ação' FROM DUAL"
