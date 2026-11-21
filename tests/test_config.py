from gcs.core.config import load_config


def test_load_config_reads_input_rate(tmp_path):
    cfg_file = tmp_path / "test.yaml"
    cfg_file.write_text("input:\n  rate_hz: 25\n", encoding="utf-8")

    config = load_config(cfg_file)

    assert config["input"]["rate_hz"] == 25