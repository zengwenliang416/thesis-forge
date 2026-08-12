use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::env;
use std::ffi::OsStr;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use tauri::ipc::{Channel, Response};
use tauri::{AppHandle, State};
use tauri_plugin_shell::{
    ShellExt,
    process::{CommandEvent, TerminatedPayload},
};
use uuid::Uuid;

pub const PROTOCOL_VERSION: &str = "thesisforge.workbench.v1";
const WINDOWS_ACCEPTANCE_CDP_PORT_ENV: &str = "THESISFORGE_WINDOWS_CDP_PORT";
const WINDOWS_ACCEPTANCE_SOURCE_ENV: &str = "THESISFORGE_WINDOWS_ACCEPTANCE_SOURCE";

pub fn windows_acceptance_browser_args(raw_port: Option<&str>) -> Result<Option<String>, String> {
    let Some(raw_port) = raw_port.map(str::trim).filter(|value| !value.is_empty()) else {
        return Ok(None);
    };
    let port = raw_port
        .parse::<u16>()
        .ok()
        .filter(|port| *port >= 1024)
        .ok_or_else(|| {
            format!("{WINDOWS_ACCEPTANCE_CDP_PORT_ENV} must be an integer from 1024 to 65535")
        })?;
    Ok(Some(format!(
        "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection \
         --remote-debugging-address=127.0.0.1 \
         --remote-debugging-port={port} \
         --remote-allow-origins=*"
    )))
}

fn is_markdown_source(path: &Path) -> bool {
    path.extension()
        .and_then(|extension| extension.to_str())
        .is_some_and(|extension| {
            extension.eq_ignore_ascii_case("md") || extension.eq_ignore_ascii_case("markdown")
        })
}

fn is_plain_pdf_name(file_name: &str) -> bool {
    !file_name.is_empty()
        && !file_name.contains('/')
        && !file_name.contains('\\')
        && Path::new(file_name).file_name() == Some(OsStr::new(file_name))
        && Path::new(file_name)
            .extension()
            .and_then(|extension| extension.to_str())
            .is_some_and(|extension| extension.eq_ignore_ascii_case("pdf"))
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct FinalPreviewDescriptor {
    pub engine: String,
    pub label: String,
    pub file_name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub download_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub authorization_id: Option<String>,
}

pub fn validate_final_preview_descriptor(value: &Value) -> Result<FinalPreviewDescriptor, String> {
    let descriptor: FinalPreviewDescriptor = serde_json::from_value(value.clone())
        .map_err(|_| "invalid final preview descriptor".to_string())?;
    if !is_plain_pdf_name(&descriptor.file_name) {
        return Err("final preview fileName must be a plain PDF file name".to_string());
    }
    match (descriptor.engine.as_str(), descriptor.label.as_str()) {
        ("libreoffice", "LibreOffice PDF") | ("wps", "WPS PDF") => {}
        _ => return Err("final preview engine and label do not match".to_string()),
    }
    if descriptor.download_id.is_some() {
        return Err("desktop final preview cannot contain a downloadId".to_string());
    }
    if descriptor.authorization_id.as_ref().is_some_and(|value| {
        value.len() != 32 || !value.chars().all(|character| character.is_ascii_hexdigit())
    }) {
        return Err("desktop final preview authorizationId is invalid".to_string());
    }
    Ok(descriptor)
}

pub fn derived_preview_path(output_path: &Path, file_name: &str) -> Result<PathBuf, String> {
    if !is_plain_pdf_name(file_name) {
        return Err("final preview fileName must be a plain PDF file name".to_string());
    }
    let expected = output_path.with_extension("preview.pdf");
    if expected.file_name() != Some(OsStr::new(file_name)) {
        return Err("final preview is not the derived DOCX sibling".to_string());
    }
    Ok(expected)
}

pub fn read_pdf_preview_path(path: &Path) -> Result<Vec<u8>, String> {
    if !is_plain_pdf_name(
        path.file_name()
            .and_then(|value| value.to_str())
            .unwrap_or_default(),
    ) {
        return Err("preview must be a PDF file".to_string());
    }
    let metadata = std::fs::symlink_metadata(path)
        .map_err(|error| format!("failed to read PDF preview: {error}"))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("preview must be a regular PDF file".to_string());
    }
    let bytes =
        std::fs::read(path).map_err(|error| format!("failed to read PDF preview: {error}"))?;
    if !bytes.starts_with(b"%PDF-") {
        return Err("preview is not a valid PDF".to_string());
    }
    Ok(bytes)
}

