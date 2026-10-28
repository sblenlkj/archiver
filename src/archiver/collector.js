/*
 * Paste into browser DevTools on a deliberately prepared test conversation.
 * Exports text from the LAST conversation stack in DOM order as one TXT.
 * Does not call VK API or send data elsewhere.
 */
(() => {
  const stacks = [...document.querySelectorAll(".ConvoStack__content")];
  const stack = stacks.at(-1);
  if (!stack) {
    console.error("No .ConvoStack__content found in the current DOM.");
    return;
  }

  const messages = [...stack.querySelectorAll(".ConvoHistory__messageWrapper")]
    .map(node => node.querySelector(".MessageText")?.innerText ?? "")
    .filter(text => text.length > 0);

  if (!messages.length) {
    console.error("Last stack contains no .MessageText elements.");
    return;
  }

  // VK may insert visual line wrapping in innerText. Base64 itself has
  // no whitespace in our encoder's output; discard whitespace on collection.
  const joined = messages.join("").replace(/\s/g, "");

  console.table({
    stacks: stacks.length,
    textMessagesInLastStack: messages.length,
    collectedCharacters: joined.length,
    start: joined.slice(0, 32),
    end: joined.slice(-32),
  });

  // A ZIP encoded as Base64 begins with UEsDB. This is a sanity check,
  // not a completeness check; the Python decoder validates the ZIP.
  if (!joined.startsWith("UEsDB")) {
    console.warn("Last stack does not start with expected ZIP/Base64 prefix (UEsDB). No download.");
    return;
  }

  const blob = new Blob([joined], { type: "text/plain;charset=us-ascii" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "collected_base64.txt";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  console.log("Downloaded collected_base64.txt");
})();
