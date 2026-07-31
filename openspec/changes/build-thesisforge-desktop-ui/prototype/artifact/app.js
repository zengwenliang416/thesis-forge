(() => {
  "use strict";

  const shell = document.querySelector(".app-shell");
  const stateButtons = [...document.querySelectorAll("[data-state-target]")];
  const stateViews = [...document.querySelectorAll("[data-state-view]")];
  const buildButton = document.getElementById("build-button");
  const buildProgress = document.getElementById("build-progress");
  const buildProgressTitle = document.getElementById("build-progress-title");
  const buildProgressCount = document.getElementById("build-progress-count");
  const buildTrackFill = document.getElementById("build-track-fill");
  const buildSteps = [...document.querySelectorAll("[data-build-step]")];
  const templateSelect = document.getElementById("template-select");
  const saveStatus = document.getElementById("save-status");
  const toast = document.getElementById("toast");
  const editor = document.getElementById("code-editor");
  const editorPosition = document.getElementById("editor-position");
  const paper = document.getElementById("paper");
  const zoomLevel = document.getElementById("zoom-level");
  const mobileTabs = [...document.querySelectorAll("[data-panel-target]")];
  const panels = [...document.querySelectorAll("[data-panel]")];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  let currentState = "populated";
  let isBuilding = false;
  let zoom = window.innerWidth <= 430 ? 78 : 82;

  const buildStageCopy = {
    parse: "正在解析 Markdown",
    validate: "正在执行 Validation",
    compile: "正在编译 ThesisDocument",
    render: "正在生成 RenderPlan",
    finalize: "正在写入 DOCX"
  };

  function setState(nextState) {
    if (isBuilding) return;

    currentState = nextState;
    shell.dataset.state = nextState;

    stateButtons.forEach((button) => {
      const active = button.dataset.stateTarget === nextState;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });

    stateViews.forEach((view) => {
      const visible = view.dataset.stateView === nextState;
      view.hidden = !visible;
      view.classList.toggle("is-visible", visible);
    });

    const canBuild = nextState === "populated";
    buildButton.disabled = !canBuild;
    buildButton.setAttribute("aria-disabled", String(!canBuild));
    templateSelect.disabled = nextState === "loading" || nextState === "permission";

    const statusCopy = {
      populated: "本地草稿已保存",
      loading: "正在读取工作区",
      empty: "尚未载入文稿",
      error: "模板校验失败",
      disabled: "构建器未启用",
      permission: "输出目录仅可读"
    };
    saveStatus.textContent = statusCopy[nextState];
  }

  function setMobilePanel(panelName) {
    mobileTabs.forEach((button) => {
      const active = button.dataset.panelTarget === panelName;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });

    panels.forEach((panel) => {
      panel.classList.toggle("is-mobile-active", panel.dataset.panel === panelName);
    });
  }

  function focusLine(lineNumber) {
    const targetLine = document.querySelector(`.code-line[data-line="${lineNumber}"]`);
    if (!targetLine) return;

    document.querySelectorAll(".code-line.is-selected").forEach((line) => {
      line.classList.remove("is-selected");
    });
    targetLine.classList.add("is-selected");
    editorPosition.textContent = `第 ${lineNumber} 行，第 1 列`;

    if (window.innerWidth <= 820) {
      setMobilePanel("editor");
    }

    const editorTop = targetLine.offsetTop - editor.clientHeight / 2;
    editor.scrollTo({ top: Math.max(0, editorTop), behavior: reducedMotion.matches ? "auto" : "smooth" });
    editor.focus({ preventScroll: true });

    document.querySelectorAll("[data-preview-target].is-targeted").forEach((node) => {
      node.classList.remove("is-targeted");
    });
    const previewTarget = document.querySelector(`[data-preview-target="${lineNumber}"]`);
    if (previewTarget) {
      previewTarget.classList.add("is-targeted");
    }
  }

  async function runBuild() {
    if (isBuilding || currentState !== "populated") return;

    isBuilding = true;
    buildButton.disabled = true;
    buildButton.setAttribute("aria-disabled", "true");
    buildButton.querySelector("span").textContent = "构建中";
    buildProgress.classList.add("is-visible");
    buildProgress.setAttribute("aria-hidden", "false");
    toast.hidden = true;

    const stages = ["parse", "validate", "compile", "render", "finalize"];
    const delay = reducedMotion.matches ? 80 : 520;

    for (let index = 0; index < stages.length; index += 1) {
      const stage = stages[index];
      buildProgressTitle.textContent = buildStageCopy[stage];
      buildProgressCount.textContent = `${index + 1} / ${stages.length}`;
      buildTrackFill.style.width = `${((index + 1) / stages.length) * 100}%`;

      buildSteps.forEach((step, stepIndex) => {
        step.classList.toggle("is-current", stepIndex === index);
        step.classList.toggle("is-complete", stepIndex < index);
      });

      await new Promise((resolve) => window.setTimeout(resolve, delay));
    }

    buildSteps.forEach((step) => {
      step.classList.remove("is-current");
      step.classList.add("is-complete");
    });
    buildProgressTitle.textContent = "构建完成";

    await new Promise((resolve) => window.setTimeout(resolve, reducedMotion.matches ? 80 : 420));

    buildProgress.classList.remove("is-visible");
    buildProgress.setAttribute("aria-hidden", "true");
    buildButton.querySelector("span").textContent = "构建 DOCX";
    buildButton.disabled = false;
    buildButton.setAttribute("aria-disabled", "false");
    saveStatus.textContent = "DOCX 构建成功";
    toast.hidden = false;
    isBuilding = false;
  }

  function updateZoom(nextZoom) {
    zoom = Math.min(104, Math.max(62, nextZoom));
    paper.style.zoom = `${zoom / 100}`;
    zoomLevel.textContent = `${zoom}%`;
  }

  stateButtons.forEach((button) => {
    button.addEventListener("click", () => setState(button.dataset.stateTarget));
  });

  document.querySelectorAll("[data-recovery]").forEach((button) => {
    button.addEventListener("click", () => setState(button.dataset.recovery));
  });

  mobileTabs.forEach((button) => {
    button.addEventListener("click", () => setMobilePanel(button.dataset.panelTarget));
  });

  document.querySelectorAll("[data-line-target]").forEach((button) => {
    button.addEventListener("click", () => focusLine(button.dataset.lineTarget));
  });

  document.querySelectorAll(".outline-item").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".outline-item.is-active").forEach((item) => {
        item.classList.remove("is-active");
        item.removeAttribute("aria-current");
      });
      button.classList.add("is-active");
      button.setAttribute("aria-current", "true");
    });
  });

  document.querySelectorAll(".code-line").forEach((line) => {
    line.addEventListener("click", () => focusLine(line.dataset.line));
  });

  editor.addEventListener("input", () => {
    saveStatus.textContent = "本地草稿有未保存修改";
  });

  buildButton.addEventListener("click", runBuild);

  document.getElementById("zoom-in").addEventListener("click", () => updateZoom(zoom + 6));
  document.getElementById("zoom-out").addEventListener("click", () => updateZoom(zoom - 6));

  document.getElementById("collapse-outline").addEventListener("click", () => {
    if (window.innerWidth <= 820) {
      setMobilePanel("editor");
      return;
    }
    shell.classList.toggle("outline-collapsed");
  });

  const diagnosticsPanel = document.querySelector(".diagnostics-panel");
  const diagnosticsToggle = document.getElementById("collapse-diagnostics");
  diagnosticsToggle.addEventListener("click", () => {
    const collapsed = diagnosticsPanel.classList.toggle("is-collapsed");
    diagnosticsToggle.setAttribute("aria-expanded", String(!collapsed));
  });

  templateSelect.addEventListener("change", () => {
    saveStatus.textContent = "模板已切换，等待构建";
  });

  toast.querySelector("button").addEventListener("click", () => {
    toast.hidden = true;
  });

  document.getElementById("mobile-menu-button").addEventListener("click", () => {
    setMobilePanel("outline");
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "b") {
      event.preventDefault();
      runBuild();
    }

    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      editor.focus();
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth <= 430 && zoom > 78) {
      updateZoom(78);
    }
  });

  updateZoom(zoom);
  setState("populated");
})();