pub fn validate_request(request: &Value) -> Result<(), String> {
    let protocol = request
        .get("protocol")
        .and_then(Value::as_str)
        .ok_or_else(|| "protocol is required".to_string())?;
    if protocol != PROTOCOL_VERSION {
        return Err("unsupported protocol".to_string());
    }
    if request.get("requestId").and_then(Value::as_str).is_none() {
        return Err("requestId is required".to_string());
    }
    if request.get("operation").and_then(Value::as_str).is_none() {
        return Err("operation is required".to_string());
    }
    if !request.get("payload").is_some_and(Value::is_object) {
        return Err("payload is required".to_string());
    }
    Ok(())
}

pub fn open_source_path(path: &Path) -> Result<Value, String> {
    if !is_markdown_source(path) {
        return Err("source must be a Markdown file (.md or .markdown)".to_string());
    }
    let text = std::fs::read_to_string(path)
        .map_err(|error| format!("failed to read Markdown source: {error}"))?;
    let file_name = path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "source file name is invalid".to_string())?;
    Ok(serde_json::json!({
        "source": {
            "kind": "desktop",
            "path": path,
            "fileName": file_name
        },
        "text": text
    }))
}

pub fn acceptance_source_override(raw_path: Option<&OsStr>) -> Result<Option<Value>, String> {
    let Some(raw_path) = raw_path.filter(|value| !value.is_empty()) else {
        return Ok(None);
    };
    open_source_path(Path::new(raw_path)).map(Some)
}

fn sidecar_command(stream: bool) -> (String, Vec<String>) {
    let mode = if stream { "--stream" } else { "--once" };
    if let Ok(executable) = env::var("THESISFORGE_SIDECAR_EXECUTABLE") {
        return (executable, vec![mode.to_string()]);
    }
    let python = env::var("THESISFORGE_PYTHON").unwrap_or_else(|_| {
        if cfg!(target_os = "windows") {
            "python".to_string()
        } else {
            "python3".to_string()
        }
    });
    (
        python,
        vec![
            "-m".to_string(),
            "thesis_forge.adapters.sidecar".to_string(),
            mode.to_string(),
        ],
    )
}

fn use_development_sidecar() -> bool {
    cfg!(debug_assertions)
        || env::var_os("THESISFORGE_SIDECAR_EXECUTABLE").is_some()
        || env::var_os("THESISFORGE_PYTHON").is_some()
}

pub fn dispatch_to_sidecar(request: &Value) -> Result<Value, String> {
    validate_request(request)?;
    let (program, args) = sidecar_command(false);
    let mut child = Command::new(program)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| format!("failed to start ThesisForge sidecar: {error}"))?;
    let encoded = serde_json::to_vec(request)
        .map_err(|error| format!("failed to encode sidecar request: {error}"))?;
    let stdin = child
        .stdin
        .as_mut()
        .ok_or_else(|| "sidecar stdin is unavailable".to_string())?;
    stdin
        .write_all(&encoded)
        .and_then(|_| stdin.write_all(b"\n"))
        .map_err(|error| format!("failed to write sidecar request: {error}"))?;
    let output = child
        .wait_with_output()
        .map_err(|error| format!("failed to wait for sidecar: {error}"))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("failed to decode sidecar response: {error}"))
}

