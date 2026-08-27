use super::{
    DEFAULT_SOURCE_PATH, FinalPreviewDescriptor, LivePreviewOutputState, MANIFEST_FILENAME,
    OBSOLETE_MANIFEST_FILENAME, PROJECT_SCHEMA_VERSION, PROTOCOL_VERSION,
    PreviewAuthorizationState, cancellation_path, open_project_path,
    validate_and_prepare_build_preview_authorization,
};
use serde_json::json;
use std::fs;
use std::path::Path;
use tempfile::tempdir;

fn write_project(root: &Path) {
    fs::write(
        root.join(MANIFEST_FILENAME),
        format!(
            r#"schema: {PROJECT_SCHEMA_VERSION}
project:
  id: rust-fixture
  language: zh-CN
document:
  source: {DEFAULT_SOURCE_PATH}
render:
  template_id: example-university-2026
"#,
        ),
    )
    .expect("manifest");
    fs::write(root.join(DEFAULT_SOURCE_PATH), "# 绪论\n").expect("source");
}

#[test]
fn project_directory_and_manifest_path_return_identity_and_source() {
    let temp = tempdir().expect("tempdir");
    write_project(temp.path());

    for input in [
        temp.path().to_path_buf(),
        temp.path().join(MANIFEST_FILENAME),
    ] {
        let result = open_project_path(&input).expect("project");
        assert_eq!(result["project"]["id"], "rust-fixture");
        assert_eq!(
            result["project"]["manifestPath"],
            temp.path()
                .join(MANIFEST_FILENAME)
                .canonicalize()
                .unwrap()
                .to_string_lossy()
                .to_string()
        );
        assert_eq!(result["source"]["fileName"], DEFAULT_SOURCE_PATH);
        assert_eq!(result["text"], "# 绪论\n");
    }
}

#[test]
fn standalone_markdown_is_rejected() {
    let temp = tempdir().expect("tempdir");
    let source = temp.path().join("thesis.md");
    fs::write(&source, "# 绪论\n").expect("source");

    let error = open_project_path(&source).expect_err("bare markdown must fail");
    assert!(error.contains("directory or docforge.yaml"));
}

#[test]
fn traversal_and_missing_source_are_rejected() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        r#"schema: docforge.project.v1
project:
  id: rust-fixture
document:
  source: ../outside.md
"#,
    )
    .expect("manifest");

    let error = open_project_path(temp.path()).expect_err("traversal must fail");
    assert!(error.contains("inside the project root"));

    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        r#"schema: docforge.project.v1
project:
  id: rust-fixture
document:
  source: missing.md
"#,
    )
    .expect("manifest");
    let error = open_project_path(temp.path()).expect_err("missing source must fail");
    assert!(error.contains("does not exist"));
}

#[cfg(unix)]
#[test]
fn symlinked_manifest_is_rejected_when_it_escapes_root() {
    use std::os::unix::fs::symlink;

    let temp = tempdir().expect("tempdir");
    let outside = tempdir().expect("outside");
    write_project(outside.path());
    symlink(
        outside.path().join(MANIFEST_FILENAME),
        temp.path().join(MANIFEST_FILENAME),
    )
    .expect("symlink");

    let error = open_project_path(temp.path()).expect_err("manifest escape must fail");
    assert!(error.contains("escapes the project root"));
}

#[cfg(unix)]
#[test]
fn explicit_symlinked_manifest_is_rejected_when_target_is_external() {
    use std::os::unix::fs::symlink;

    let selected = tempdir().expect("selected");
    let outside = tempdir().expect("outside");
    write_project(outside.path());
    let selected_manifest = selected.path().join(MANIFEST_FILENAME);
    symlink(outside.path().join(MANIFEST_FILENAME), &selected_manifest).expect("symlink");

    let error = open_project_path(&selected_manifest).expect_err("escape must fail");
    assert!(error.contains("escapes the project root"));
}

#[test]
fn windows_absolute_and_uri_source_values_are_rejected_cross_platform() {
    for source in [
        "C:/outside.md",
        r"C:\outside.md",
        "https://example.com/a.md",
    ] {
        let temp = tempdir().expect("tempdir");
        fs::write(
            temp.path().join(MANIFEST_FILENAME),
            format!(
                "schema: {PROJECT_SCHEMA_VERSION}\nproject:\n  id: rust-fixture\ndocument:\n  source: {source}\n"
            ),
        )
        .expect("manifest");
        let error = open_project_path(temp.path()).expect_err("unsafe source must fail");
        assert!(
            error.contains("inside the project root"),
            "{source}: {error}"
        );
    }
}

#[test]
fn omitted_source_defaults_to_document_markdown() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        format!("schema: {PROJECT_SCHEMA_VERSION}\nproject:\n  id: rust-fixture\n"),
    )
    .expect("manifest");
    fs::write(temp.path().join(DEFAULT_SOURCE_PATH), "# 默认源文件\n").expect("source");

    let result = open_project_path(temp.path()).expect("project");

    assert_eq!(result["source"]["fileName"], DEFAULT_SOURCE_PATH);
    assert_eq!(result["text"], "# 默认源文件\n");
}

