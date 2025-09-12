import os
import sys
import types
from unittest.mock import patch, Mock

# Ensure src/ is importable for tests
sys.path.append('src')

# Provide lightweight stubs for modules that tools.py imports but tests don't need
def _install_stub(name, attrs=None):
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod

class _DummyFastMCP:
    def __init__(self, *a, **k):
        pass
    def tool(self, *a, **k):
        def dec(f):
            return f
        return dec
    def run(self, *a, **k):
        pass

_install_stub('fastmcp', { 'FastMCP': _DummyFastMCP })
_install_stub('langgraph')
class _DummyCommand(dict):
    def __init__(self, *a, **k):
        super().__init__()
        for k2, v2 in k.items():
            setattr(self, k2, v2)
_install_stub('langgraph.types', { 'Command': _DummyCommand })
_install_stub('langgraph.prebuilt', { 'InjectedState': object })
_install_stub('langgraph.graph')
_install_stub('langgraph.graph.message', { 'add_messages': lambda x: x })


def test_create_image_orientation_mapping(tmp_path, monkeypatch):
    # Arrange
    # Ensure content dir exists
    from pathlib import Path
    import toml
    cfg_path = Path('config.toml')
    cfg = toml.load(cfg_path)
    story = cfg["story"]["current_story"]
    images_dir = Path(cfg["paths"]["content_dir"]) / story / cfg["paths"]["images_dir"]
    images_dir.mkdir(parents=True, exist_ok=True)

    # Mock DALLE generator to avoid API
    with patch('src.tools._generate_image_dalle', return_value='https://example.com/fake.png'):
        # Mock network download
        fake_resp = Mock()
        fake_resp.content = b"PNGDATA"
        fake_resp.raise_for_status = Mock()
        with patch('src.tools.requests.get', return_value=fake_resp):
            from src.tools import create_image

            # Act
            res_square = create_image("test image square", orientation="square")
            res_land = create_image("test image landscape", orientation="landscape")
            res_port = create_image("test image portrait", orientation="portrait")

    # Assert
    assert "Orientation: square (1024x1024)" in res_square
    assert "Orientation: landscape (1792x1024)" in res_land
    assert "Orientation: portrait (1024x1792)" in res_port


def test_create_image_handles_dalle_rejection(monkeypatch):
    # If openai.BadRequestError is available, raise it; otherwise, raise a generic Exception
    try:
        from openai import BadRequestError  # type: ignore
        rejection_exc = BadRequestError(message="Prompt violates safety policy", request=None)
    except Exception:
        rejection_exc = Exception("Prompt violates safety policy")

    with patch('src.tools._generate_image_dalle', side_effect=rejection_exc):
        from src.tools import create_image
        msg = create_image("public figure doing illegal thing", orientation="landscape")

    assert "ERROR: DALLE request" in msg
    assert "Advice:" in msg