async fn dispatch_to_managed_sidecar(app: &AppHandle, request: &Value) -> Result<Value, String> {
    validate_request(request)?;
    let encoded = serde_json::to_vec(request)
        .map_err(|error| format!("failed to encode sidecar request: {error}"))?;
    let command = app
        .shell()
        .sidecar("thesisforge-sidecar")
        .map_err(|error| format!("failed to resolve packaged ThesisForge sidecar: {error}"))?
        .arg("--once");
    let (mut events, mut child) = command
        .spawn()
        .map_err(|error| format!("failed to start packaged ThesisForge sidecar: {error}"))?;
    child
        .write(&[encoded, b"\n".to_vec()].concat())
        .map_err(|error| format!("failed to write packaged sidecar request: {error}"))?;

    let mut stdout = Vec::new();
    let mut stderr = Vec::new();
    let mut terminated = None;
    while let Some(event) = events.recv().await {
        match event {
            CommandEvent::Stdout(line) => stdout.extend(line),
            CommandEvent::Stderr(line) => stderr.extend(line),
            CommandEvent::Error(error) => {
                return Err(format!("packaged ThesisForge sidecar failed: {error}"));
            }
            CommandEvent::Terminated(payload) => terminated = Some(payload),
            _ => {}
        }
    }
    ensure_successful_termination(terminated, &stderr)?;
    serde_json::from_slice(&stdout)
        .map_err(|error| format!("failed to decode packaged sidecar response: {error}"))
}

fn ensure_successful_termination(
    terminated: Option<TerminatedPayload>,
    stderr: &[u8],
) -> Result<(), String> {
    if terminated.as_ref().and_then(|payload| payload.code) == Some(0) {
        return Ok(());
    }
    let detail = String::from_utf8_lossy(stderr).trim().to_string();
    Err(if detail.is_empty() {
        "packaged ThesisForge sidecar terminated without success".to_string()
    } else {
        detail
    })
}

#[derive(Clone, Default)]
struct BuildCancellationState {
    paths: Arc<Mutex<HashMap<String, PathBuf>>>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct AuthorizedPreview {
    engine: String,
    file_name: String,
    path: PathBuf,
}

#[derive(Clone, Default)]
pub struct PreviewAuthorizationState {
    previews: Arc<Mutex<HashMap<String, AuthorizedPreview>>>,
}

impl PreviewAuthorizationState {
    fn stable_path_identity(path: &Path) -> Result<PathBuf, String> {
        let parent = path
            .parent()
            .ok_or_else(|| "PDF preview parent directory is required".to_string())?;
        let file_name = path
            .file_name()
            .ok_or_else(|| "PDF preview file name is required".to_string())?;
        parent
            .canonicalize()
            .map(|canonical_parent| canonical_parent.join(file_name))
            .map_err(|error| format!("failed to resolve PDF preview path: {error}"))
    }

    pub fn authorize(
        &self,
        descriptor: &FinalPreviewDescriptor,
        path: PathBuf,
    ) -> Result<FinalPreviewDescriptor, String> {
        if descriptor.download_id.is_some() || descriptor.authorization_id.is_some() {
            return Err("preview authorization requires an unlocated descriptor".to_string());
        }
        let stable_path = Self::stable_path_identity(&path)?;
        let authorization_id = Uuid::new_v4().simple().to_string();
        self.previews
            .lock()
            .map_err(|_| "preview authorization state is unavailable".to_string())?
            .insert(
                authorization_id.clone(),
                AuthorizedPreview {
                    engine: descriptor.engine.clone(),
                    file_name: descriptor.file_name.clone(),
                    path: stable_path,
                },
            );
        Ok(FinalPreviewDescriptor {
            authorization_id: Some(authorization_id),
            ..descriptor.clone()
        })
    }

    pub fn resolve(&self, descriptor: &FinalPreviewDescriptor) -> Result<PathBuf, String> {
        let authorization_id = descriptor
            .authorization_id
            .as_ref()
            .ok_or_else(|| "PDF preview authorizationId is required".to_string())?;
        let preview = self
            .previews
            .lock()
            .map_err(|_| "preview authorization state is unavailable".to_string())?
            .get(authorization_id)
            .cloned()
            .ok_or_else(|| "PDF preview is not authorized".to_string())?;
        if preview.engine != descriptor.engine || preview.file_name != descriptor.file_name {
            return Err("PDF preview authorization does not match descriptor".to_string());
        }
        Ok(preview.path)
    }

