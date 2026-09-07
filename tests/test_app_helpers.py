from pathlib import Path


def test_environment_template_exists():
    env_example = Path(__file__).parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "ORACLE_USER=" in content
    assert "ORACLE_PASSWORD=" in content
    assert "ORACLE_DSN=" in content
    assert "senhadb" not in content