#[test]
fn rejects_non_markdown_project_sources() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        format!(
            "schema: {PROJECT_SCHEMA_VERSION}\nproject:\n  id: rust-fixture\ndocument:\n  source: notes.txt\n"
        ),
    )
    .expect("manifest");
    fs::write(temp.path().join("notes.txt"), "not Markdown").expect("source");

    let error = open_project_path(temp.path()).expect_err("non-Markdown source must fail");

    assert!(error.contains("Markdown file"));
}

#[test]
fn rejects_nul_project_sources() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        format!(
            "schema: {PROJECT_SCHEMA_VERSION}\nproject:\n  id: rust-fixture\ndocument:\n  source: document\0.md\n"
        ),
    )
    .expect("manifest");

    let error = open_project_path(temp.path()).expect_err("NUL source must fail");

    assert!(error.contains("inside the project root"));
}

#[test]
fn forged_live_preview_output_does_not_revoke_existing_preview_authorization() {
    let temp = tempdir().expect("tempdir");
    let output = temp.path().join("document.docx");
    let preview = temp.path().join("document.preview.pdf");
    fs::write(&output, b"docx").expect("output");
    fs::write(&preview, b"%PDF-1.7\npreview").expect("preview");

    let preview_state = PreviewAuthorizationState::default();
    let authorized = preview_state
        .authorize(
            &FinalPreviewDescriptor {
                engine: "libreoffice".to_string(),
                label: "LibreOffice PDF".to_string(),
                file_name: "document.preview.pdf".to_string(),
                download_id: None,
                authorization_id: None,
                live_preview_id: None,
            },
            preview.clone(),
        )
        .expect("preview authorization");
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "live-preview-forged",
        "operation": "build",
        "payload": {
            "intent": "live-preview",
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "document.docx",
                "livePreviewId": "f".repeat(32)
            }
        }
    });

    let error = validate_and_prepare_build_preview_authorization(
        &preview_state,
        &LivePreviewOutputState::default(),
        &request,
    )
    .expect_err("forged live preview output must fail before revoke");

    assert!(error.contains("not authorized"));
    assert_eq!(
        preview_state
            .resolve(&authorized)
            .expect("old authorization"),
        preview.canonicalize().expect("canonical preview")
    );
}

#[test]
fn invalid_build_operation_does_not_revoke_existing_preview_authorization() {
    let live_preview_state = LivePreviewOutputState::default();
    let (live_preview_id, output) = live_preview_state.prepare().expect("live preview output");
    let preview = output.with_extension("preview.pdf");
    fs::write(&preview, b"%PDF-1.7\npreview").expect("preview");

    let preview_state = PreviewAuthorizationState::default();
    let authorized = preview_state
        .authorize(
            &FinalPreviewDescriptor {
                engine: "libreoffice".to_string(),
                label: "LibreOffice PDF".to_string(),
                file_name: preview
                    .file_name()
                    .and_then(|value| value.to_str())
                    .expect("preview file name")
                    .to_string(),
                download_id: None,
                authorization_id: None,
                live_preview_id: None,
            },
            preview.clone(),
        )
        .expect("preview authorization");
    let output_value = json!({
        "kind": "desktop",
        "path": output.clone(),
        "fileName": output
            .file_name()
            .and_then(|value| value.to_str())
            .expect("output file name"),
        "livePreviewId": live_preview_id
    });
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "live-preview-invalid-operation",
        "operation": "inspect",
        "payload": {
            "intent": "live-preview",
            "output": output_value.clone()
        }
    });

    let error = validate_and_prepare_build_preview_authorization(
        &preview_state,
        &live_preview_state,
        &request,
    )
    .expect_err("non-build operation must fail before revoke");

    assert_eq!(error, "build stream requires a build operation");
    assert_eq!(
        preview_state
            .resolve(&authorized)
            .expect("old authorization"),
        preview.canonicalize().expect("canonical preview")
    );
    live_preview_state
        .release(&output_value)
        .expect("release live preview output");
}

#[test]
fn cancellation_path_uses_docforge_namespace() {
    let path = cancellation_path();
    let file_name = path
        .file_name()
        .and_then(|value| value.to_str())
        .expect("cancellation file name");

    assert!(file_name.starts_with("docforge-cancel-"));
    assert!(!file_name.starts_with("thesisforge-cancel-"));
}

#[test]
fn rejects_obsolete_manifest_paths_and_directory_entries() {
    let temp = tempdir().expect("tempdir");
    let obsolete = temp.path().join(OBSOLETE_MANIFEST_FILENAME);
    fs::write(&obsolete, "schema: thesisforge.project.v2\n").expect("obsolete manifest");

    let direct_error = open_project_path(&obsolete).expect_err("obsolete path must fail");
    assert!(direct_error.contains("obsolete"));

    let directory_error = open_project_path(temp.path()).expect_err("obsolete entry must fail");
    assert!(directory_error.contains("obsolete"));
    assert!(directory_error.contains(MANIFEST_FILENAME));
}

#[test]
fn rejects_obsolete_project_schema_in_docforge_manifest() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join(MANIFEST_FILENAME),
        "schema: thesisforge.project.v2\nproject:\n  id: rust-fixture\n",
    )
    .expect("manifest");

    let error = open_project_path(temp.path()).expect_err("obsolete schema must fail");

    assert!(error.contains("thesisforge.project.v2"));
    assert!(error.contains(PROJECT_SCHEMA_VERSION));
}
