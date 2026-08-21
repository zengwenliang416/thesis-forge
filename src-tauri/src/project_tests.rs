use super::open_project_path;
use std::fs;
use std::path::Path;
use tempfile::tempdir;

fn write_project(root: &Path) {
    fs::write(
        root.join("thesisforge.yaml"),
        r#"schema: thesisforge.project.v2
project:
  id: rust-fixture
  language: zh-CN
document:
  source: thesis.md
render:
  template_id: example-university-2026
"#,
    )
    .expect("manifest");
    fs::write(root.join("thesis.md"), "# 绪论\n").expect("source");
}

#[test]
fn project_directory_and_manifest_path_return_identity_and_source() {
    let temp = tempdir().expect("tempdir");
    write_project(temp.path());

    for input in [
        temp.path().to_path_buf(),
        temp.path().join("thesisforge.yaml"),
    ] {
        let result = open_project_path(&input).expect("project");
        assert_eq!(result["project"]["id"], "rust-fixture");
        assert_eq!(
            result["project"]["manifestPath"],
            temp.path()
                .join("thesisforge.yaml")
                .canonicalize()
                .unwrap()
                .to_string_lossy()
                .to_string()
        );
        assert_eq!(result["source"]["fileName"], "thesis.md");
        assert_eq!(result["text"], "# 绪论\n");
    }
}

#[test]
fn standalone_markdown_is_rejected() {
    let temp = tempdir().expect("tempdir");
    let source = temp.path().join("thesis.md");
    fs::write(&source, "# 绪论\n").expect("source");

    let error = open_project_path(&source).expect_err("bare markdown must fail");
    assert!(error.contains("directory or thesisforge.yaml"));
}

#[test]
fn traversal_and_missing_source_are_rejected() {
    let temp = tempdir().expect("tempdir");
    fs::write(
        temp.path().join("thesisforge.yaml"),
        r#"schema: thesisforge.project.v2
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
        temp.path().join("thesisforge.yaml"),
        r#"schema: thesisforge.project.v2
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
        outside.path().join("thesisforge.yaml"),
        temp.path().join("thesisforge.yaml"),
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
    let selected_manifest = selected.path().join("thesisforge.yaml");
    symlink(outside.path().join("thesisforge.yaml"), &selected_manifest).expect("symlink");

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
            temp.path().join("thesisforge.yaml"),
            format!(
                "schema: thesisforge.project.v2\nproject:\n  id: rust-fixture\ndocument:\n  source: {source}\n"
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
