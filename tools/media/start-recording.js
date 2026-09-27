async (page) => {
  if (!page.__mediaBrowser || !page.__mediaBaseUrl) throw new Error("Initialize the local headless browser and recording server first.");
  if (page.__activeRecording) throw new Error("Stop the current recording before starting another.");
  const response = await page.request.get(page.__mediaBaseUrl + "/capture-config.json");
  if (!response.ok()) throw new Error("Cannot read the local capture configuration.");
  const config = await response.json();
  const options = {viewport: {width: 1280, height: 720}, recordVideo: {dir: config.directory, size: {width: 1280, height: 720}}};
  if (config.kind === "portal") options.storageState = await page.__mediaContext.storageState();
  const context = await page.__mediaBrowser.newContext(options);
  await context.addInitScript(({redact}) => {
    const clean = text => {
      for (const value of redact) {
        if (value) text = text.replace(new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), "[redacted]");
      }
      return text
        .replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, "[account redacted]")
        .replace(/\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b/g, "[ID redacted]");
    };
    const scrub = () => {
      const root = document.body;
      if (!root) return;
      if (location.hostname === "login.microsoftonline.com") {
        root.style.visibility = "hidden";
        return;
      }
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const changes = [];
      while (walker.nextNode()) {
        const node = walker.currentNode;
        if (["SCRIPT", "STYLE"].includes(node.parentElement?.tagName)) continue;
        const next = clean(node.nodeValue);
        if (next !== node.nodeValue) changes.push([node, next]);
      }
      for (const [node, text] of changes) node.nodeValue = text;
      for (const input of root.querySelectorAll("input[type=password]")) input.style.visibility = "hidden";
    };
    new MutationObserver(scrub).observe(document, {subtree: true, childList: true, characterData: true});
    document.addEventListener("DOMContentLoaded", scrub);
  }, {redact: config.redact});
  const started = Date.now();
  const screen = await context.newPage();
  await screen.goto(config.url);
  await screen.waitForTimeout(config.kind === "portal" ? 6500 : 1000);
  if (screen.url().includes("login.microsoftonline.com")) {
    await context.close();
    throw new Error("Recording context needs authentication. Login contents were hidden; do not publish this take.");
  }
  const ready = Date.now() - started;
  page.__activeRecording = {id: config.id, context, page: screen, started_at_ms: started, ready_offset_ms: ready};
  return {recording: config.id, headless: true, ready_offset_ms: ready, visibleText: (await screen.locator("body").innerText()).slice(0, 700)};
}
