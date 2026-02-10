# Family Journal Upload System - DETAILED ARCHITECTURE

## Table of Contents
1. [Complete Backend Code Flow](#1-backend-code-flow-apppy)
2. [Complete Frontend Code Flow](#2-frontend-code-flow-indexhtml)
3. [Google Drive Integration](#3-google-drive-integration)
4. [Data Flow Diagrams with Line Numbers](#4-data-flow-diagrams)
5. [Debugging Commands](#5-debugging-commands)
6. [Known Bugs and Fixes](#6-known-bugs-and-fixes)

---

## 1. Backend Code Flow (app.py)

### A. Top-level Configuration (Lines 1-130)

```python
# Line 83: Threshold for local vs Google Drive storage
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB threshold

# Line 128: GLOBAL DICTIONARY tracking Drive upload progress
# Key: upload_id (UUID string)
# Value: {'progress': int (0-100), 'complete': bool, 'url': str, 'error': str}
drive_upload_status = {}
```
**CRITICAL:** This dict stores the state of in-progress Google Drive uploads.
When a large file is uploaded, the server starts a background thread to upload
to Drive. This dict is updated by that thread so other endpoints can poll it.

### B. POST /upload-progress Endpoint (Lines 146-245)

```python
@app.route('/upload-progress', methods=['POST'])
def upload_progress():
    """
    Main upload endpoint. 
    - Files <25MB: Save locally, return short code
    - Files >=25MB: Upload to Google Drive, track progress
    """
```

**Lines 149-155: Extract file from request**
```python
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename) or 'unnamed'
    file_id = str(uuid.uuid4())
    upload_id = str(uuid.uuid4())  # Unique ID for tracking
```

**Lines 158-165: Generate unique filename**
```python
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = filename.replace(' ', '_')
    local_filename = f"{timestamp}_{safe_name}"
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], local_filename)
```

**Lines 167-171: Save file to disk**
```python
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(local_path)
    file_size = os.path.getsize(local_path)
```

**Lines 173-178: Check if small or large file**
```python
    if file_size < MAX_ATTACHMENT_SIZE:
        # === SMALL FILE PATH ===
        short_code = short_code_generator.generate()
        save_short_code(short_code, local_filename)
        
        return jsonify({
            'status': 'uploaded',
            'drive': False,
            'code': short_code,
            'filename': filename,
            'size': file_size
        })
```

**Lines 183-207: LARGE FILE PATH - Google Drive Upload**
```python
    else:
        # === LARGE FILE PATH ===
        # Initialize tracking BEFORE starting upload
        drive_upload_status[upload_id] = {
            'progress': 0,
            'complete': False,
            'error': None
        }
        
        # Start background thread for Drive upload
        thread = threading.Thread(
            target=upload_to_drive_thread,
            args=(local_path, filename, upload_id, app.config['UPLOAD_FOLDER'])
        )
        thread.start()
        
        # Return immediately so browser knows upload started
        return jsonify({
            'status': 'uploaded',
            'drive': True,
            'upload_id': upload_id,
            'url': None,  # Will be filled by thread
            'filename': filename,
            'size': file_size
        })
```

**Key insight:** The response returns BEFORE the Drive upload completes!
The browser must poll `/upload-status/<upload_id>` to know when it's done.

### C. upload_to_drive_thread() Function (Lines 247-290)

This runs in a BACKGROUND THREAD:

```python
def upload_to_drive_thread(local_path, filename, upload_id, upload_folder):
    """
    Background thread that:
    1. Uploads file to Google Drive
    2. Updates drive_upload_status[upload_id] as it progresses
    3. Cleans up temp file when done
    """
    try:
        # === PHASE 1: Start upload ===
        drive_upload_status[upload_id]['progress'] = 10
        
        # Call the actual uploader
        result = google_drive_upload(
            local_path=local_path,
            filename=filename,
            timeout_seconds=600
        )
        
        # === PHASE 2: Upload complete ===
        drive_upload_status[upload_id]['progress'] = 90
        drive_upload_status[upload_id]['url'] = result['shareLink']
        drive_upload_status[upload_id]['complete'] = True
        drive_upload_status[upload_id]['progress'] = 100
        
    except Exception as e:
        drive_upload_status[upload_id]['error'] = str(e)
        drive_upload_status[upload_id]['complete'] = True
    finally:
        # === CLEANUP ===
        try:
            os.remove(local_path)  # Delete temp file
        except:
            pass
```

### D. GET /upload-status/<upload_id> Endpoint (Lines 132-141)

```python
@app.route('/upload-status/<upload_id>')
def upload_status(upload_id):
    """
    REST polling endpoint for Drive upload progress.
    Frontend calls this every second to check status.
    
    Returns:
        {
            "progress": 100,
            "complete": true,
            "url": "https://drive.google.com/..."
        }
    """
    if upload_id in drive_upload_status:
        return jsonify(drive_upload_status[upload_id])
    return jsonify({'status': 'unknown'}), 404
```

### E. GET /upload-progress-stream/<upload_id> Endpoint (Lines 89-126)

```python
@app.route('/upload-progress-stream/<upload_id>')
def upload_progress_stream(upload_id):
    """
    Server-Sent Events (SSE) endpoint.
    Keeps connection open and pushes progress updates as they happen.
    
    Format:
        data: {"progress": 50, "status": "uploading"}
        data: {"progress": 100, "status": "complete", "url": "..."}
    """
    def generate():
        yield 'data: {"status": "connecting"}\n\n'
        
        last_progress = -1
        check_count = 0
        
        while check_count < 300:  # Max 30 seconds of streaming
            if upload_id in drive_upload_status:
                p = drive_upload_status[upload_id]
                progress = p.get('progress', 0)
                
                # Only yield if progress changed
                if progress > last_progress:
                    last_progress = progress
                    msg = json.dumps({'progress': progress, 'status': 'uploading'})
                    yield f'data: {msg}\n\n'
                
                # Check if complete
                if p.get('complete'):
                    msg = json.dumps({
                        'progress': 100, 
                        'status': 'complete', 
                        'url': p.get('url', '')
                    })
                    yield f'data: {msg}\n\n'
                    
                    # Cleanup
                    del drive_upload_status[upload_id]
                    break
                
                # Check for error
                if p.get('error'):
                    msg = json.dumps({'status': 'error', 'message': p.get('error')})
                    yield f'data: {msg}\n\n'
                    del drive_upload_status[upload_id]
                    break
            
            time.sleep(0.1)  # Wait 100ms between checks
            check_count += 1
        
        yield 'data: {"status": "timeout"}\n\n'
    
    return Response(stream_with_context(generate()), 
                    mimetype='text/event-stream')
```

---

## 2. Frontend Code Flow (templates/index.html)

### A. Main Entry Point (Lines ~580-620)

```javascript
async function handleFileSelect(event) {
    const files = event.target.files;
    const progressDiv = document.getElementById('uploadProgress');
    
    // Show progress bar
    progressDiv.style.display = 'block';
    progressDiv.innerHTML = `
        <div class="name">📤 <strong>Uploading ${files.length} file(s)</strong></div>
        <div class="bar"><div class="fill" id="progressFill" style="width: 0%"></div></div>
        <div class="status" id="progressStatus">Initializing...</div>
    `;
    
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = '⏳ Uploading...';
    
    let successCount = 0;
    let failCount = 0;
```

### B. File Upload Loop (Lines ~625-690)

```javascript
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Update status to show which file
        if (progressStatus) {
            progressStatus.innerHTML = `[${i+1}/${files.length}] <strong>${file.name}</strong><br>${formatSize(file.size)} - Connecting...`;
        }
        
        try {
            // === CALL UPLOAD FUNCTION ===
            const result = await uploadFile(file);
            
            // === CHECK RESULT ===
            if (result.status === 'uploaded') {
                
                if (result.drive && result.upload_id) {
                    // === LARGE FILE PATH ===
                    // Server upload done, but Drive upload still in progress
                    
                    if (progressStatus) {
                        progressStatus.innerHTML = 
                            `☁️ <strong>${file.name}</strong><br>📡 Uploaded to server, uploading to Google Drive...`;
                    }
                    
                    // === POLL FOR DRIVE COMPLETION ===
                    await trackDriveProgress(
                        result.upload_id,
                        progressStatus,
                        progressFill,
                        file.name,
                        file.size
                    );
                    
                    // Add to list AFTER Drive upload done
                    uploadedFiles.push({
                        name: result.filename,
                        url: result.url || null,
                        code: result.code || null,
                        size: result.size,
                        drive: result.drive
                    });
                    successCount++;
                    
                    if (progressStatus) {
                        progressStatus.innerHTML = 
                            `☁️ <strong>${file.name}</strong><br>✅ Uploaded to Google Drive!`;
                    }
                    
                } else {
                    // === SMALL FILE PATH ===
                    // Already done, no Drive upload needed
                    uploadedFiles.push({
                        name: result.filename,
                        url: result.url || null,
                        code: result.code || null,
                        size: result.size,
                        drive: result.drive
                    });
                    successCount++;
                    
                    if (progressStatus) {
                        progressStatus.innerHTML = 
                            `✅ <strong>${file.name}</strong><br>✅ Uploaded!`;
                    }
                }
                
                if (progressFill) {
                    progressFill.style.width = '100%';
                }
                
                saveUploads();
                updateUploadedList();
                
            } else {
                // === UPLOAD FAILED ===
                failCount++;
                if (progressStatus) {
                    progressStatus.innerHTML = 
                        `❌ <strong>${file.name}</strong>: ${result.error || 'Upload failed'}`;
                }
            }
            
        } catch (err) {
            // === NETWORK/EXCEPTION ERROR ===
            failCount++;
            if (progressStatus) {
                progressStatus.innerHTML = 
                    `❌ <strong>${file.name}</strong>: ${err.message}`;
            }
        }
    }
```

### C. uploadFile() - XHR Upload Function (Lines ~710-755)

```javascript
async function uploadFile(file) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);
        
        // === PROGRESS HANDLER ===
        // Updates during the HTTP POST to the server
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const progressFill = document.getElementById('progressFill');
                const progressStatus = document.getElementById('progressStatus');
                
                if (progressFill) {
                    progressFill.style.width = percent + '%';
                }
                
                if (progressStatus) {
                    progressStatus.innerHTML = 
                        `<strong>📹 ${file.name}</strong><br>🔄 ${formatSize(e.loaded)} / ${formatSize(e.total)} (${percent}%)`;
                }
            }
        });
        
        // === LOAD (SUCCESS) HANDLER ===
        xhr.addEventListener('load', function() {
            try {
                const result = JSON.parse(xhr.responseText);
                resolve(result);
            } catch (e) {
                reject(new Error('Parse error - invalid JSON response'));
            }
        });
        
        // === ERROR HANDLER ===
        xhr.addEventListener('error', function() {
            reject(new Error('Network error - upload failed'));
        });
        
        // === TIMEOUT HANDLER ===
        xhr.timeout = 600000;  // 10 minutes
        xhr.addEventListener('timeout', function() {
            reject(new Error('Upload timed out'));
        });
        
        // === SEND REQUEST ===
        xhr.open('POST', '/upload-progress');
        xhr.send(formData);
    });
}
```

### D. trackDriveProgress() - Drive Upload Polling (Lines ~716-795)

```javascript
async function trackDriveProgress(uploadId, progressStatus, progressFill, filename, totalSize) {
    const maxWait = 600000;     // 10 minutes max
    const pollInterval = 1000;  // Poll every 1 second
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWait) {
        // === TRY SSE STREAM FIRST ===
        try {
            const response = await fetch('/upload-progress-stream/' + uploadId);
            if (response.ok) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                // Read SSE stream
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value);
                    const lines = buffer.split('\n');
                    buffer = lines.pop();  // Keep incomplete line in buffer
                    
                    // Process each SSE message
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.progress !== undefined && progressFill) {
                                    progressFill.style.width = data.progress + '%';
                                }
                                
                                if (data.status === 'complete' && progressStatus) {
                                    progressStatus.innerHTML = 
                                        `☁️ <strong>${filename}</strong><br>✅ Ready!`;
                                    return;  // DONE!
                                }
                                
                                if (data.status === 'error' && progressStatus) {
                                    progressStatus.innerHTML = 
                                        `☁️ <strong>${filename}</strong><br>⚠️ ${data.message || 'Upload failed'}`;
                                    return;
                                }
                                
                            } catch (e) {
                                // Ignore parse errors
                            }
                        }
                    }
                }
            }
        } catch (e) {
            // SSE failed, fall back to polling
        }
        
        // === FALLBACK: POLL REST ENDPOINT ===
        try {
            const response = await fetch('/upload-status/' + uploadId);
            if (response.ok) {
                const data = await response.json();
                
                if (data.progress !== undefined && progressFill) {
                    progressFill.style.width = data.progress + '%';
                }
                
                if (data.complete && progressStatus) {
                    progressStatus.innerHTML = 
                        `☁️ <strong>${filename}</strong><br>✅ Ready!`;
                    return;  // DONE!
                }
            }
        } catch (e2) {
            // Polling failed too
        }
        
        // Wait before next poll
        await new Promise(r => setTimeout(r, pollInterval));
    }
    
    // === TIMEOUT ===
    if (progressStatus) {
        progressStatus.innerHTML = 
            `☁️ <strong>${filename}</strong><br>⏰ Taking longer than expected...`;
    }
}
```

### E. Final Success/Failure Display (Lines ~691-710)

```javascript
    document.getElementById('submitBtn').disabled = false;
    
    if (failCount === 0) {
        document.getElementById('submitBtn').textContent = '✅ Ready to Send!';
        if (progressStatus) {
            const filesList = uploadedFiles.map(function(f) { 
                return f.name; 
            }).join(', ');
            progressStatus.innerHTML = 
                `<strong>🎉 All ${successCount} file(s) uploaded!</strong><br><small>${filesList}</small>`;
        }
    } else {
        document.getElementById('submitBtn').textContent = '⚠️ Retry Upload';
        if (progressStatus) {
            progressStatus.innerHTML = 
                `<strong>⚠️ ${successCount} succeeded, ${failCount} failed</strong><br>Remove failed files and try again.`;
        }
    }
    
    event.target.value = '';
```

---

## 3. Google Drive Integration

### File: google_drive/uploader.py

```python
def google_drive_upload(local_path, filename, timeout_seconds=600):
    """
    Uploads a file to Google Drive using the Drive API v3.
    
    Steps:
    1. Load credentials from token.json
    2. Refresh token if expired
    3. Create resumable upload session
    4. Upload file content
    5. Set permissions (anyone with link can view)
    6. Return shareable URL
    """
    # === STEP 1: Load credentials ===
    creds = None
    token_path = '/root/.openclaw/workspace/family-journal/google_dournal/google_drive/token.json'
    
    if os.path.exists(token_path):
        with open(token_path, 'r') as token:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # === STEP 2: Refresh if needed ===
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Uses refresh_token, client_id, client_secret
    
    # === STEP 3: Build Drive service ===
    service = build('drive', 'v3', credentials=creds)
    
    # === STEP 4: Create file metadata ===
    file_metadata = {
        'name': filename,
        'mimeType': get_mime_type(filename)
    }
    
    # === STEP 5: Start resumable upload ===
    media = MediaFileUpload(local_path, resumable=True)
    
    # This returns immediately with a session URI
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        uploadType='resumable'  # Key parameter!
    ).execute()
    
    # === STEP 6: Make it shareable ===
    service.permissions().create(
        fileId=file['id'],
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    
    # === STEP 7: Return shareable link ===
    share_link = f"https://drive.google.com/file/d/{file['id']}/view?usp=drivesdk"
    return {'shareLink': share_link}
```

### OAuth Token Structure (token.json)
```json
{
    "token": "ya29.a0AfH6...",
    "refresh_token": "1//0g...",  // For getting new access tokens
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "123456789.apps.googleusercontent.com",
    "client_secret": "GOCSPX-...",
    "scopes": ["https://www.googleapis.com/auth/drive.file"]
}
```

---

## 4. Data Flow Diagrams

### Small File Upload (<25MB)

```
USER                BROWSER              FLASK SERVER              LOCAL DISK
  |                    |                     |                        |
  |-- Select file --->|                     |                        |
  |                   |                     |                        |
  |                   |-- POST /upload-progress -->                 |
  |                   |   (multipart/form-data)                     |
  |                   |                     |                        |
  |                   |                     |-- Save file ----------->|
  |                   |                     |   uploads/xxx.mp4      |
  |                   |                     |                        |
  |                   |                     |-- Generate code ------->|
  |                   |                     |   code: "ABC123"        |
  |                   |                     |                        |
  |                   |   {"status":"uploaded",        |              |
  |<------------------|   "drive":false,              |              |
  |                   |   "code":"ABC123"}            |              |
  |                   |                     |                        |
  |-- "✅ Ready to Send!"                  |                        |
```

### Large File Upload (>=25MB)

```
USER                BROWSER              FLASK SERVER              GOOGLE DRIVE
  |                    |                     |                        |
  |-- Select file --->|                     |                        |
  |                   |                     |                        |
  |                   |-- POST /upload-progress -->                 |
  |                   |   (multipart/form-data)                     |
  |                   |                     |                        |
  |                   |                     |-- Save temp ----------->|
  |                   |                     |   uploads/xxx.mp4      |
  |                   |                     |                        |
  |                   |                     |-- Start thread -------->|-- Upload
  |                   |                     |   drive_upload_status =|    file
  |                   |                     |   {progress: 0}       |      |
  |                   |                     |                        |<-----|
  |                   |   {"status":"uploaded",    |                |      |
  |                   |   "drive":true,           |                |      |
  |                   |   "upload_id":"UUID"}      |                |      |
  |<------------------|                     |                        |      |
  |                   |                     |                        |      |
  |                   |-- GET /upload-status/U -->|                |      |
  |                   |                     |<--{progress:10}-------|      |
  |                   |   (progress: 10%)  |                        |      |
  |                   |                     |                        |<-----|
  |                   |                     |<--{progress:90}-------|      |
  |                   |   (progress: 90%)  |                        |      |
  |                   |                     |                        |<-----|
  |                   |                     |<--{complete:true,------|      |
  |                   |                     |   url:"https://..."}    |      |
  |                   |                     |                        |      |
  |                   |   {"complete":true} |                        |      |
  |<------------------|                     |                        |      |
  |                   |                     |                        |      |
  |-- "✅ Ready to Send!"                  |                        |      |
```

---

## 5. Debugging Commands

### Check if server is running:
```bash
curl http://127.0.0.1:5001
# Should return HTML page
```

### Test small file upload:
```bash
dd if=/dev/zero of=/tmp/test_10mb.mp4 bs=1M count=10
curl -X POST -F "file=@/tmp/test_10mb.mp4" http://127.0.0.1:5001/upload-progress
```

### Test large file upload:
```bash
dd if=/dev/zero of=/tmp/test_50mb.mp4 bs=1M count=50
curl -X POST -F "file=@/tmp/test_50mb.mp4" http://127.0.0.1:5001/upload-progress -m 180
```

### Check Drive upload status:
```bash
# After large file upload, get the upload_id from response
curl http://127.0.0.1:5001/upload-status/<upload_id>
```

### Stream progress (SSE):
```bash
curl -H "Accept: text/event-stream" http://127.0.0.1:5001/upload-progress-stream/<upload_id>
```

### Check server logs:
```bash
tail -100 /tmp/journal.log
```

### Restart server:
```bash
fuser -k 5001/tcp
cd /root/.openclaw/workspace/family-journal && python3 app.py &
```

---

## 6. Known Bugs and Fixes

### Bug #1: Variable Shadowing
**Symptom:** `TypeError: argument of type 'function' is not iterable`  
**Cause:** Python variable `upload_status` was shadowed by function `upload_status()`  
**Fix:** Rename dict to `drive_upload_status` everywhere

### Bug #2: Progress Updates Not Reaching SSE
**Symptom:** SSE stream shows "connecting" then timeout, never shows progress  
**Cause:** Progress updates written to `upload_progress` dict, but SSE reads from `drive_upload_status`  
**Fix:** Update BOTH dicts when progress changes

### Bug #3: Browser Caching Old JavaScript
**Symptom:** Upload button says "Retry Upload" even after fixes  
**Cause:** Browser caches old HTML/JS  
**Fix:** Hard refresh (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on Mac)

### Bug #4: 220MB File Stalls
**Symptom:** Progress bar gets stuck, eventually shows "Retry Upload"  
**Cause:** Frontend waits for Drive upload completion but has no progress visibility  
**Fix:** Implemented `trackDriveProgress()` function with polling

### Bug #5: Missing Upload Folder
**Symptom:** `[Errno 2] No such file or directory: '/uploads/...'`  
**Cause:** Folder doesn't exist or wrong path  
**Fix:** `os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)`
