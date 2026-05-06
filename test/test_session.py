from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import research.agent.session as agent_session
import research.agent.vector as agent_vector
from script.agent.session.auto_round import read_data
from research.agent.audit import append_message, message_record
from research.agent.audit import session_dir
from research.agent.session import check_session
from research.agent.session import active_name
from research.agent.session import close_session
from research.agent.session import heartbeat
from research.agent.session import initial_text
from research.agent.session import make_session
from research.agent.session import record_active
from research.agent.session import record_message
from research.agent.session import record_round
from research.agent.session import read_session
from research.agent.session import retire_session
from research.agent.session import rotate_session
from research.agent.session import write_session
from research.agent.handoff import handoff_path
from research.agent.memory import memory_path
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
                "role": {"active": "architect"},
                "vector": {
                    "backend": "local-jsonl",
                    "failure": "fail",
                    "required": True,
                },
            },
        },
    )
    rule = root / "config" / "rule"
    rule.mkdir(parents=True, exist_ok=True)
    write_yaml(
        str(rule / "registry.yaml"),
        {
            "registry": {
                "role": {
                    "allow": ["architect"],
                    "template_part": ["Review", "Summary", "Next", "Risk", "Choice"],
                },
                "state": {"allow": ["active", "closed", "retired"]},
                "path": {
                    "session": "out/agent/session",
                    "vector": "out/agent/vector",
                    "memory": "out/agent/memory",
                    "handoff": "out/agent/handoff",
                },
                "vector": {
                    "allow": {
                        "local-jsonl": {
                            "kind": "local-jsonl",
                            "path": "local.jsonl",
                            "require": [],
                        },
                        "qdrant-local": {
                            "kind": "qdrant",
                            "path": "qdrant",
                            "require": ["collection", "model"],
                        },
                    },
                    "failure": ["warn", "fail"],
                },
                "check": {"allow": ["rule", "test"]},
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
        prev = sha256(
            f"{data['time']}\nuser\nchat\nsecret=low".encode("utf-8")
        ).hexdigest()

        self.assertNotEqual(data["message_id"], prev)

    def test_heartbeat(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Heartbeat", "run-1")
            folder = root / "out" / "agent" / "session" / "architect" / name
            event_data = read_jsonl(str(folder / "event.jsonl"))
            vector_data = read_jsonl(
                str(root / "out" / "agent" / "vector" / "local.jsonl")
            )

        self.assertEqual(event_data[-1]["event"], "vector-heartbeat")
        self.assertEqual(vector_data[-1]["meta"]["kind"], "heartbeat")

    def test_active(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)

            with self.assertRaises(ValueError):
                active_name(root, "architect")

            name, _ = make_session(root, "architect", "Active", "run-1")
            data = active_name(root, "architect")

        self.assertEqual(data, name)

    def test_count(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            make_session(root, "architect", "One", "run-1")
            make_session(root, "architect", "Two", "run-2")

            with self.assertRaises(ValueError):
                active_name(root, "architect")

    def test_round(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round", "run-1")
            record_round(
                root, "architect", name, "omo", "hello", "answer", "test", "run-2"
            )
            folder = root / "out" / "agent" / "session" / "architect" / name
            data = [
                item
                for item in read_jsonl(str(folder / "message.jsonl"))
                if item["kind"] == "round"
            ]
            vector = [
                item
                for item in read_jsonl(
                    str(root / "out" / "agent" / "vector" / "local.jsonl")
                )
                if item["meta"]["kind"] == "round"
            ]

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["part"], "user")
        self.assertEqual(data[1]["part"], "ai")
        self.assertEqual(data[0]["round_id"], data[1]["round_id"])
        self.assertNotEqual(data[0]["round_id"], "[REDACTED]")
        self.assertEqual(vector[0]["meta"]["round_id"], data[0]["round_id"])
        self.assertEqual(vector[1]["meta"]["backend"], "omo")

    def test_auto(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Auto", "run-1")
            record_active(
                root,
                "architect",
                "auto-bind",
                "hello",
                "answer",
                "auto-source",
                "run-2",
            )
            record_active(
                root,
                "architect",
                "auto-bind",
                "hello",
                "answer",
                "auto-source",
                "run-3",
            )
            folder = root / "out" / "agent" / "session" / "architect" / name
            data = [
                item
                for item in read_jsonl(str(folder / "message.jsonl"))
                if item["kind"] == "round"
            ]
            session = read_session(root, "architect", name)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["source"], "auto-source")
        self.assertEqual(session["bind"], ["auto-bind"])

    def test_bind(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "One", "run-1")
            other, _ = make_session(root, "architect", "Two", "run-2")

            with self.assertRaisesRegex(ValueError, "ambiguous bind target"):
                record_active(
                    root,
                    "architect",
                    "auto-bind",
                    "hello",
                    "answer",
                    "auto-source",
                    "run-3",
                )

            for name in [name, other]:
                session = read_session(root, "architect", name)
                folder = root / "out" / "agent" / "session" / "architect" / name
                data = [
                    item
                    for item in read_jsonl(str(folder / "message.jsonl"))
                    if item["kind"] == "round"
                ]
                self.assertEqual(session["bind"], [])
                self.assertEqual(data, [])

    def test_claim(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            make_session(root, "architect", "One", "run-1")
            record_active(
                root,
                "architect",
                "auto-bind",
                "hello",
                "answer",
                "auto-source-1",
                "run-2",
            )
            base = root / "out" / "agent" / "session" / "architect"
            name = next(
                path.name
                for path in base.iterdir()
                if path.is_dir()
                and read_session(root, "architect", path.name).get("bind")
                == ["auto-bind"]
            )
            make_session(root, "architect", "Two", "run-3")
            record_active(
                root,
                "architect",
                "auto-bind",
                "hello",
                "answer",
                "auto-source-2",
                "run-4",
            )
            folder = root / "out" / "agent" / "session" / "architect" / name
            data = [
                item
                for item in read_jsonl(str(folder / "message.jsonl"))
                if item["kind"] == "round"
            ]

        self.assertEqual(len(data), 4)

    def test_state(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            make_session(root, "architect", "Closed", "run-1")
            record_active(
                root,
                "architect",
                "closed-bind",
                "hello",
                "answer",
                "auto-source-1",
                "run-2",
            )
            base = root / "out" / "agent" / "session" / "architect"
            name = next(
                path.name
                for path in base.iterdir()
                if path.is_dir()
                and read_session(root, "architect", path.name).get("bind")
                == ["closed-bind"]
            )
            close_session(
                root, "architect", name, template_text("Memory"), "summary", "run-3"
            )
            make_session(root, "architect", "Other", "run-4")

            with self.assertRaises(ValueError):
                record_active(
                    root,
                    "architect",
                    "closed-bind",
                    "hello",
                    "answer",
                    "auto-source-2",
                    "run-5",
                )

            retired, _ = make_session(root, "architect", "Retired", "run-6")
            data = read_session(root, "architect", retired)
            data["bind"] = ["retired-bind"]
            write_session(root, "architect", retired, data)
            retire_session(root, "architect", retired, "mistake", "run-8")

            with self.assertRaises(ValueError):
                record_active(
                    root,
                    "architect",
                    "retired-bind",
                    "hello",
                    "answer",
                    "auto-source-4",
                    "run-9",
                )

            missing, _ = make_session(root, "architect", "Missing", "run-10")
            data = read_session(root, "architect", missing)
            data["bind"] = ["missing-bind"]
            write_session(root, "architect", missing, data)
            (session_dir(root, "architect", missing) / "session.yaml").unlink()

            with self.assertRaises((FileNotFoundError, ValueError)):
                record_active(
                    root,
                    "architect",
                    "missing-bind",
                    "hello",
                    "answer",
                    "auto-source-6",
                    "run-12",
                )

    def test_copy(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "One", "run-1")
            other, _ = make_session(root, "architect", "Two", "run-2")
            for name in [name, other]:
                data = read_session(root, "architect", name)
                data["bind"] = ["auto-bind"]
                write_session(root, "architect", name, data)

            with self.assertRaises(ValueError):
                record_active(
                    root,
                    "architect",
                    "auto-bind",
                    "hello",
                    "answer",
                    "auto-source",
                    "run-3",
                )

    def test_reject(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)

            with self.assertRaises(ValueError):
                record_active(
                    root,
                    "architect",
                    "",
                    "hello",
                    "answer",
                    "auto-source",
                    "run-1",
                )

            with self.assertRaisesRegex(ValueError, "no bind target"):
                record_active(
                    root,
                    "architect",
                    "auto-bind",
                    "hello",
                    "answer",
                    "auto-source",
                    "run-2",
                )

    def test_size(self) -> None:
        with self.assertRaises(ValueError):
            read_data(b'{"user_text":"hello","ai_text":"answer"}', 10)

    def test_fail(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Round Fail", "run-1")

            with self.assertRaises(ValueError):
                record_round(
                    root, "architect", name, "other", "hello", "answer", "test", "run-2"
                )

            with self.assertRaises(ValueError):
                record_round(
                    root, "architect", name, "omo", "", "answer", "test", "run-3"
                )

            with self.assertRaises(ValueError):
                record_round(
                    root, "architect", name, "omo", "hello", "answer", "", "run-4"
                )

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

            def fail_add(
                root: Path, role: str, name: str, data: dict[str, object]
            ) -> str:
                raise OSError("vector")

            agent_session.add_message = fail_add
            try:
                with self.assertRaises(OSError):
                    record_round(
                        root,
                        "architect",
                        name,
                        "omo",
                        "hello",
                        "answer",
                        "test",
                        "run-2",
                    )
            finally:
                agent_session.add_message = save
            data = [
                item
                for item in read_jsonl(str(folder / "message.jsonl"))
                if item["kind"] == "round"
            ]
            bad = check_session(root, "architect", name)

        self.assertEqual(len(data), 2)
        self.assertNotIn("round", bad)
        self.assertIn("vector", bad)

    def test_sync(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Vector Sync", "run-1")
            append_message(
                root,
                "architect",
                name,
                message_record("user", "sync me", "chat", "run-2"),
            )

            prev = check_session(root, "architect", name)
            heartbeat(root, "architect", name, "run-3", "2026-05-06T00:00:00+00:00")
            next = check_session(root, "architect", name)

        self.assertIn("vector", prev)
        self.assertNotIn("vector", next)

    def test_qdrant(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_yaml(
                str(root / "config" / "agent.yaml"),
                {
                    "backend": {"active": "omo"},
                    "session": {
                        "role": {"active": "architect"},
                        "vector": {
                            "backend": "qdrant-local",
                            "failure": "fail",
                            "required": True,
                            "collection": "agent",
                            "model": "test-model",
                        },
                    },
                },
            )
            data = agent_vector.read_conf(root)
            path = agent_vector.lock_path(root, data)
            output = root / "out" / "agent" / "vector" / "qdrant"

        self.assertEqual(path, output / ".vector.lock")
        self.assertIn(output, path.parents)

    def test_lock(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Lock", "run-1")
            data: list[Path] = []
            save = agent_vector.vector_lock

            class FakeLock:
                def __init__(self, path: Path) -> None:
                    self.path = path

                def __enter__(self) -> Path:
                    data.append(self.path)
                    return self.path

                def __exit__(self, *arg: object) -> None:
                    return None

            def make_lock(root: Path, item: dict[str, object]) -> FakeLock:
                return FakeLock(agent_vector.lock_path(root, item))

            agent_vector.vector_lock = make_lock
            try:
                agent_vector.check_store(root, "architect", name)
                agent_vector.add_text(
                    root, "architect", name, "plain text", {"kind": "plain"}
                )
                agent_vector.add_heartbeat(
                    root, "architect", name, "run-2", "2026-05-06T00:00:00+00:00"
                )
                agent_vector.add_message(
                    root,
                    "architect",
                    name,
                    message_record("user", "locked", "chat", "run-3"),
                )
                agent_vector.sync_message(root, "architect", name)
                agent_vector.missing_message(root, "architect", name)
            finally:
                agent_vector.vector_lock = save

        self.assertEqual(len(data), 6)
        self.assertTrue(all(path.name == "local.jsonl.lock" for path in data))

    def test_lifecycle(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            close_name, _ = make_session(root, "architect", "Close Lock", "run-1")
            retire_name, _ = make_session(root, "architect", "Retire Lock", "run-2")
            save = agent_session.check_store

            def fail_store(root: Path, role: str, name: str) -> object:
                raise OSError("vector")

            agent_session.check_store = fail_store
            try:
                with self.assertRaises(OSError):
                    close_session(
                        root,
                        "architect",
                        close_name,
                        template_text("Memory"),
                        "summary",
                        "run-3",
                    )
                with self.assertRaises(OSError):
                    retire_session(root, "architect", retire_name, "mistake", "run-4")
            finally:
                agent_session.check_store = save
            close_data = read_session(root, "architect", close_name)
            retire_data = read_session(root, "architect", retire_name)

        self.assertEqual(close_data["state"], "active")
        self.assertEqual(retire_data["state"], "active")

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

    def test_initial(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            text = initial_text(root, "architect")

        self.assertIn("out/agent/memory/architect.md", text)
        self.assertIn("out/agent/handoff/architect.md", text)
        self.assertIn("agent/core.md", text)

    def test_role(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)

            with self.assertRaises(ValueError):
                memory_path(root, "../bad")

            with self.assertRaises(ValueError):
                handoff_path(root, "../bad")

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

            output = close_session(
                root, "architect", name, template_text("Memory"), "summary", "run-3"
            )

        self.assertTrue(output)

    def test_rotate(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            name, _ = make_session(root, "architect", "Rotate", "run-1")

            with self.assertRaises(ValueError):
                rotate_session(
                    root,
                    "architect",
                    name,
                    template_text("Memory"),
                    "summary",
                    "# Handoff",
                    "Next",
                    "run-2",
                )

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
