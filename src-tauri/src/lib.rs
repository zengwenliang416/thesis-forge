use serde_json::Value;
use std::env;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

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

fn sidecar_command() -> (String, Vec<String>) {
    if let Ok(executable) = env::var("THESISFORGE_SIDECAR_EXECUTABLE") {
        return (executable, Vec::new());
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
            "--once".to_string(),
        ],
    )
}

pub fn dispatch_to_sidecar(request: &Value) -> Result<Value, String> {
    validate_request(request)?;
    let (program, args) = sidecar_command();
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

#[tauri::command]
async fn dispatch_workbench(request: Value) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || dispatch_to_sidecar(&request))
        .await
        .map_err(|error| format!("sidecar task failed: {error}"))?
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
        .invoke_handler(tauri::generate_handler![dispatch_workbench, pick_source])
        .run(tauri::generate_context!())
        .expect("error while running ThesisForge desktop");
}
