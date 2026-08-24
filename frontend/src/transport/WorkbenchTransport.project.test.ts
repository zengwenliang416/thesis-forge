import { PROTOCOL_VERSION } from "./dto";
import {
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
  manifestPath: "/workspace/thesis/thesisforge.yaml",
};

const sourceText = "# 绪论\n\n公式 $a^2 + b^2 = c^2$，引用“文献”。\n";
const manifestText =
  "schema: thesisforge.project.v2\nproject:\n  id: project-1\n";

const input: OpenProjectInput = {
  project,
  manifest: {
    fileName: "thesisforge.yaml",
    text: manifestText,
  },
  source: {
    fileName: "thesis.md",
    text: sourceText,
  },
};

const workspaceSource = {
  kind: "web-workspace" as const,
  workspaceId: "a".repeat(32),
  fileName: "thesis.md",
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
  it("posts exactly one typed request carrying the full project identity and snapshot", async () => {
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
      project: {
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: "/workspace/thesis/thesisforge.yaml",
      },
      manifest: {
        fileName: "thesisforge.yaml",
        text: manifestText,
      },
      source: {
        fileName: "thesis.md",
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
        manifestPath: "/workspace/thesis/thesisforge.yaml",
      },
      source: {
        kind: "web-workspace",
        workspaceId: "a".repeat(32),
        fileName: "thesis.md",
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

  it("rejects a project identity with an empty id", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({ ...input, project: { ...project, id: "" } }),
    ).rejects.toThrow("无效的 ThesisForge project 标识");
  });

  it("rejects a project identity with an empty root", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({ ...input, project: { ...project, root: "" } }),
    ).rejects.toThrow("无效的 ThesisForge project 标识");
  });

  it("rejects a project identity with an empty manifestPath", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    await expect(
      transport.openProject({
        ...input,
        project: { ...project, manifestPath: "" },
      }),
    ).rejects.toThrow("无效的 ThesisForge project 标识");
  });

  it("rejects a project identity with a non-string field", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });
    const invalid = {
      ...input,
      project: { ...project, root: 42 },
    } as unknown as OpenProjectInput;

    await expect(transport.openProject(invalid)).rejects.toThrow(
      "无效的 ThesisForge project 标识",
    );
  });

  it("rejects a project identity with an extra key", async () => {
    const transport = new WebWorkbenchTransport({
      fetch: async () => jsonResponse(openedProjectBody),
    });

    const invalid = {
      ...input,
      project: { ...project, school: "example-university" },
    };

    await expect(
      transport.openProject(invalid),
    ).rejects.toThrow("无效的 ThesisForge project 标识");
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
    ).rejects.toThrow("无效的 ThesisForge source 快照");
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
            manifestPath: "/workspace/thesis/thesisforge.yaml",
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
            fileName: "thesis.md",
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
            fileName: "thesis.md",
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
    path: "/workspace/thesis/thesis.md",
    fileName: "thesis.md",
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
        manifestPath: "/workspace/thesis/thesisforge.yaml",
      },
      source: {
        kind: "desktop",
        path: "/workspace/thesis/thesis.md",
        fileName: "thesis.md",
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
      source: { kind: "web-mirror", mirrorId: "mirror-1", fileName: "thesis.md" },
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
        fileName: "thesis.md",
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
        manifestPath: "/workspace/thesis/thesisforge.yaml",
      }),
    ).toEqual(project);
  });

  it("readProjectIdentity rejects null", () => {
    expect(() => readProjectIdentity(null)).toThrow(
      "无效的 ThesisForge project 标识",
    );
  });

  it("readProjectIdentity rejects non-object values", () => {
    expect(() => readProjectIdentity("project-1")).toThrow(
      "无效的 ThesisForge project 标识",
    );
  });

  it("readProjectIdentity rejects arrays", () => {
    expect(() =>
      readProjectIdentity(["project-1", "/workspace/thesis"]),
    ).toThrow("无效的 ThesisForge project 标识");
  });

  it("readProjectIdentity rejects wrong field types", () => {
    expect(() =>
      readProjectIdentity({
        id: "project-1",
        root: "/workspace/thesis",
        manifestPath: 7,
      }),
    ).toThrow("无效的 ThesisForge project 标识");
  });

  it("readProjectIdentity rejects empty strings", () => {
    expect(() =>
      readProjectIdentity({
        id: "project-1",
        root: "",
        manifestPath: "/workspace/thesis/thesisforge.yaml",
      }),
    ).toThrow("无效的 ThesisForge project 标识");
  });

  it("readProjectIdentity rejects extra keys", () => {
    expect(() =>
      readProjectIdentity({ ...project, extra: true }),
    ).toThrow("无效的 ThesisForge project 标识");
  });

  it("readProjectFileSnapshot accepts the manifest and source shapes", () => {
    expect(
      readProjectFileSnapshot(
        { fileName: "thesisforge.yaml", text: manifestText },
        "manifest",
      ),
    ).toEqual({ fileName: "thesisforge.yaml", text: manifestText });
    expect(
      readProjectFileSnapshot(
        { fileName: "chapters/intro.md", text: sourceText },
        "source",
      ),
    ).toEqual({ fileName: "chapters/intro.md", text: sourceText });
  });

  it("readProjectFileSnapshot rejects non-canonical manifest and source names", () => {
    expect(() =>
      readProjectFileSnapshot(
        { fileName: "project.yaml", text: manifestText },
        "manifest",
      ),
    ).toThrow("必须是 thesisforge.yaml");
    expect(() =>
      readProjectFileSnapshot(
        { fileName: "thesisforge.yaml", text: sourceText },
        "source",
      ),
    ).toThrow("必须是 Markdown 文件");
  });

  it("readOpenProjectInput rejects projectless and duplicate-metadata input", () => {
    expect(() =>
      readOpenProjectInput({
        manifest: input.manifest,
        source: input.source,
      }),
    ).toThrow("无效的 ThesisForge project 标识");
    expect(() =>
      readOpenProjectInput({
        ...input,
        fileName: "thesis.md",
      }),
    ).toThrow("无效的 ThesisForge project 输入");
  });

  it("readOpenedProject accepts the shared typed contract", () => {
    const desktopSource = {
      kind: "desktop",
      path: "/workspace/thesis/thesis.md",
      fileName: "thesis.md",
    };

    expect(
      readOpenedProject({ project, source: desktopSource, text: sourceText }),
    ).toEqual({ project, source: desktopSource, text: sourceText });
  });

  it("readOpenedProject rejects null", () => {
    expect(() => readOpenedProject(null)).toThrow(
      "无效的 ThesisForge project 响应",
    );
  });

  it("readOpenedProject rejects non-object values", () => {
    expect(() => readOpenedProject(42)).toThrow(
      "无效的 ThesisForge project 响应",
    );
  });

  it("readOpenedProject rejects a missing source", () => {
    expect(() =>
      readOpenedProject({ project, text: sourceText }),
    ).toThrow("无效的 ThesisForge project 响应");
  });

  it("readOpenedProject rejects an unknown source kind", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: { kind: "web-mirror", mirrorId: "mirror-1", fileName: "thesis.md" },
        text: sourceText,
      }),
    ).toThrow("无效的 ThesisForge project 响应");
  });

  it("readOpenedProject rejects an uploaded-file-only source", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: {
          kind: "web-upload",
          uploadId: "u".repeat(32),
          fileName: "thesis.md",
        },
        text: sourceText,
      }),
    ).toThrow("无效的 ThesisForge project 响应");
  });

  it("readOpenedProject rejects a source with an extra key", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: { ...workspaceSource, uploadId: "upload-1" },
        text: sourceText,
      }),
    ).toThrow("无效的 ThesisForge project 响应");
  });

  it("readOpenedProject rejects a non-string text", () => {
    expect(() =>
      readOpenedProject({ project, source: workspaceSource, text: null }),
    ).toThrow("无效的 ThesisForge project 响应");
  });

  it("readOpenedProject rejects extra top-level keys", () => {
    expect(() =>
      readOpenedProject({
        project,
        source: workspaceSource,
        text: sourceText,
        extra: true,
      }),
    ).toThrow("无效的 ThesisForge project 响应");
  });
});
