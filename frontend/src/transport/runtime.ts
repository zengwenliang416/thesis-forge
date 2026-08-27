import { invoke } from "@tauri-apps/api/core";
import type { WorkbenchTransport } from "./WorkbenchTransport";
import { TauriWorkbenchTransport } from "./tauri";
import { WebWorkbenchTransport } from "./web";

export function createRuntimeTransport(): WorkbenchTransport {
  if ("__TAURI_INTERNALS__" in window) {
    return new TauriWorkbenchTransport(invoke);
  }
  return new WebWorkbenchTransport({
    baseUrl: import.meta.env.VITE_DOCFORGE_API_URL ?? "",
  });
}
