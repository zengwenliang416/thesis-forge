use serde_json::json;
use thesisforge_desktop::{PROTOCOL_VERSION, open_source_path, validate_request};

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
