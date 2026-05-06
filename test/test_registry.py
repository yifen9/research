from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent.backend import BackendSpec, ConfigItem
from research.agent.check import check_backend
from research.agent.registry import active_backend
from research.agent.registry import part_list
from research.agent.registry import path_value
from research.agent.registry import role_check
from research.agent.registry import vector_conf
from research.agent.registry import vector_path
from research.agent.render import render_item
from research.io.yaml import write_yaml
from research.util.logger import make_logger
from script.rule.check import check_registry
from script.rule.check import check_root


def write_conf(root: Path) -> None:
    folder = root / "config"
    folder.mkdir(parents=True, exist_ok=True)
    write_yaml(
        str(folder / "agent.yaml"),
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


def write_rule(root: Path) -> None:
    folder = root / "config" / "rule"
    folder.mkdir(parents=True, exist_ok=True)
    write_yaml(
        str(folder / "registry.yaml"),
        {
            "registry": {
                "role": {
                    "allow": ["architect"],
                    "template_part": ["Review", "Summary"],
                },
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
                "state": {"allow": ["active", "closed", "retired"]},
                "check": {"allow": ["rule", "test"]},
            },
        },
    )


class AgentRegistryTest(unittest.TestCase):
    def test_config(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            data = vector_conf(root)
            active = active_backend(root)

        self.assertEqual(active, "omo")
        self.assertEqual(data["backend"], "local-jsonl")

    def test_role(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            role_check(root, "architect")

            with self.assertRaises(ValueError):
                role_check(root, "writer")

    def test_part(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            data = part_list(root)

        self.assertEqual(data, ["Review", "Summary"])

    def test_unknown(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            conf = root / "config" / "agent.yaml"
            write_yaml(
                str(conf),
                {
                    "backend": {"active": "omo"},
                    "session": {
                        "role": {"active": "architect"},
                        "vector": {
                            "backend": "other",
                            "failure": "fail",
                            "required": True,
                        },
                    },
                },
            )

            with self.assertRaises(KeyError):
                vector_conf(root)

    def test_required(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            conf = root / "config" / "agent.yaml"
            write_yaml(
                str(conf),
                {
                    "backend": {"active": "omo"},
                    "session": {
                        "role": {"active": "architect"},
                        "vector": {
                            "backend": "qdrant-local",
                            "failure": "fail",
                            "required": True,
                        },
                    },
                },
            )

            with self.assertRaises(KeyError):
                vector_conf(root)

    def test_fail(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            conf = root / "config" / "agent.yaml"

            write_yaml(
                str(conf),
                {
                    "backend": {"active": "omo"},
                    "session": {
                        "role": {"active": "architect"},
                        "vector": {
                            "backend": "local-jsonl",
                            "failure": "fail",
                            "required": False,
                        },
                    },
                },
            )
            with self.assertRaises(ValueError):
                vector_conf(root)

            write_yaml(
                str(conf),
                {
                    "backend": {"active": "omo"},
                    "session": {
                        "role": {"active": "architect"},
                        "vector": {
                            "backend": "local-jsonl",
                            "failure": "warn",
                            "required": True,
                        },
                    },
                },
            )
            with self.assertRaises(ValueError):
                vector_conf(root)

    def test_root(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            data = path_value(root, "session")

        self.assertEqual(data.name, "session")

    def test_path(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            write_yaml(
                str(root / "config" / "rule" / "registry.yaml"),
                {
                    "registry": {
                        "role": {"allow": ["architect"], "template_part": ["Review"]},
                        "path": {
                            "session": "../bad",
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
                            },
                            "failure": ["fail"],
                        },
                        "state": {"allow": ["active"]},
                        "check": {"allow": ["rule"]},
                    },
                },
            )

            with self.assertRaises(ValueError):
                path_value(root, "session")

    def test_vector(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            write_yaml(
                str(root / "config" / "rule" / "registry.yaml"),
                {
                    "registry": {
                        "role": {"allow": ["architect"], "template_part": ["Review"]},
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
                                    "path": "../bad",
                                    "require": [],
                                },
                            },
                            "failure": ["fail"],
                        },
                        "state": {"allow": ["active"]},
                        "check": {"allow": ["rule"]},
                    },
                },
            )
            data = vector_conf(root)

            with self.assertRaises(ValueError):
                vector_path(root, data)

    def test_name(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_conf(root)
            write_rule(root)
            write_yaml(
                str(root / "config" / "rule" / "registry.yaml"),
                {
                    "registry": {
                        "role": {"allow": ["../bad"], "template_part": ["Review"]},
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
                            },
                            "failure": ["fail"],
                        },
                        "state": {"allow": ["active"]},
                        "check": {"allow": ["rule"]},
                    },
                },
            )

            with self.assertRaises(ValueError):
                role_check(root, "../bad")

    def test_bad(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            data = check_registry(root, {"registry": {"role": []}})

        self.assertTrue(data)

    def test_check(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "config" / "rule"
            folder.mkdir(parents=True, exist_ok=True)
            write_yaml(str(folder / "index.yaml"), {"rule": ["code", "name", "file", "config", "design", "agent", "ai", "mode", "registry"], "word": ["core"]})
            source = Path("/workspace/config/rule")
            for name in ["code", "name", "file", "config", "design", "agent", "ai", "mode"]:
                (folder / f"{name}.yaml").write_text((source / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            word = folder / "word"
            word.mkdir(parents=True, exist_ok=True)
            (word / "core.yaml").write_text((source / "word" / "core.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            write_yaml(str(folder / "registry.yaml"), {"registry": {"role": []}})
            data = check_root(root, make_logger([]))

        self.assertTrue(data)

    def test_target(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "agent" / "backend" / "omo" / "template"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "source.txt").write_text("ok", encoding="utf-8")
            render_item(
                root, "omo", ConfigItem(target="out.txt", template="source.txt")
            )

            with self.assertRaises(ValueError):
                render_item(
                    root, "omo", ConfigItem(target="../bad", template="source.txt")
                )

            with self.assertRaises(ValueError):
                render_item(
                    root, "omo", ConfigItem(target="out.txt", template="../bad")
                )

    def test_round(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "agent" / "backend" / "omo" / "template"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "opencode.json").write_text(
                """{
  "plugin": [
    [
      "./.opencode/plugins/session-round.mjs",
      {
        "role": "architect",
        "source_prefix": "opencode",
        "command": ["uv", "run", "python", "script/agent/session/auto_round.py"],
        "limit": 20,
        "max_bytes": 65536
      }
    ]
  ]
}
""",
                encoding="utf-8",
            )
            (folder / "session-round.mjs").write_text("plugin\n", encoding="utf-8")
            data = BackendSpec(
                name="omo",
                part="omo",
                config=[
                    ConfigItem(target="opencode.json", template="opencode.json"),
                    ConfigItem(
                        target=".opencode/plugins/session-round.mjs",
                        template="session-round.mjs",
                    ),
                ],
                check=[],
            )

            bad = check_backend(root, data)
            self.assertIn("config:opencode.json", bad)
            self.assertIn("config:.opencode/plugins/session-round.mjs", bad)
            self.assertIn("auto-round:plugin", bad)

            render_item(root, "omo", data.config[0])
            render_item(root, "omo", data.config[1])
            self.assertEqual(check_backend(root, data), [])

            (root / "opencode.json").write_text(
                """{
  "plugin": [
    [
      "./.opencode/plugins/session-round.mjs",
      {
        "role": "writer",
        "source_prefix": "other",
        "command": ["node", "other.js"],
        "limit": 0,
        "max_bytes": 0
      }
    ]
  ]
}
""",
                encoding="utf-8",
            )
            bad = check_backend(root, data)

        self.assertIn("config:opencode.json", bad)
        self.assertIn("auto-round:role", bad)
        self.assertIn("auto-round:source_prefix", bad)
        self.assertIn("auto-round:command", bad)
        self.assertIn("auto-round:limit", bad)
        self.assertIn("auto-round:max_bytes", bad)


if __name__ == "__main__":
    unittest.main()
