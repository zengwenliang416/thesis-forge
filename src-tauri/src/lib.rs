use serde_json::Value;
use std::collections::HashMap;
use std::env;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use tauri::State;
use tauri::ipc::Channel;

pub const PROTOCOL_VERSION: &str = "thesisforge.workbench.v1";

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

#[derive(Clone, Default)]
struct BuildCancellationState {
    paths: Arc<Mutex<HashMap<String, PathBuf>>>,
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

#[tauri::command]
async fn dispatch_workbench(request: Value) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || dispatch_to_sidecar(&request))
        .await
        .map_err(|error| format!("sidecar task failed: {error}"))?
}

#[tauri::command]
async fn run_build(
    request: Value,
    on_event: Channel<Value>,
    state: State<'_, BuildCancellationState>,
) -> Result<(), String> {
    let request_id = request
        .get("requestId")
        .and_then(Value::as_str)
        .ok_or_else(|| "requestId is required".to_string())?
        .to_string();
    let cancel_path = cancellation_path();
    let _ = std::fs::remove_file(&cancel_path);
    state
        .paths
        .lock()
        .map_err(|_| "build cancellation state is unavailable".to_string())?
        .insert(request_id.clone(), cancel_path.clone());
    let active = state.inner().clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        let result = stream_sidecar_events(&request, &cancel_path, &on_event);
        let _ = std::fs::remove_file(&cancel_path);
        if let Ok(mut paths) = active.paths.lock() {
            paths.remove(&request_id);
        }
        result
    })
    .await
    .map_err(|error| format!("sidecar build task failed: {error}"))?;
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
    let handle = rfd::AsyncFileDialog::new()
        .add_filter("Markdown", &["md"])
        .pick_file()
        .await;
    handle.map(|file| open_source_path(file.path())).transpose()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(BuildCancellationState::default())
        .invoke_handler(tauri::generate_handler![
            dispatch_workbench,
            run_build,
            cancel_build,
            pick_source
        ])
        .run(tauri::generate_context!())
        .expect("error while running ThesisForge desktop");
}
