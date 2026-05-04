import pathlib
import sys
import yaml


def read_yaml(path):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data


def read_text(path):
    text = path.read_text(encoding="utf-8")
    return text


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bind_text(text, data):
    out = text
    for name, value in data["version"].items():
        key = "{{" + name + "}}"
        out = out.replace(key, str(value))
    return out


def make_file(root):
    conf = root / "infra" / "docker" / "profile" / "full" / "build.yaml"
    data = read_yaml(conf)
    body = []
    body.append(f"FROM {data['image']['base']}\n")

    for name in data["part"]:
        path = root / "infra" / "docker" / "part" / name / "Dockerfile"
        text = read_text(path)
        body.append(bind_text(text, data))
        body.append("")

    body.append('WORKDIR /workspace\n')
    return "\n".join(body)


def main(argv):
    if argv.__len__() != 2:
        sys.stderr.write("usage: write_docker.py ROOT\n")
        sys.exit(1)

    root = pathlib.Path(argv[1])
    text = make_file(root)
    path = root / "infra" / "docker" / "profile" / "full" / "Dockerfile"
    write_text(path, text)


if __name__ == "__main__":
    main(sys.argv)
