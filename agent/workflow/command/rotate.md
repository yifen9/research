# Rotate Command

## Purpose

Rotate commands close one session and prepare the next context.

## Rule

- Rotation requires memory.
- Rotation carries open questions and active artifacts.
- Chat `rotate` requests must call the rotate command.
- Autopilot should rotate after approval, topic change, governance change, or session limit.
