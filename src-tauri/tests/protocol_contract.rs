use serde_json::json;
use thesisforge_desktop::{
    PROTOCOL_VERSION, acceptance_source_override, open_source_path, validate_request,
    windows_acceptance_browser_args,
};

#[test]
fn accepts_the_shared_versioned_request_envelope() {
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "request-1",
        "operation": "inspect",
        "payload": {}
    });

    assert!(validate_request(&request).is_ok());
}

#[test]
fn rejects_protocol_drift_before_spawning_python() {
    let request = json!({
        "protocol": "thesisforge.workbench.v0",
        "requestId": "request-1",
        "operation": "inspect",
        "payload": {}
    });

    assert_eq!(
        validate_request(&request).unwrap_err(),
        "unsupported protocol"
    );
}

#[test]
fn reads_a_native_markdown_source_into_the_shared_source_dto() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("thesis.md");
    std::fs::write(&source, "# 绪论\n").unwrap();

    let opened = open_source_path(&source).unwrap();

    assert_eq!(opened["source"]["kind"], "desktop");
    assert_eq!(opened["source"]["fileName"], "thesis.md");
    assert_eq!(opened["text"], "# 绪论\n");
}

#[test]
fn accepts_the_long_markdown_extension() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("thesis.markdown");
    std::fs::write(&source, "# 绪论\n").unwrap();

    let opened = open_source_path(&source).unwrap();

    assert_eq!(opened["source"]["fileName"], "thesis.markdown");
}

#[test]
fn rejects_non_markdown_sources_at_the_native_boundary() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("thesis.txt");
    std::fs::write(&source, "# 绪论\n").unwrap();

    assert_eq!(
        open_source_path(&source).unwrap_err(),
        "source must be a Markdown file (.md or .markdown)"
    );
}

#[test]
fn opens_the_explicit_native_acceptance_source_without_a_system_picker() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("thesis.md");
    std::fs::write(&source, "---\nthesis:\n  title: test\n---\n").unwrap();

    let opened = acceptance_source_override(Some(source.as_os_str()))
        .unwrap()
        .expect("acceptance source");

    assert_eq!(opened["source"]["kind"], "desktop");
    assert_eq!(opened["source"]["fileName"], "thesis.md");
    assert!(opened["text"].as_str().unwrap().contains("thesis:"));
}

#[test]
fn keeps_the_native_acceptance_source_seam_disabled_by_default() {
    assert_eq!(acceptance_source_override(None).unwrap(), None);
}

#[test]
fn rejects_a_request_without_an_object_payload() {
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "request-1",
        "operation": "save"
    });

    assert_eq!(
        validate_request(&request).unwrap_err(),
        "payload is required"
    );
}

#[test]
fn keeps_webview_remote_debugging_disabled_without_the_acceptance_port() {
    assert_eq!(windows_acceptance_browser_args(None).unwrap(), None);
    assert_eq!(windows_acceptance_browser_args(Some("   ")).unwrap(), None);
}

#[test]
fn builds_loopback_only_webview2_arguments_for_native_acceptance() {
    let arguments = windows_acceptance_browser_args(Some("9222"))
        .unwrap()
        .expect("acceptance arguments");

    assert!(arguments.contains("--remote-debugging-address=127.0.0.1"));
    assert!(arguments.contains("--remote-debugging-port=9222"));
    assert!(arguments.contains("--remote-allow-origins=*"));
    assert!(arguments.contains("--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection"));
}

#[test]
fn rejects_unsafe_native_acceptance_cdp_ports() {
    assert_eq!(
        windows_acceptance_browser_args(Some("not-a-port")).unwrap_err(),
        "THESISFORGE_WINDOWS_CDP_PORT must be an integer from 1024 to 65535"
    );
    assert_eq!(
        windows_acceptance_browser_args(Some("80")).unwrap_err(),
        "THESISFORGE_WINDOWS_CDP_PORT must be an integer from 1024 to 65535"
    );
}
