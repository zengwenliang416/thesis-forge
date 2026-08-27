import { PROTOCOL_VERSION } from "./dto";
import {
  DEFAULT_SOURCE_FILENAME,
  MANIFEST_FILENAME,
  PROJECT_SCHEMA_VERSION,
} from "./constants";
import {
  deriveDocxFileName,
  isMarkdownFileName,
  readOpenProjectInput,
  readOpenedProject,
  readProjectFileSnapshot,
  readProjectIdentity,
  type OpenProjectInput,
  type ProjectIdentityRef,
} from "./WorkbenchTransport";
import { TauriWorkbenchTransport } from "./tauri";
import { WebWorkbenchTransport } from "./web";

const project: ProjectIdentityRef = {
  id: "project-1",
  root: "/workspace/thesis",
  manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
};

const sourceText = "# 绪论\n\n公式 $a^2 + b^2 = c^2$，引用“文献”。\n";
const manifestText = `schema: ${PROJECT_SCHEMA_VERSION}\nproject:\n  id: project-1\n`;

const input: OpenProjectInput = {
  manifest: {
    fileName: MANIFEST_FILENAME,
    text: manifestText,
  },
  source: {
    fileName: DEFAULT_SOURCE_FILENAME,
    text: sourceText,
  },
};

const workspaceSource = {
  kind: "web-workspace" as const,
  workspaceId: "a".repeat(32),
  fileName: DEFAULT_SOURCE_FILENAME,
};

const openedProjectBody = {
  protocol: PROTOCOL_VERSION,
  ok: true,
  project,
  source: workspaceSource,
  text: sourceText,
};

function jsonResponse(body: unknown, status = 201): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("WebWorkbenchTransport.openProject", () => {
  it("posts exactly one typed request carrying only the manifest and source snapshots", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({ url: String(url), init });
        return jsonResponse(openedProjectBody);
      },
    });

    await transport.openProject(input);

    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe("http://127.0.0.1:8765/api/v1/workspaces");
    expect(calls[0].init?.method).toBe("POST");
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      manifest: {
        fileName: MANIFEST_FILENAME,
        text: manifestText,
      },
      source: {
        fileName: DEFAULT_SOURCE_FILENAME,
        text: sourceText,
      },
    });
  });

  it("returns the opened project preserving identity, source, and text snapshot", async () => {
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async () => jsonResponse(openedProjectBody),
    });

    const opened = await transport.openProject(input);

    expect(opened).toEqual({
      project: {
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
      },
      source: {
        kind: "web-workspace",
        workspaceId: "a".repeat(32),
        fileName: DEFAULT_SOURCE_FILENAME,
      },
      text: sourceText,
    });
  });

  it("round-trips the source snapshot text unchanged", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    const opened = await transport.openProject(input);

    expect(opened.text).toBe(sourceText);
  });

  it("rejects when the project input is missing", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(transport.openProject()).rejects.toThrow(
      "Web project input is required",
    );
  });

  it("rejects an input without a manifest snapshot", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({ source: input.source } as OpenProjectInput),
    ).rejects.toThrow("无效的 DocForge manifest 快照");
  });

  it("rejects the obsolete ThesisForge manifest filename", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({
        ...input,
        manifest: { ...input.manifest, fileName: "thesisforge.yaml" },
      }),
    ).rejects.toThrow(`DocForge project manifest 必须是 ${MANIFEST_FILENAME}`);
  });

  it("rejects an input without a source snapshot", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({ manifest: input.manifest } as OpenProjectInput),
    ).rejects.toThrow("无效的 DocForge source 快照");
  });

  it("rejects an input carrying a client project identity", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });
    const invalid = {
      ...input,
      project,
    };

    await expect(
      transport.openProject(invalid),
    ).rejects.toThrow("无效的 DocForge project 输入");
  });

  it("rejects an input carrying duplicate metadata", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({
        ...input,
        fileName: DEFAULT_SOURCE_FILENAME,
      } as unknown as OpenProjectInput),
    ).rejects.toThrow("无效的 DocForge project 输入");
  });

  it("rejects when the input source snapshot fileName is empty", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({
        ...input,
        source: { ...input.source, fileName: "" },
      }),
    ).rejects.toThrow("无效的 DocForge source 快照");
  });

  it("rejects a response with a wrong protocol version", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          ...openedProjectBody,
          protocol: "thesisforge.workbench.v0",
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response with ok: false", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse({ ...openedProjectBody, ok: false }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response without the echoed project identity", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          protocol: PROTOCOL_VERSION,
          ok: true,
          source: workspaceSource,
          text: sourceText,
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response whose project identity is missing root", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          ...openedProjectBody,
          project: {
            id: "project-1",
            manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
          },
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response without a source", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          protocol: PROTOCOL_VERSION,
          ok: true,
          project,
          text: sourceText,
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response with an unknown source kind", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          ...openedProjectBody,
          source: {
            kind: "web-mirror",
            mirrorId: "mirror-1",
            fileName: DEFAULT_SOURCE_FILENAME,
          },
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response containing an uploaded-file-only project source", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          ...openedProjectBody,
          source: {
            kind: "web-upload",
            uploadId: "u".repeat(32),
            fileName: DEFAULT_SOURCE_FILENAME,
          },
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response with duplicate manifest metadata", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          ...openedProjectBody,
          manifest: input.manifest,
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects a response without text", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          protocol: PROTOCOL_VERSION,
          ok: true,
          project,
          source: workspaceSource,
        }),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });

  it("rejects an HTTP error status", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody, 500),
    });

    await expect(transport.openProject(input)).rejects.toThrow(
      "打开 Web 项目工作区失败",
    );
  });
});

