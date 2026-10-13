// Parse event frames across arbitrary HTTP chunk boundaries.
export async function readRagStream(response, onEvent) {
  if (!response.ok) {
    const body = await response.json();
    throw new Error(body.detail || "请求失败 / Request failed");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let receivedResult = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r/g, "");
      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split("\n");
        const event = lines.find(line => line.startsWith("event:"))?.slice(6).trim();
        const raw = lines.filter(line => line.startsWith("data:")).map(line => line.slice(5).trim()).join("\n");
        if (!raw) continue;
        const data = JSON.parse(raw);
        if (event === "error") throw new Error(data.message);
        if (event === "result") receivedResult = true;
        onEvent(event, data);
      }
      if (done) break;
    }
    if (!receivedResult) throw new Error("连接中断，未收到完整回答 / Incomplete response");
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
}
