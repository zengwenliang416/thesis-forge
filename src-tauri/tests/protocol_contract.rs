use serde_json::json;
use std::path::Path;
use thesisforge_desktop::{
    FinalPreviewDescriptor, LivePreviewOutputState, PROTOCOL_VERSION, PreviewAuthorizationState,
    acceptance_source_override, authorize_build_preview, cleanup_live_preview_output_path,
    cleanup_live_preview_path, derived_preview_path, live_preview_output_path, open_source_path,
    prepare_build_preview_authorization, read_pdf_preview_path, validate_final_preview_descriptor,
    validate_request, windows_acceptance_browser_args,
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

#[test]
fn accepts_only_strict_path_free_desktop_preview_descriptors() {
    let word_descriptor = json!({
        "engine": "microsoft-word",
        "label": "Microsoft Word PDF",
        "fileName": "thesis.preview.pdf",
        "authorizationId": "b".repeat(32)
    });
    let descriptor = json!({
        "engine": "libreoffice",
        "label": "LibreOffice PDF",
        "fileName": "thesis.preview.pdf",
        "authorizationId": "a".repeat(32)
    });

    assert!(validate_final_preview_descriptor(&word_descriptor).is_ok());
    assert!(validate_final_preview_descriptor(&descriptor).is_ok());
    assert!(
        validate_final_preview_descriptor(&json!({
            "engine": "libreoffice",
            "label": "WPS PDF",
            "fileName": "thesis.preview.pdf"
        }))
        .is_err()
    );
    assert!(
        validate_final_preview_descriptor(&json!({
            "engine": "wps",
            "label": "WPS PDF",
            "fileName": "../private.pdf"
        }))
        .is_err()
    );
    assert!(
        validate_final_preview_descriptor(&json!({
            "engine": "libreoffice",
            "label": "LibreOffice PDF",
            "fileName": "thesis.preview.pdf",
            "path": "/private/thesis.preview.pdf"
        }))
        .is_err()
    );
}

fn preview_descriptor(engine: &str, label: &str, file_name: &str) -> FinalPreviewDescriptor {
    FinalPreviewDescriptor {
        engine: engine.to_string(),
        label: label.to_string(),
        file_name: file_name.to_string(),
        download_id: None,
        authorization_id: None,
        live_preview_id: None,
    }
}

#[test]
fn authorization_handles_keep_same_named_pdfs_bound_to_their_selected_paths() {
    let first = tempfile::tempdir().unwrap();
    let second = tempfile::tempdir().unwrap();
    let first_pdf = first.path().join("export.pdf");
    let second_pdf = second.path().join("export.pdf");
    std::fs::write(&first_pdf, b"%PDF-1.7\nfirst").unwrap();
    std::fs::write(&second_pdf, b"%PDF-1.7\nsecond").unwrap();
    let state = PreviewAuthorizationState::default();
    let descriptor =
        preview_descriptor("microsoft-word", "Microsoft Word PDF", "export.pdf");

    let first_authorized = state.authorize(&descriptor, first_pdf.clone()).unwrap();
    let second_authorized = state.authorize(&descriptor, second_pdf.clone()).unwrap();

    assert_ne!(
        first_authorized.authorization_id,
        second_authorized.authorization_id
    );
    assert_eq!(
        state.resolve(&first_authorized).unwrap(),
        first_pdf.canonicalize().unwrap()
    );
    assert_eq!(
        state.resolve(&second_authorized).unwrap(),
        second_pdf.canonicalize().unwrap()
    );
    assert_eq!(
        read_pdf_preview_path(&state.resolve(&first_authorized).unwrap()).unwrap(),
        b"%PDF-1.7\nfirst"
    );
}

#[test]
fn authorization_rejects_descriptor_drift_and_revocation() {
    let directory = tempfile::tempdir().unwrap();
    let pdf = directory.path().join("export.pdf");
    std::fs::write(&pdf, b"%PDF-1.7\npreview").unwrap();
    let state = PreviewAuthorizationState::default();
    let descriptor =
        preview_descriptor("microsoft-word", "Microsoft Word PDF", "export.pdf");
    let authorized = state.authorize(&descriptor, pdf).unwrap();
    let mut drifted = authorized.clone();
    drifted.file_name = "other.pdf".to_string();

    assert!(state.resolve(&drifted).is_err());
    state.revoke(&authorized).unwrap();
    assert!(state.resolve(&authorized).is_err());
}

#[test]
fn build_success_authorizes_only_the_derived_preview_and_injects_an_opaque_id() {
    let directory = tempfile::tempdir().unwrap();
    let output = directory.path().join("thesis.docx");
    let preview = directory.path().join("thesis.preview.pdf");
    std::fs::write(&output, b"docx").unwrap();
    std::fs::write(&preview, b"%PDF-1.7\npreview").unwrap();
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-1",
        "operation": "build",
        "payload": {
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "thesis.docx"
            }
        }
    });
    let event = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-1",
        "type": "completed",
        "report": {
            "schemaVersion": "thesisforge.build-report.v2",
            "buildId": "build-1",
            "intent": "publish",
            "outcome": "succeeded",
            "stages": [
                {
                    "name": "parse",
                    "status": "succeeded"
                }
            ],
            "failedStage": null,
            "primaryDiagnosticId": null,
            "diagnostics": [],
            "logs": [],
            "output": {
                "docxPath": output,
                "pdfPath": preview,
                "previewStale": false,
                "successfulBuildId": "build-1",
                "finalPreview": {
                    "engine": "microsoft-word",
                    "label": "Microsoft Word PDF",
                    "fileName": "thesis.preview.pdf"
                }
            },
        }
    });
    let state = PreviewAuthorizationState::default();

    let authorized_event = authorize_build_preview(&state, &request, &event).unwrap();
    let descriptor =
        validate_final_preview_descriptor(&authorized_event["report"]["output"]["finalPreview"])
            .unwrap();

    assert_eq!(descriptor.engine, "microsoft-word");
    assert_eq!(
        descriptor.authorization_id.as_deref().map(str::len),
        Some(32)
    );
    assert_eq!(
        read_pdf_preview_path(&state.resolve(&descriptor).unwrap()).unwrap(),
        b"%PDF-1.7\npreview"
    );
}

