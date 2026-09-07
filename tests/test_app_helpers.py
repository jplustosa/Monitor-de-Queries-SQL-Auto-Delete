from pathlib import Path


def test_environment_template_exists():
    env_example = Path(__file__).parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "ORACLE_USER=" in content
    assert "ORACLE_PASSWORD=" in content
    assert "ORACLE_DSN=" in content
    assert "usuario_db" not in content
    assert "senhadb" not in content


def test_query_file_is_decoded_as_utf8(tmp_path):
    path = tmp_path / "query.txt"
    path.write_text("SELECT 'ação' FROM DUAL", encoding="utf-8")

    import app

    assert app.extrair_query_do_arquivo(path) == "SELECT 'ação' FROM DUAL"


def test_query_file_supports_cp1252(tmp_path):
    path = tmp_path / "query.txt"
    path.write_bytes("SELECT 'ação' FROM DUAL".encode("cp1252"))

    import app

    assert app.extrair_query_do_arquivo(path) == "SELECT 'ação' FROM DUAL"
