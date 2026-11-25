/*
 * Collect a Markdown document split into multiple messages.
 * Usage: send a standalone ### message, then paste/send Markdown text.
 * Paste this script in browser DevTools: it copies the reconstructed text.
 */
(async () => {
  const stacks = [...document.querySelectorAll(".ConvoStack__content")];
  const stack = stacks.at(-1);
  if (!stack) return console.error("No conversation stack in the DOM.");

  const texts = [...stack.querySelectorAll(".ConvoHistory__messageWrapper")]
    .map(node => node.querySelector(".MessageText")?.innerText ?? "");
  const marker = texts.findLastIndex(text => text.trim() === "###");
  if (marker < 0) {
    return console.warn('No standalone "###" marker in the last stack. Nothing copied.');
  }

  const fragments = texts.slice(marker + 1).filter(text => text.length > 0);
  if (!fragments.length) return console.warn("No text messages after the marker.");

  // Preserve Markdown formatting. Join without an injected newline:
  // the original long paste may have been split mid-line.
  const markdown = fragments.join("");
  try {
    await navigator.clipboard.writeText(markdown);
  } catch (error) {
    // DevTools / browser permissions can prevent the Clipboard API.
    const area = document.createElement("textarea");
    area.value = markdown;
    area.style.cssText = "position:fixed;left:-9999px;top:0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    const copied = document.execCommand("copy");
    area.remove();
    if (!copied) {
      console.error("Clipboard write failed; check browser permissions.", error);
      return;
    }
  }
  console.log("Markdown copied to clipboard:", fragments.length, "messages,", markdown.length, "characters");
})();