    pub fn revoke(&self, descriptor: &FinalPreviewDescriptor) -> Result<(), String> {
        let Some(authorization_id) = descriptor.authorization_id.as_ref() else {
            return Ok(());
        };
        self.previews
            .lock()
            .map_err(|_| "preview authorization state is unavailable".to_string())?
            .remove(authorization_id);
        Ok(())
    }

    pub fn revoke_path(&self, path: &Path) -> Result<(), String> {
        let stable_path = Self::stable_path_identity(path)?;
        self.previews
            .lock()
            .map_err(|_| "preview authorization state is unavailable".to_string())?
            .retain(|_, preview| preview.path != stable_path);
        Ok(())
    }
}

fn requested_build_preview(
    request: &Value,
) -> Result<Option<(FinalPreviewDescriptor, PathBuf)>, String> {
    let Some(output) = request
        .get("payload")
        .and_then(|payload| payload.get("output"))
    else {
        return Ok(None);
    };
    if output.get("kind").and_then(Value::as_str) != Some("desktop") {
        return Ok(None);
    }
    let output_path = output
        .get("path")
        .and_then(Value::as_str)
        .ok_or_else(|| "desktop build output path is required".to_string())?;
    let preview_path = Path::new(output_path).with_extension("preview.pdf");
    let file_name = preview_path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "derived preview file name is invalid".to_string())?
        .to_string();
    Ok(Some((
        FinalPreviewDescriptor {
            engine: "libreoffice".to_string(),
            label: "LibreOffice PDF".to_string(),
            file_name,
            download_id: None,
            authorization_id: None,
        },
        preview_path,
    )))
}

pub fn prepare_build_preview_authorization(
    state: &PreviewAuthorizationState,
    request: &Value,
) -> Result<(), String> {
    if let Some((_, path)) = requested_build_preview(request)? {
        state.revoke_path(&path)?;
    }
    Ok(())
}

pub fn authorize_build_preview(
    state: &PreviewAuthorizationState,
    request: &Value,
    event: &Value,
) -> Result<Value, String> {
    if event.get("type").and_then(Value::as_str) != Some("success") {
        return Ok(event.clone());
    }
    let Some(descriptor_value) = event
        .get("result")
        .and_then(|result| result.get("output"))
        .and_then(|output| output.get("finalPreview"))
    else {
        return Ok(event.clone());
    };
    let descriptor = validate_final_preview_descriptor(descriptor_value)?;
    if descriptor.engine != "libreoffice" {
        return Err("build final preview must be a LibreOffice PDF".to_string());
    }
    let (_, requested_path) = requested_build_preview(request)?
        .ok_or_else(|| "desktop build output is required".to_string())?;
    if requested_path.file_name() != Some(OsStr::new(&descriptor.file_name)) {
        return Err("final preview is not the derived DOCX sibling".to_string());
    }
    let authorized = state.authorize(&descriptor, requested_path)?;
    let mut authorized_event = event.clone();
    authorized_event["result"]["output"]["finalPreview"] = serde_json::to_value(authorized)
        .map_err(|error| format!("failed to encode preview authorization: {error}"))?;
    Ok(authorized_event)
}

static CANCEL_TOKEN: AtomicU64 = AtomicU64::new(1);

fn cancellation_path() -> PathBuf {
    env::temp_dir().join(format!(
        "thesisforge-cancel-{}-{}",
        std::process::id(),
        CANCEL_TOKEN.fetch_add(1, Ordering::Relaxed)
    ))
}

