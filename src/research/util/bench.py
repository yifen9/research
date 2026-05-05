from __future__ import annotations

from typing import Any


def check_item(item: dict[str, Any], metric: dict[str, float]) -> dict[str, Any]:
    name = item["metric"]

    if name not in metric:
        return {"metric": name, "status": "missing"}

    value = float(metric[name])
    output: dict[str, Any] = {"metric": name, "value": value}

    if "min" in item:
        output["min"] = item["min"]

        if value >= float(item["min"]):
            output["status"] = "pass"
        else:
            output["status"] = "fail"

        return output

    if "max" in item:
        output["max"] = item["max"]

        if value <= float(item["max"]):
            output["status"] = "pass"
        else:
            output["status"] = "fail"

        return output

    output["status"] = "no-threshold"
    return output


def check_bench(
    bench: list[dict[str, Any]],
    metric: dict[str, float],
) -> dict[str, Any]:
    output: list[dict[str, Any]] = []
    bad = 0

    for item in bench:
        result = check_item(item, metric)
        output.append(result)

        if result["status"] != "pass":
            bad += 1

    if bad == 0:
        status = "pass"
    else:
        status = "fail"

    return {
        "status": status,
        "data": output,
        "bad": bad,
    }
