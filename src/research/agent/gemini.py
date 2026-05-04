from __future__ import annotations

from dataclasses import dataclass

from google import genai

from research.agent.provider import Req, Resp


@dataclass(slots=True)
class Gemini:
    model: str

    def send(self, req: Req) -> Resp:
        client = genai.Client()
        result = client.models.generate_content(
            model=self.model,
            contents=req.text,
        )

        text = result.text

        if text is None:
            raise RuntimeError("empty gemini response")

        return Resp(
            provider="gemini",
            model=self.model,
            text=text,
            meta={
                "role": req.role,
                "size": len(req.text),
                **req.meta,
            },
        )