fn stream_sidecar_events(
    request: &Value,
    cancel_path: &Path,
    on_event: &Channel<Value>,
    preview_state: &PreviewAuthorizationState,
) -> Result<(), String> {
    validate_request(request)?;
    if request.get("operation").and_then(Value::as_str) != Some("build") {
        return Err("build stream requires a build operation".to_string());
    }
    let (program, args) = sidecar_command(true);
    let mut child = Command::new(program)
        .args(args)
        .env("THESISFORGE_CANCEL_FILE", cancel_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| format!("failed to start ThesisForge sidecar: {error}"))?;
    let encoded = serde_json::to_vec(request)
        .map_err(|error| format!("failed to encode sidecar request: {error}"))?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| "sidecar stdin is unavailable".to_string())?;
    stdin
        .write_all(&encoded)
        .and_then(|_| stdin.write_all(b"\n"))
        .map_err(|error| format!("failed to write sidecar request: {error}"))?;
    drop(stdin);

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "sidecar stdout is unavailable".to_string())?;
    for line in BufReader::new(stdout).lines() {
        let line = line.map_err(|error| format!("failed to read sidecar event: {error}"))?;
        let event: Value = serde_json::from_str(&line)
            .map_err(|error| format!("failed to decode sidecar event: {error}"))?;
        let event = authorize_build_preview(preview_state, request, &event)?;
        on_event
            .send(event)
            .map_err(|error| format!("failed to forward sidecar event: {error}"))?;
    }
    let status = child
        .wait()
        .map_err(|error| format!("failed to wait for sidecar: {error}"))?;
    if !status.success() {
        let mut stderr = String::new();
        if let Some(mut stream) = child.stderr.take() {
            let _ = stream.read_to_string(&mut stderr);
        }
        return Err(stderr.trim().to_string());
    }
    Ok(())
}

async fn stream_managed_sidecar_events(
    app: &AppHandle,
    request: &Value,
    cancel_path: &Path,
    on_event: &Channel<Value>,
    preview_state: &PreviewAuthorizationState,
) -> Result<(), String> {
    validate_request(request)?;
    if request.get("operation").and_then(Value::as_str) != Some("build") {
        return Err("build stream requires a build operation".to_string());
    }
    let encoded = serde_json::to_vec(request)
        .map_err(|error| format!("failed to encode sidecar request: {error}"))?;
    let command = app
        .shell()
        .sidecar("thesisforge-sidecar")
        .map_err(|error| format!("failed to resolve packaged ThesisForge sidecar: {error}"))?
        .arg("--stream")
        .env("THESISFORGE_CANCEL_FILE", cancel_path);
    let (mut events, mut child) = command
        .spawn()
        .map_err(|error| format!("failed to start packaged ThesisForge sidecar: {error}"))?;
    child
        .write(&[encoded, b"\n".to_vec()].concat())
        .map_err(|error| format!("failed to write packaged sidecar request: {error}"))?;

    let mut stderr = Vec::new();
    let mut terminated = None;
    while let Some(event) = events.recv().await {
        match event {
            CommandEvent::Stdout(line) => {
                let event: Value = serde_json::from_slice(&line)
                    .map_err(|error| format!("failed to decode packaged sidecar event: {error}"))?;
                let event = authorize_build_preview(preview_state, request, &event)?;
                on_event.send(event).map_err(|error| {
                    format!("failed to forward packaged sidecar event: {error}")
                })?;
            }
            CommandEvent::Stderr(line) => stderr.extend(line),
            CommandEvent::Error(error) => {
                return Err(format!("packaged ThesisForge sidecar failed: {error}"));
            }
            CommandEvent::Terminated(payload) => terminated = Some(payload),
            _ => {}
        }
    }
    ensure_successful_termination(terminated, &stderr)
}

#[tauri::command]
async fn dispatch_workbench(app: AppHandle, request: Value) -> Result<Value, String> {
    if use_development_sidecar() {
        return tauri::async_runtime::spawn_blocking(move || dispatch_to_sidecar(&request))
            .await
            .map_err(|error| format!("sidecar task failed: {error}"))?;
    }
    dispatch_to_managed_sidecar(&app, &request).await
}

#[tauri::command]
async fn run_build(
    app: AppHandle,
    request: Value,
    on_event: Channel<Value>,
    state: State<'_, BuildCancellationState>,
    preview_state: State<'_, PreviewAuthorizationState>,
) -> Result<(), String> {
    let request_id = request
        .get("requestId")
        .and_then(Value::as_str)
        .ok_or_else(|| "requestId is required".to_string())?
        .to_string();
    prepare_build_preview_authorization(preview_state.inner(), &request)?;
    let cancel_path = cancellation_path();
    let _ = std::fs::remove_file(&cancel_path);
    state
        .paths
        .lock()
        .map_err(|_| "build cancellation state is unavailable".to_string())?
        .insert(request_id.clone(), cancel_path.clone());
    let active = state.inner().clone();
    let result = if use_development_sidecar() {
        let request = request.clone();
        let cancel_path = cancel_path.clone();
        let preview_state = preview_state.inner().clone();
        tauri::async_runtime::spawn_blocking(move || {
            stream_sidecar_events(&request, &cancel_path, &on_event, &preview_state)
        })
        .await
        .map_err(|error| format!("sidecar build task failed: {error}"))?
    } else {
        stream_managed_sidecar_events(
            &app,
            &request,
            &cancel_path,
            &on_event,
            preview_state.inner(),
        )
        .await
    };
    let _ = std::fs::remove_file(&cancel_path);
    if let Ok(mut paths) = active.paths.lock() {
        paths.remove(&request_id);
    }
    result
}