#[test]
fn completed_report_without_preview_passes_through_and_request_drift_fails() {
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-1",
        "operation": "build",
        "payload": {}
    });
    let event = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-1",
        "type": "completed",
        "report": {
            "schemaVersion": "thesisforge.build-report.v2",
            "buildId": "build-1",
            "intent": "publish",
            "outcome": "succeeded",
            "stages": [{ "name": "parse", "status": "succeeded" }],
            "failedStage": null,
            "primaryDiagnosticId": null,
            "diagnostics": [],
            "logs": [],
            "output": null
        }
    });
    let state = PreviewAuthorizationState::default();
    assert_eq!(
        authorize_build_preview(&state, &request, &event).unwrap(),
        event
    );

    let mut drifted = event.clone();
    drifted["requestId"] = json!("build-2");
    assert!(authorize_build_preview(&state, &request, &drifted).is_err());
}

#[test]
fn completed_live_preview_authorization_marks_cleanup_after_read() {
    let directory = tempfile::tempdir().unwrap();
    let output = directory.path().join("thesis.docx");
    let preview = directory.path().join("thesis.preview.pdf");
    std::fs::write(&output, b"docx").unwrap();
    std::fs::write(&preview, b"%PDF-1.7\npreview").unwrap();
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "live-1",
        "operation": "build",
        "payload": {
            "intent": "live-preview",
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "thesis.docx"
            }
        }
    });
    let event = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "live-1",
        "type": "completed",
        "report": {
            "schemaVersion": "thesisforge.build-report.v2",
            "buildId": "build-live-1",
            "intent": "live-preview",
            "outcome": "succeeded",
            "stages": [{ "name": "preview", "status": "succeeded" }],
            "failedStage": null,
            "primaryDiagnosticId": null,
            "diagnostics": [],
            "logs": [],
            "output": {
                "docxPath": "thesis.docx",
                "pdfPath": "thesis.preview.pdf",
                "previewStale": false,
                "successfulBuildId": "build-live-1",
                "finalPreview": {
                    "engine": "libreoffice",
                    "label": "LibreOffice PDF",
                    "fileName": "thesis.preview.pdf"
                }
            }
        }
    });
    let state = PreviewAuthorizationState::default();
    let authorized = authorize_build_preview(&state, &request, &event).unwrap();
    let descriptor =
        validate_final_preview_descriptor(&authorized["report"]["output"]["finalPreview"]).unwrap();
    let (_, cleanup_after_read) = state.resolve_with_cleanup(&descriptor).unwrap();
    assert!(cleanup_after_read);
}

