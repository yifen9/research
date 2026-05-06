import { spawn } from "node:child_process"


export function requireOption(options, key) {
  const value = options?.[key]
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`missing option ${key}`)
  }
  return value.trim()
}


export function requireCommand(options) {
  const value = options?.command
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error("missing option command")
  }
  return value.map((item) => {
    if (typeof item !== "string" || item.trim() === "") {
      throw new Error("bad option command")
    }
    return item
  })
}


export function textOf(parts) {
  return parts
    .filter((part) => part.type === "text" && !part.synthetic && !part.ignored)
    .map((part) => part.text)
    .filter((text) => typeof text === "string" && text.trim() !== "")
    .join("\n")
}


export function byteSize(text) {
  return Buffer.byteLength(text, "utf8")
}


export function checkSize(text, maxBytes) {
  if (byteSize(text) > maxBytes) {
    throw new Error("message too large")
  }
}


export function latestRound(data) {
  const rows = [...data].reverse()
  const assistant = rows.find((row) => row.info?.role === "assistant" && row.info?.parentID)
  if (!assistant) {
    return null
  }
  const user = data.find((row) => row.info?.id === assistant.info.parentID)
  if (!user || user.info?.role !== "user") {
    return null
  }
  const userText = textOf(user.parts || [])
  const aiText = textOf(assistant.parts || [])
  if (userText === "" || aiText === "") {
    return null
  }
  return {
    userText,
    aiText,
    assistantID: assistant.info.id,
  }
}


export function eventSessionID(event) {
  return event?.properties?.sessionID || event?.properties?.info?.sessionID || null
}


export async function fetchMessages(client, sessionID, limit, directory) {
  const result = await client.session.messages({
    path: { id: sessionID },
    query: { directory, limit },
  })
  return result?.data || result?.response || result
}


export function boundedMessage(reason) {
  return [
    `session round capture skipped: ${reason}`,
    "choices: start architect session | disable auto capture | retry after repair",
  ].join("\n")
}


export function callBridge(input, run = spawn) {
  checkSize(input.userText, input.maxBytes)
  checkSize(input.aiText, input.maxBytes)
  const args = [...input.command.slice(1), input.root, input.role, input.source, String(input.maxBytes)]
  const payload = JSON.stringify({ user_text: input.userText, ai_text: input.aiText })
  checkSize(payload, input.maxBytes)
  return new Promise((resolve, reject) => {
    const child = run(input.command[0], args, {
      cwd: input.root,
      shell: false,
      stdio: ["pipe", "ignore", "pipe"],
    })
    let error = ""
    child.stderr.on("data", (data) => {
      error += data.toString()
    })
    child.on("error", reject)
    child.on("close", (code) => {
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(error.trim() || `auto round failed ${code}`))
      }
    })
    child.stdin.end(payload)
  })
}


export async function server(input, options = {}) {
  const role = requireOption(options, "role")
  const source = requireOption(options, "source_prefix")
  const command = requireCommand(options)
  const limit = Number(options.limit || 20)
  const maxBytes = Number(options.max_bytes)
  if (!Number.isSafeInteger(maxBytes) || maxBytes <= 0) {
    throw new Error("bad option max_bytes")
  }
  const bridge = options.bridge || callBridge
  const seen = new Set()

  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") {
        return
      }
      const sessionID = eventSessionID(event)
      if (!sessionID) {
        console.warn(boundedMessage("missing session id"))
        return
      }
      const data = await fetchMessages(input.client, sessionID, limit, input.directory)
      const round = latestRound(Array.isArray(data) ? data : [])
      if (!round) {
        console.warn(boundedMessage("missing complete user ai pair"))
        return
      }
      const key = `${source}:${sessionID}:${round.assistantID}`
      if (seen.has(key)) {
        return
      }
      seen.add(key)
      await bridge({
        command,
        root: input.directory,
        role,
        source: key,
        userText: round.userText,
        aiText: round.aiText,
        maxBytes,
      })
    },
  }
}


export default { server }
