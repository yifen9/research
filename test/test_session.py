from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import research.agent.session as agent_session
from research.agent.audit import append_message, message_record
from research.agent.audit import session_dir
from research.agent.session import check_session
from research.agent.session import close_session
from research.agent.session import make_session
from research.agent.session import record_message
from research.agent.session import record_round
from research.agent.session import rotate_session
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


def template_text(title: str) -> str:
    return f"""# {title}

## Review

Done.

## Summary

State.

## Next

Continue.

## Risk

None.

## Choice

- Continue.
"""


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

    def test_id(self) -> None:
        data = message_record("user", "secret=low", "chat", "run-1")
        prev = sha256(f"{data['time']}\nuser\nchat\nsecret=low".encode("utf-8")).hexdigest()

        self.assertNotEqual(data["message_id"], prev)

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

    def test_round(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round", "run-1")
            record_round(root, "architect", name, "omo", "hello", "answer", "test", "run-2")
            folder = root / "out" / "agent" / "session" / "architect" / name
            data = [item for item in read_jsonl(str(folder / "message.jsonl")) if item["kind"] == "round"]
            vector = [item for item in read_jsonl(str(root / "out" / "agent" / "vector" / "local.jsonl")) if item["meta"]["kind"] == "round"]

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["part"], "user")
        self.assertEqual(data[1]["part"], "ai")
        self.assertEqual(data[0]["round_id"], data[1]["round_id"])
        self.assertNotEqual(data[0]["round_id"], "[REDACTED]")
        self.assertEqual(vector[0]["meta"]["round_id"], data[0]["round_id"])
        self.assertEqual(vector[1]["meta"]["backend"], "omo")

    def test_fail(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round Fail", "run-1")

            with self.assertRaises(ValueError):
                record_round(root, "architect", name, "other", "hello", "answer", "test", "run-2")

            with self.assertRaises(ValueError):
                record_round(root, "architect", name, "omo", "", "answer", "test", "run-3")

            with self.assertRaises(ValueError):
                record_round(root, "architect", name, "omo", "hello", "answer", "", "run-4")

    def test_bad(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round Check", "run-1")
            item = message_record("user", "hello", "round", "run-2")
            item["round_id"] = "round-1"
            item["part"] = "user"
            item["source"] = "test"
            item["backend"] = "omo"
            record_message(root, "architect", name, item)
            data = check_session(root, "architect", name)

        self.assertIn("round", data)

    def test_actor(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round Actor", "run-1")
            user = message_record("ai", "hello", "round", "run-2")
            ai = message_record("user", "answer", "round", "run-2")
            for part, item in [("user", user), ("ai", ai)]:
                item["round_id"] = "round-1"
                item["part"] = part
                item["source"] = "test"
                item["backend"] = "omo"
                record_message(root, "architect", name, item)
            data = check_session(root, "architect", name)

        self.assertIn("round", data)

    def test_vector(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round Vector", "run-1")
            folder = root / "out" / "agent" / "session" / "architect" / name
            save = agent_session.add_message

            def fail_add(root: Path, role: str, name: str, data: dict[str, object]) -> str:
                raise OSError("vector")

            agent_session.add_message = fail_add
            try:
                with self.assertRaises(OSError):
                    record_round(root, "architect", name, "omo", "hello", "answer", "test", "run-2")
            finally:
                agent_session.add_message = save
            data = [item for item in read_jsonl(str(folder / "message.jsonl")) if item["kind"] == "round"]
            bad = check_session(root, "architect", name)

        self.assertEqual(len(data), 2)
        self.assertNotIn("round", bad)
        self.assertIn("vector", bad)

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

    def test_close(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Close", "run-1")

            with self.assertRaises(ValueError):
                close_session(root, "architect", name, "# Memory", "summary", "run-2")

            output = close_session(root, "architect", name, template_text("Memory"), "summary", "run-3")

        self.assertTrue(output)

    def test_rotate(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Rotate", "run-1")

            with self.assertRaises(ValueError):
                rotate_session(root, "architect", name, template_text("Memory"), "summary", "# Handoff", "Next", "run-2")

            new_name, output = rotate_session(
                root,
                "architect",
                name,
                template_text("Memory"),
                "summary",
                template_text("Handoff"),
                "Next",
                "run-3",
            )

        self.assertIn("next", new_name)
        self.assertTrue(output)


if __name__ == "__main__":
    unittest.main()