#[test]
fn a_new_failed_or_canceled_build_revokes_the_previous_derived_authorization() {
    let directory = tempfile::tempdir().unwrap();
    let output = directory.path().join("thesis.docx");
    let preview = directory.path().join("thesis.preview.pdf");
    std::fs::write(&output, b"docx").unwrap();
    std::fs::write(&preview, b"%PDF-1.7\npreview").unwrap();
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-1",
        "operation": "build",
        "payload": {
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "thesis.docx"
            }
        }
    });
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor("libreoffice", "LibreOffice PDF", "thesis.preview.pdf"),
            preview,
        )
        .unwrap();

    prepare_build_preview_authorization(&state, &request).unwrap();
    assert!(state.resolve(&descriptor).is_err());

    for outcome in ["failed", "canceled"] {
        let event = json!({
            "protocol": PROTOCOL_VERSION,
            "requestId": "build-1",
            "type": "completed",
            "report": {
                "schemaVersion": "thesisforge.build-report.v2",
                "buildId": "build-2",
                "intent": "live-preview",
                "outcome": outcome,
                "stages": [
                    { "name": "parse", "status": "succeeded" },
                    { "name": "render", "status": "failed" }
                ],
                "failedStage": "render",
                "primaryDiagnosticId": null,
                "diagnostics": [],
                "logs": [],
                "output": {
                    "docxPath": null,
                    "pdfPath": null,
                    "previewStale": true,
                    "successfulBuildId": null,
                    "finalPreview": {
                        "engine": "libreoffice",
                        "label": "LibreOffice PDF",
                        "fileName": "thesis.preview.pdf"
                    }
                }
            }
        });
        assert_eq!(
            authorize_build_preview(&state, &request, &event).unwrap(),
            event
        );
    }
}

#[test]
fn a_new_build_revokes_authorization_after_the_old_preview_is_deleted() {
    let directory = tempfile::tempdir().unwrap();
    let output = directory.path().join("thesis.docx");
    let preview = directory.path().join("thesis.preview.pdf");
    std::fs::write(&output, b"docx").unwrap();
    std::fs::write(&preview, b"%PDF-1.7\npreview").unwrap();
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-2",
        "operation": "build",
        "payload": {
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "thesis.docx"
            }
        }
    });
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor("libreoffice", "LibreOffice PDF", "thesis.preview.pdf"),
            preview.clone(),
        )
        .unwrap();
    std::fs::remove_file(preview).unwrap();

    prepare_build_preview_authorization(&state, &request).unwrap();

    assert!(state.resolve(&descriptor).is_err());
}

#[cfg(unix)]
#[test]
fn a_new_build_revokes_old_authorization_after_preview_becomes_a_symlink() {
    use std::os::unix::fs::symlink;

    let directory = tempfile::tempdir().unwrap();
    let output = directory.path().join("thesis.docx");
    let preview = directory.path().join("thesis.preview.pdf");
    let target = directory.path().join("target.pdf");
    std::fs::write(&output, b"docx").unwrap();
    std::fs::write(&preview, b"%PDF-1.7\nold preview").unwrap();
    std::fs::write(&target, b"%PDF-1.7\nsymlink target").unwrap();
    let request = json!({
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-3",
        "operation": "build",
        "payload": {
            "output": {
                "kind": "desktop",
                "path": output,
                "fileName": "thesis.docx"
            }
        }
    });
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor("libreoffice", "LibreOffice PDF", "thesis.preview.pdf"),
            preview.clone(),
        )
        .unwrap();

    std::fs::remove_file(&preview).unwrap();
    symlink(&target, &preview).unwrap();
    prepare_build_preview_authorization(&state, &request).unwrap();
    std::fs::remove_file(&preview).unwrap();
    std::fs::write(&preview, b"%PDF-1.7\nnew preview").unwrap();

    assert!(state.resolve(&descriptor).is_err());
}

#[test]
fn authorization_revalidates_symlinks_and_pdf_content_at_read_time() {
    let directory = tempfile::tempdir().unwrap();
    let pdf = directory.path().join("preview.pdf");
    std::fs::write(&pdf, b"%PDF-1.7\npreview").unwrap();
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor(
                "microsoft-word",
                "Microsoft Word PDF",
                "preview.pdf",
            ),
            pdf.clone(),
        )
        .unwrap();

    std::fs::write(&pdf, b"not a pdf").unwrap();
    assert!(read_pdf_preview_path(&state.resolve(&descriptor).unwrap()).is_err());
}

