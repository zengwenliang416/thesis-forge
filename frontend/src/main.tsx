import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { WorkbenchApp } from "./components/WorkbenchApp";
import { createInitialWorkspaceState } from "./state/workspace";
import { createRuntimeTransport } from "./transport/runtime";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WorkbenchApp
      transport={createRuntimeTransport()}
      initialState={createInitialWorkspaceState()}
    />
  </StrictMode>,
);