describe("TauriWorkbenchTransport.openProject", () => {
  const desktopSource = {
    kind: "desktop" as const,
    path: `/workspace/thesis/${DEFAULT_SOURCE_FILENAME}`,
    fileName: DEFAULT_SOURCE_FILENAME,
  };

  const pickerBody = {
    project,
    source: desktopSource,
    text: sourceText,
  };

  it("invokes exactly the pick_project command and returns the typed project", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      return pickerBody;
    });

    const opened = await transport.openProject();

    expect(calls).toEqual([{ command: "pick_project", args: undefined }]);
    expect(opened).toEqual({
      project: {
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
      },
      source: {
        kind: "desktop",
        path: `/workspace/thesis/${DEFAULT_SOURCE_FILENAME}`,
        fileName: DEFAULT_SOURCE_FILENAME,
      },
      text: sourceText,
    });
  });

  it("returns null when the picker resolves null", async () => {
    const transport = new TauriWorkbenchTransport(async () => null);

    await expect(transport.openProject()).resolves.toBeNull();
  });

  it("rejects a non-object picker response", async () => {
    const transport = new TauriWorkbenchTransport(async () => "project-1");

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response without the project identity", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      source: desktopSource,
      text: sourceText,
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with an empty project id", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      project: { ...project, id: "" },
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with an empty project root", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      project: { ...project, root: "" },
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with an empty project manifestPath", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      project: { ...project, manifestPath: "" },
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with an extra project key", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      project: { ...project, school: "example-university" },
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response without a source", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      project,
      text: sourceText,
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with an unknown source kind", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      source: {
        kind: "web-mirror",
        mirrorId: "mirror-1",
        fileName: DEFAULT_SOURCE_FILENAME,
      },
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response without text", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      project,
      source: desktopSource,
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("rejects a picker response with a non-string text", async () => {
    const transport = new TauriWorkbenchTransport(async () => ({
      ...pickerBody,
      text: null,
    }));

    await expect(transport.openProject()).rejects.toThrow(
      "无效的 Tauri project picker 响应",
    );
  });

  it("shares one project contract with the Web transport", async () => {
    const sharedBody = {
      project,
      source: {
        kind: "web-workspace" as const,
        workspaceId: "a".repeat(32),
        fileName: DEFAULT_SOURCE_FILENAME,
      },
      text: sourceText,
    };
    const tauri = new TauriWorkbenchTransport(async () => sharedBody);
    const web = new WebWorkbenchTransport({
      fetch: async () =>
        jsonResponse({
          protocol: PROTOCOL_VERSION,
          ok: true,
          ...sharedBody,
        }),
    });

    const fromTauri = await tauri.openProject();
    const fromWeb = await web.openProject(input);

    expect(fromTauri).toEqual(sharedBody);
    expect(fromWeb).toEqual(fromTauri);
  });
});

