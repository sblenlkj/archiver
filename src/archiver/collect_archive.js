/* Collect Base64 ZIP from the last loaded conversation stack after a standalone ### marker. */
(() => {
  const stacks = [...document.querySelectorAll(".ConvoStack__content")];
  const stack = stacks.at(-1);
  if (!stack) return console.error("No conversation stack in the DOM.");

  const texts = [...stack.querySelectorAll(".ConvoHistory__messageWrapper")]
    .map(node => node.querySelector(".MessageText")?.innerText ?? "");
  const marker = texts.findLastIndex(text => text.trim() === "###");
  if (marker < 0) {
    return console.warn('No standalone "###" marker in the last stack. Nothing exported.');
  }
  const fragments = texts.slice(marker + 1).filter(text => text.length > 0);
  if (!fragments.length) return console.warn("No messages after the last ### marker.");

  const encoded = fragments.join("").replace(/\s/g, "");
  if (!/^UEsDB[A-Za-z0-9+/=]*$/.test(encoded)) {
    return console.warn("Collected text does not look like ZIP Base64. Nothing exported.");
  }

  const blob = new Blob([encoded], { type: "text/plain;charset=us-ascii" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "collected_base64.txt";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  console.log("Downloaded Base64:", fragments.length, "messages,", encoded.length, "characters");
})();
