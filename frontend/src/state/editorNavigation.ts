export function lineSelectionRange(text: string, line: number) {
  if (!Number.isInteger(line) || line < 1) {
    return null;
  }
  const lines = text.split("\n");
  if (line > lines.length) {
    return null;
  }
  let start = 0;
  for (let index = 0; index < line - 1; index += 1) {
    start += lines[index].length + 1;
  }
  return { start, end: start + lines[line - 1].length };
}
