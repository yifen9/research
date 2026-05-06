import assert from "node:assert/strict"
import { EventEmitter } from "node:events"
import test from "node:test"

import {
  callBridge,
  checkSize,
  eventSessionID,
  latestRound,
  requireCommand,
  server,
  textOf,
} from "../agent/backend/omo/template/session-round.mjs"


const user = {
  info: { id: "u1", role: "user", sessionID: "s1" },
  parts: [{ type: "text", text: "hello" }],
}

const assistant = {
  info: { id: "a1", role: "assistant", sessionID: "s1", parentID: "u1" },
  parts: [{ type: "text", text: "answer" }],
}


test("text filters ignored parts", () => {
  assert.equal(
    textOf([
      { type: "text", text: "keep" },
      { type: "text", text: "skip", synthetic: true },
      { type: "file", text: "file" },
    ]),
    "keep",
  )
})


test("latest round finds parent user", () => {
  assert.deepEqual(latestRound([user, assistant]), {
    userText: "hello",
    aiText: "answer",
    assistantID: "a1",
  })
})


test("session id comes from idle event", () => {
  assert.equal(eventSessionID({ properties: { sessionID: "s1" } }), "s1")
})


test("command option is required", () => {
  assert.throws(() => requireCommand({ command: [] }), /missing option command/)
})


test("bridge uses argv and stdin", async () => {
  let call
  const run = (cmd, args, options) => {
    call = { cmd, args, options }
    const child = new EventEmitter()
    child.stderr = new EventEmitter()
    child.stdin = { end: (data) => { call.data = data } }
    queueMicrotask(() => child.emit("close", 0))
    return child
  }

  await callBridge({
    command: ["uv", "run", "python", "script/agent/session/auto_round.py"],
    root: "/repo",
    role: "architect",
    source: "opencode:s1:a1",
    userText: "hello",
    aiText: "answer",
    maxBytes: 1000,
  }, run)

  assert.equal(call.cmd, "uv")
  assert.equal(call.options.shell, false)
  assert.deepEqual(call.args.slice(-4), ["/repo", "architect", "opencode:s1:a1", "1000"])
  assert.equal(JSON.parse(call.data).ai_text, "answer")
})


test("bridge rejects oversized text", () => {
  assert.throws(() => checkSize("abcdef", 3), /message too large/)
})


test("plugin records idle event once", async () => {
  const calls = []
  const hook = await server({
    directory: "/repo",
    client: {
      session: {
        messages: async () => ({ data: [user, assistant] }),
      },
    },
  }, {
    role: "architect",
    source_prefix: "opencode",
    command: ["node", "ok"],
    limit: 5,
    max_bytes: 1000,
    bridge: async (input) => { calls.push(input) },
  })

  const save = console.warn
  console.warn = () => {}
  try {
    await hook.event({ event: { type: "session.idle", properties: { sessionID: "s1" } } })
    await hook.event({ event: { type: "session.idle", properties: { sessionID: "s1" } } })
  } finally {
    console.warn = save
  }

  assert.equal(calls.length, 1)
  assert.equal(calls[0].source, "opencode:s1:a1")
})