describe("project transport readers", () => {
  it("readProjectIdentity accepts a well-formed identity", () => {
    expect(
      readProjectIdentity({
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
      }),
    ).toEqual(project);
  });

  it("readProjectIdentity rejects null", () => {
    expect(() => readProjectIdentity(null)).toThrow(
      "无效的 DocForge project 标识",
    );
  });

  it("readProjectIdentity rejects non-object values", () => {
    expect(() => readProjectIdentity("project-1")).toThrow(
      "无效的 DocForge project 标识",
    );
  });

  it("readProjectIdentity rejects arrays", () => {
    expect(() =>
      readProjectIdentity(["project-1", "/workspace/thesis"]),
    ).toThrow("无效的 DocForge project 标识");
  });

  it("readProjectIdentity rejects wrong field types", () => {
    expect(() =>
      readProjectIdentity({
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: 7,
      }),
    ).toThrow("无效的 DocForge project 标识");
  });

  it("readProjectIdentity rejects empty strings", () => {
    expect(() =>
      readProjectIdentity({
        id: "project-1",
        root: "",
        manifestPath: `/workspace/thesis/${MANIFEST_FILENAME}`,
      }),
    ).toThrow("无效的 DocForge project 标识");
  });

  it("readProjectIdentity rejects extra keys", () => {
    expect(() =>
      readProjectIdentity({ ...project, extra: true }),
    ).toThrow("无效的 DocForge project 标识");
  });

  it("readProjectFileSnapshot accepts the manifest and source shapes", () => {
    expect(
      readProjectFileSnapshot(
        { fileName: MANIFEST_FILENAME, text: manifestText },
        "manifest",
      ),
    ).toEqual({ fileName: MANIFEST_FILENAME, text: manifestText });
    expect(
      readProjectFileSnapshot(
        { fileName: "chapters/intro.MARKDOWN", text: sourceText },
        "source",
      ),
    ).toEqual({ fileName: "chapters/intro.MARKDOWN", text: sourceText });
  });

  it("recognizes Markdown extensions case-insensitively and derives DOCX names", () => {
    expect(isMarkdownFileName("document.md")).toBe(true);
    expect(isMarkdownFileName("document.MARKDOWN")).toBe(true);
    expect(isMarkdownFileName("document.txt")).toBe(false);
    expect(deriveDocxFileName("/workspace/document.MARKDOWN")).toBe(
      "/workspace/document.docx",
    );
  });

  it("readProjectFileSnapshot rejects non-canonical manifest and source names", () => {
    expect(() =>
      readProjectFileSnapshot(
        { fileName: "project.yaml", text: manifestText },
        "manifest",
      ),
    ).toThrow(`必须是 ${MANIFEST_FILENAME}`);
    expect(() =>
      readProjectFileSnapshot(
        { fileName: MANIFEST_FILENAME, text: sourceText },
        "source",
      ),
    ).toThrow("必须是 Markdown 文件");
  });

  it("readOpenProjectInput accepts only manifest and source snapshots", () => {
    expect(readOpenProjectInput(input)).toEqual(input);
    expect(() =>
      readOpenProjectInput({
        ...input,
        project,
        fileName: DEFAULT_SOURCE_FILENAME,
      }),
    ).toThrow("无效的 DocForge project 输入");
  });

  it("readOpenedProject accepts the shared typed contract", () => {
    const desktopSource = {
      kind: "desktop",
      path: `/workspace/thesis/${DEFAULT_SOURCE_FILENAME}`,
      fileName: DEFAULT_SOURCE_FILENAME,
    };

    expect(
      readOpenedProject({ project, source: desktopSource, text: sourceText }),
    ).toEqual({ project, source: desktopSource, text: sourceText });
  });

  it("readOpenedProject rejects null", () => {
    expect(() => readOpenedProject(null)).toThrow(
      "无效的 DocForge project 响应",
    );
  });

  it("readOpenedProject rejects non-object values", () => {
    expect(() => readOpenedProject(42)).toThrow(
      "无效的 DocForge project 响应",
    );
  });

  it("readOpenedProject rejects a missing source", () => {
    expect(() =>
      readOpenedProject({ project, text: sourceText }),
    ).toThrow("无效的 DocForge project 响应");
  });

  it("readOpenedProject rejects an unknown source kind", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: {
          kind: "web-mirror",
          mirrorId: "mirror-1",
          fileName: DEFAULT_SOURCE_FILENAME,
        },
        text: sourceText,
      }),
    ).toThrow("无效的 DocForge project 响应");
  });

  it("readOpenedProject rejects an uploaded-file-only source", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: {
          kind: "web-upload",
          uploadId: "u".repeat(32),
          fileName: DEFAULT_SOURCE_FILENAME,
        },
        text: sourceText,
      }),
    ).toThrow("无效的 DocForge project 响应");
  });

  it("readOpenedProject rejects a source with an extra key", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: { ...workspaceSource, uploadId: "upload-1" },
        text: sourceText,
      }),
    ).toThrow("无效的 DocForge project 响应");
  });

  it("readOpenedProject rejects a non-string text", () => {
    expect(() =>
      readOpenedProject({ project, source: workspaceSource, text: null }),
    ).toThrow("无效的 DocForge project 响应");
  });

  it("readOpenedProject rejects extra top-level keys", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: workspaceSource,
        text: sourceText,
        extra: true,
      }),
    ).toThrow("无效的 DocForge project 响应");
  });
});
