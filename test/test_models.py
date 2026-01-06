# test.test_models
import tempfile
from pathlib import Path
import pytest
from src.models import Directory, File, Link, NodeType, Node


def complex_directory_factory():
    """Creates a deep, complex structure for testing."""
    return Directory(
        name="root",
        description="The root folder",
        children=[
            File(name="config.json", file=Path("/etc/config.json")),
            Link(name="Google", url="https://google.com"),
            Directory(
                name="src",
                children=[
                    File(name="main.py", file=Path("./src/main.py")),
                    Directory(name="tests", children=[])
                ]
            )
        ]
    )

@pytest.mark.parametrize("original_obj", [
    File(name="test.txt", file=Path("/tmp/test.txt")),
    Link(name="Localhost", description="Home", url="http://127.0.0.1:8000"),
    Directory(name="empty_dir"),
    complex_directory_factory()
])
def test_json_serialization_cycle(original_obj: NodeType):
    """
    Verifies that an object can be serialized to JSON and deserialized
    back into an identical object.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file = tmpdir / "test.json"
        original_obj.save_json(file)
        restored_obj = Node.load_json(file)

        assert type(original_obj) is type(restored_obj)
        assert original_obj == restored_obj

