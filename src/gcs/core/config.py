import yaml


def load_config(path="config/default.yaml"):
    """Read a YAML file and return its contents as a dict."""

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config