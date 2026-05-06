from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent.audit import append_message, message_record
from research.agent.audit import session_dir
from research.agent.session import make_session
from research.agent.store import LocalJsonlStore
from research.io.jsonl import read_jsonl
from research.io.yaml import write_yaml
from research.util.run import env_value


def write_conf(root: Path) -> None:
    folder = root / "config"
    folder.mkdir(parents=True, exist_ok=True)
    write_yaml(
        str(root / "config" / "agent.yaml"),
        {
            "backend": {"active": "omo"},
            "session": {
                "vector": {
                    "backend": "local-jsonl",
                    "failure": "fail",
                    "required": True,
                },
            },
        },
    )


class AgentSessionTest(unittest.TestCase):
    def test_redact(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Redaction", "run-1")
            path = append_message(
                root,
                "architect",
                name,
                message_record(
                    "user",
                    "token=abc123 password=hunter2 hello",
                    "chat",
                    "run-2",
                ),
            )
            data = read_jsonl(str(path))

        self.assertEqual(data[-1]["text"], "token=[REDACTED] password=[REDACTED] hello")
        self.assertEqual(data[-1]["run"], "run-2")

    def test_heartbeat(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Heartbeat", "run-1")
            folder = root / "out" / "agent" / "session" / "architect" / name
            event_data = read_jsonl(str(folder / "event.jsonl"))
            vector_data = read_jsonl(str(root / "out" / "agent" / "vector" / "local.jsonl"))

        self.assertEqual(event_data[-1]["event"], "vector-heartbeat")
        self.assertEqual(vector_data[-1]["meta"]["kind"], "heartbeat")

    def test_store(self) -> None:
        with TemporaryDirectory() as temp:
            store = LocalJsonlStore(Path(temp) / "store.jsonl")
            store.add("architect", "session heartbeat alpha beta", None)
            store.add("architect", "session heartbeat gamma delta", None)
            data = store.find("architect", "alpha", 5)

        self.assertEqual(data, ["session heartbeat alpha beta"])

    def test_path(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)

            with self.assertRaises(ValueError):
                session_dir(root, "architect", "../bad")

    def test_env(self) -> None:
        self.assertEqual(env_value("API_TOKEN", "abc123"), "[REDACTED]")
        self.assertEqual(env_value("NAME", "token=abc123 ok"), "token=[REDACTED] ok")


if __name__ == "__main__":
    unittest.main()
