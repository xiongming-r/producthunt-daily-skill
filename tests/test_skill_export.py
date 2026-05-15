from tools.export_producthunt_skill import export_skill, validate_export


def test_export_skill_creates_self_contained_package(tmp_path):
    destination = tmp_path / "producthunt-daily"

    export_skill(destination)

    assert (destination / "SKILL.md").exists()
    assert (destination / "README.md").exists()
    assert (destination / "references" / "config-reference.md").exists()
    assert (destination / "references" / "agent-templates.md").exists()
    assert (destination / "references" / "enrichment-prompt.md").exists()
    assert (destination / "scripts" / "setup.sh").exists()
    assert (destination / "scripts" / ".env.example").exists()
    assert (destination / "scripts" / "pyproject.toml").exists()
    assert (destination / "scripts" / "src" / "ph_daily" / "cli.py").exists()


def test_export_skill_excludes_runtime_artifacts(tmp_path):
    destination = tmp_path / "producthunt-daily"

    export_skill(destination)

    forbidden_names = {".git", ".DS_Store", "__pycache__"}
    exported_paths = {path.name for path in destination.rglob("*")}
    assert forbidden_names.isdisjoint(exported_paths)
    assert not list(destination.rglob("*.pyc"))
    assert not list(destination.rglob("*.egg-info"))


def test_validate_export_accepts_clean_package(tmp_path):
    destination = tmp_path / "producthunt-daily"
    export_skill(destination)

    validate_export(destination)


def test_validate_export_rejects_forbidden_artifact(tmp_path):
    destination = tmp_path / "producthunt-daily"
    export_skill(destination)
    (destination / ".DS_Store").write_text("noise", encoding="utf-8")

    try:
        validate_export(destination)
    except ValueError as exc:
        assert ".DS_Store" in str(exc)
    else:
        raise AssertionError("validate_export should reject forbidden artifacts")