#[tauri::command]
async fn cancel_build(
    request_id: String,
    state: State<'_, BuildCancellationState>,
) -> Result<bool, String> {
    let path = state
        .paths
        .lock()
        .map_err(|_| "build cancellation state is unavailable".to_string())?
        .get(&request_id)
        .cloned();
    if let Some(path) = path {
        std::fs::write(path, b"cancel")
            .map_err(|error| format!("failed to cancel build: {error}"))?;
        return Ok(true);
    }
    Ok(false)
}

#[tauri::command]
async fn pick_source() -> Result<Option<Value>, String> {
    if let Some(opened) =
        acceptance_source_override(env::var_os(WINDOWS_ACCEPTANCE_SOURCE_ENV).as_deref())?
    {
        return Ok(Some(opened));
    }
    let handle = rfd::AsyncFileDialog::new()
        .set_title("选择 Markdown 文稿（.md 或 .markdown）")
        .pick_file()
        .await;
    handle.map(|file| open_source_path(file.path())).transpose()
}

#[tauri::command]
async fn pick_pdf_preview(
    state: State<'_, PreviewAuthorizationState>,
) -> Result<Option<Value>, String> {
    let handle = rfd::AsyncFileDialog::new()
        .set_title("选择 WPS 导出的 PDF")
        .add_filter("PDF", &["pdf"])
        .pick_file()
        .await;
    let Some(file) = handle else {
        return Ok(None);
    };
    let path = file.path();
    read_pdf_preview_path(path)?;
    let file_name = path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "PDF preview file name is invalid".to_string())?
        .to_string();
    let descriptor = FinalPreviewDescriptor {
        engine: "wps".to_string(),
        label: "WPS PDF".to_string(),
        file_name,
        download_id: None,
        authorization_id: None,
    };
    let descriptor = state.authorize(&descriptor, path.to_path_buf())?;
    Ok(Some(serde_json::to_value(descriptor).map_err(|error| {
        format!("failed to encode preview authorization: {error}")
    })?))
}

#[tauri::command]
async fn read_pdf_preview(
    descriptor: Value,
    state: State<'_, PreviewAuthorizationState>,
) -> Result<Response, String> {
    let descriptor = validate_final_preview_descriptor(&descriptor)?;
    let path = state.resolve(&descriptor)?;
    Ok(Response::new(read_pdf_preview_path(&path)?))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BuildCancellationState::default())
        .manage(PreviewAuthorizationState::default())
        .setup(|app| {
            let window_config = app
                .config()
                .app
                .windows
                .first()
                .ok_or_else(|| std::io::Error::other("main window config is missing"))?;
            let window_builder =
                tauri::WebviewWindowBuilder::from_config(app.handle(), window_config)?;
            #[cfg(target_os = "windows")]
            let window_builder = {
                let browser_args = windows_acceptance_browser_args(
                    env::var(WINDOWS_ACCEPTANCE_CDP_PORT_ENV).ok().as_deref(),
                )
                .map_err(std::io::Error::other)?;
                if let Some(browser_args) = browser_args {
                    window_builder.additional_browser_args(&browser_args)
                } else {
                    window_builder
                }
            };
            window_builder.build()?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            dispatch_workbench,
            run_build,
            cancel_build,
            pick_source,
            pick_pdf_preview,
            read_pdf_preview
        ])
        .run(tauri::generate_context!())
        .expect("error while running ThesisForge desktop");
}