#[cfg(unix)]
#[test]
fn authorization_rejects_a_file_replaced_by_a_symlink_at_read_time() {
    use std::os::unix::fs::symlink;

    let directory = tempfile::tempdir().unwrap();
    let pdf = directory.path().join("preview.pdf");
    let target = directory.path().join("target.pdf");
    std::fs::write(&pdf, b"%PDF-1.7\npreview").unwrap();
    std::fs::write(&target, b"%PDF-1.7\ntarget").unwrap();
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor(
                "microsoft-word",
                "Microsoft Word PDF",
                "preview.pdf",
            ),
            pdf.clone(),
        )
        .unwrap();

    std::fs::remove_file(&pdf).unwrap();
    symlink(&target, &pdf).unwrap();

    assert!(read_pdf_preview_path(&state.resolve(&descriptor).unwrap()).is_err());
}

#[test]
fn derives_only_the_fixed_preview_pdf_sibling() {
    let output = Path::new("/tmp/thesis.docx");

    assert_eq!(
        derived_preview_path(output, "thesis.preview.pdf").unwrap(),
        Path::new("/tmp/thesis.preview.pdf")
    );
    assert!(derived_preview_path(output, "other.pdf").is_err());
    assert!(derived_preview_path(output, "../thesis.preview.pdf").is_err());
}

#[test]
fn reads_only_regular_pdf_signature_files() {
    let directory = tempfile::tempdir().unwrap();
    let pdf = directory.path().join("preview.pdf");
    let invalid = directory.path().join("invalid.pdf");
    let wrong_extension = directory.path().join("preview.txt");
    std::fs::write(&pdf, b"%PDF-1.7\npreview").unwrap();
    std::fs::write(&invalid, b"not a pdf").unwrap();
    std::fs::write(&wrong_extension, b"%PDF-1.7\npreview").unwrap();

    assert_eq!(read_pdf_preview_path(&pdf).unwrap(), b"%PDF-1.7\npreview");
    assert!(read_pdf_preview_path(&invalid).is_err());
    assert!(read_pdf_preview_path(&wrong_extension).is_err());
}

#[test]
fn live_preview_output_is_unique_and_cleanup_is_scoped_to_its_directory() {
    let first = live_preview_output_path().unwrap();
    let second = live_preview_output_path().unwrap();
    assert_ne!(first, second);
    assert!(
        first
            .file_name()
            .and_then(|value| value.to_str())
            .is_some_and(|value| value.starts_with("thesisforge-live-preview-"))
    );

    std::fs::write(&first, b"docx").unwrap();
    let pdf = first.with_extension("preview.pdf");
    std::fs::write(&pdf, b"%PDF-1.7\npreview").unwrap();
    let parent = first.parent().unwrap().to_path_buf();

    cleanup_live_preview_path(&pdf.canonicalize().unwrap());

    assert!(!first.exists());
    assert!(!pdf.exists());
    assert!(!parent.exists());
    let _ = std::fs::remove_dir_all(second.parent().unwrap());
}

#[test]
fn prepared_live_preview_output_can_be_discarded_before_build_starts() {
    let output = live_preview_output_path().unwrap();
    let parent = output.parent().unwrap().to_path_buf();

    cleanup_live_preview_output_path(&output).unwrap();

    assert!(!parent.exists());
}

#[test]
fn live_preview_output_state_rejects_forged_capabilities_and_releases_idempotently() {
    let state = LivePreviewOutputState::default();
    let (live_preview_id, output) = state.prepare().unwrap();
    let value = json!({
        "kind": "desktop",
        "path": output,
        "fileName": output.file_name().unwrap().to_str().unwrap(),
        "livePreviewId": live_preview_id,
    });
    let forged = json!({
        "kind": "desktop",
        "path": output,
        "fileName": output.file_name().unwrap().to_str().unwrap(),
        "livePreviewId": "f".repeat(32),
    });

    assert!(state.validate_output(&forged).is_err());
    state.release(&value).unwrap();
    state.release(&value).unwrap();
    assert!(!output.parent().unwrap().exists());
}

#[test]
fn formal_preview_authorization_never_requests_live_cleanup() {
    let directory = tempfile::tempdir().unwrap();
    let pdf = directory.path().join("thesis.preview.pdf");
    std::fs::write(&pdf, b"%PDF-1.7\nformal").unwrap();
    let state = PreviewAuthorizationState::default();
    let descriptor = state
        .authorize(
            &preview_descriptor("libreoffice", "LibreOffice PDF", "thesis.preview.pdf"),
            pdf.clone(),
        )
        .unwrap();

    let (resolved, cleanup_after_read) = state.resolve_with_cleanup(&descriptor).unwrap();

    assert_eq!(resolved, pdf.canonicalize().unwrap());
    assert!(!cleanup_after_read);
    assert!(pdf.exists());
}
