import path from "node:path";
import { realpath, stat } from "node:fs/promises";

import { diagnostic } from "./diagnostics.mjs";

const REMOTE_SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/;
const WINDOWS_ABSOLUTE = /^(?:[a-zA-Z]:[\\/]|\\\\|\/\/)/;
const WINDOWS_DEVICE = /^(?:\\\\[.?]\\|(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:[./\\:]|$))/i;

export function toPosix(value) {
  return value.split(path.sep).join("/");
}

export function isInside(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

export function lexicalPathDiagnostic(raw, target, line) {
  if (raw.includes("\0")) {
    return diagnostic(
      "DFP-RESOURCE-NUL",
      "error",
      target,
      "Resource path contains a NUL character.",
      "Remove the invalid character.",
      line,
    );
  }
  if (WINDOWS_DEVICE.test(raw)) {
    return diagnostic(
      "DFP-RESOURCE-DEVICE",
      "error",
      target,
      "Device paths are not valid project resources.",
      "Use a regular local file.",
      line,
    );
  }
  if (path.isAbsolute(raw) || WINDOWS_ABSOLUTE.test(raw)) {
    return diagnostic(
      "DFP-RESOURCE-ABSOLUTE",
      "error",
      target,
      "Absolute resource paths are outside the portable input contract.",
      "Use a relative path inside the source boundary.",
      line,
    );
  }
  if (REMOTE_SCHEME.test(raw)) {
    return diagnostic(
      "DFP-RESOURCE-REMOTE",
      "error",
      target,
      "Remote resources are not downloaded.",
      "Replace the reference with a local file inside the source boundary.",
      line,
    );
  }
  const normalized = raw.replaceAll("\\", "/");
  if (normalized.split("/").includes("..")) {
    return diagnostic(
      "DFP-RESOURCE-TRAVERSAL",
      "error",
      target,
      "Resource paths may not contain parent traversal.",
      "Move the file under the source boundary and reference it directly.",
      line,
    );
  }
  return null;
}

export async function resolveConfinedFile(root, raw, target, line) {
  const lexicalIssue = lexicalPathDiagnostic(raw, target, line);
  if (lexicalIssue) {
    return { diagnostic: lexicalIssue };
  }

  const candidate = path.resolve(root, raw);
  let resolved;
  try {
    resolved = await realpath(candidate);
  } catch {
    return {
      diagnostic: diagnostic(
        "DFP-RESOURCE-MISSING",
        "error",
        target,
        "Referenced local resource does not exist.",
        "Restore the file or correct the Markdown reference.",
        line,
      ),
    };
  }

  if (!isInside(root, resolved)) {
    return {
      diagnostic: diagnostic(
        "DFP-RESOURCE-SYMLINK-ESCAPE",
        "error",
        target,
        "Resolved resource leaves the selected source boundary.",
        "Move the resource inside the source boundary and remove the escaping symlink.",
        line,
      ),
    };
  }

  const info = await stat(resolved);
  if (!info.isFile()) {
    return {
      diagnostic: diagnostic(
        "DFP-RESOURCE-NOT-FILE",
        "error",
        target,
        "Referenced resource is not a regular file.",
        "Reference a regular local file.",
        line,
      ),
    };
  }
  return { path: resolved };
}
