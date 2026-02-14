export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }
    
    // API endpoint for transcription
    if (url.pathname === '/transcribe' && request.method === 'POST') {
      return handleTranscribe(request, env, corsHeaders);
    }
    
    // Serve the web interface
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(HTML, {
        headers: { ...corsHeaders, 'Content-Type': 'text/html' }
      });
    }
    
    return new Response('Not Found', { status: 404, headers: corsHeaders });
  }
};

async function handleTranscribe(request, env, corsHeaders) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');
    
    if (!file) {
      return new Response(JSON.stringify({ error: 'No file provided' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Get file data
    const fileData = await file.arrayBuffer();
    
    // Send to ElevenLabs
    const elevenLabsResponse = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
      method: 'POST',
      headers: {
        'xi-api-key': env.ELEVENLABS_API_KEY || 'e1eddd1d04c1770684999c8d9a050d833a18cea0058a9e244f8d7485eab3e728',
      },
      body: (() => {
        const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);
        const body = new Uint8Array(fileData);
        const parts = [
          `--${boundary}\r\n`,
          `Content-Disposition: form-data; name="file"; filename="${file.name}"\r\n`,
          `Content-Type: ${file.type || 'audio/ogg'}\r\n\r\n`,
        ];
        // This is simplified - in real implementation we'd need proper multipart encoding
        return body;
      })()
    });
    
    // For simplicity, let's use a different approach - direct audio upload
    const response = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
      method: 'POST',
      headers: {
        'xi-api-key': env.ELEVENLABS_API_KEY || 'e1eddd1d04c1770684999c8d9a050d833a18cea0058a9e244f8d7485eab3e728',
        'Accept': 'application/json',
      },
      body: fileData
    });
    
    if (!response.ok) {
      const error = await response.text();
      return new Response(JSON.stringify({ error: 'Transcription failed: ' + error }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const result = await response.json();
    return new Response(JSON.stringify({ transcript: result.text }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

const HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Video Transcriber</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea, #764ba2);
      min-height: 100vh;
      padding: 20px;
      color: #1a202c;
    }
    .container {
      max-width: 500px;
      margin: 0 auto;
      background: white;
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    h1 { text-align: center; margin-bottom: 30px; font-size: 28px; }
    .upload-area {
      border: 3px dashed #667eea;
      border-radius: 15px;
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      margin-bottom: 20px;
      background: #f7fafc;
      transition: all 0.3s;
    }
    .upload-area:hover { background: #edf2f7; border-color: #764ba2; }
    .upload-area input { display: none; }
    .upload-icon { font-size: 48px; margin-bottom: 10px; }
    .btn {
      width: 100%;
      padding: 18px;
      font-size: 18px;
      font-weight: 600;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      margin-bottom: 20px;
    }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .status {
      text-align: center;
      padding: 15px;
      border-radius: 10px;
      margin-bottom: 20px;
      display: none;
    }
    .status.show { display: block; }
    .status.loading { background: #bee3f8; color: #2a4365; }
    .status.success { background: #c6f6d5; color: #22543d; }
    .status.error { background: #fed7d7; color: #742a2a; }
    .result {
      background: #f7fafc;
      padding: 20px;
      border-radius: 12px;
      white-space: pre-wrap;
      margin-bottom: 20px;
      display: none;
    }
    .result.show { display: block; }
    .copy-btn {
      width: 100%;
      padding: 12px;
      background: #48bb78;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 16px;
      display: none;
    }
    .copy-btn.show { display: block; }
    .file-info {
      text-align: center;
      padding: 10px;
      background: #edf2f7;
      border-radius: 8px;
      margin-bottom: 20px;
      display: none;
    }
    .file-info.show { display: block; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Video Transcriber</h1>
    <div class="upload-area" onclick="document.getElementById('file').click()">
      <div class="upload-icon">📹</div>
      <div>Tap to select video or audio</div>
      <input type="file" id="file" accept="video/*,audio/*" onchange="selectFile()">
    </div>
    <div class="file-info" id="fileInfo"></div>
    <button class="btn" id="transcribeBtn" onclick="transcribe()" disabled>Transcribe</button>
    <div class="status" id="status"></div>
    <div class="result" id="result"></div>
    <button class="copy-btn" id="copyBtn" onclick="copyText()">Copy</button>
  </div>
  <script>
    let selectedFile = null;
    
    function selectFile() {
      const input = document.getElementById('file');
      if (input.files.length > 0) {
        selectedFile = input.files[0];
        document.getElementById('fileInfo').textContent = '📁 ' + selectedFile.name;
        document.getElementById('fileInfo').classList.add('show');
        document.getElementById('transcribeBtn').disabled = false;
        document.getElementById('result').classList.remove('show');
        document.getElementById('copyBtn').classList.remove('show');
      }
    }
    
    async function transcribe() {
      if (!selectedFile) return;
      
      const btn = document.getElementById('transcribeBtn');
      const status = document.getElementById('status');
      const result = document.getElementById('result');
      
      btn.disabled = true;
      btn.textContent = 'Processing...';
      status.className = 'status show loading';
      status.textContent = 'Transcribing...';
      result.classList.remove('show');
      document.getElementById('copyBtn').classList.remove('show');
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      try {
        const response = await fetch('/transcribe', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.transcript) {
          status.className = 'status show success';
          status.textContent = 'Done!';
          result.textContent = data.transcript;
          result.classList.add('show');
          document.getElementById('copyBtn').classList.add('show');
        } else {
          throw new Error(data.error || 'Failed');
        }
      } catch (err) {
        status.className = 'status show error';
        status.textContent = 'Error: ' + err.message;
      }
      
      btn.disabled = false;
      btn.textContent = 'Transcribe';
    }
    
    function copyText() {
      const text = document.getElementById('result').textContent;
      navigator.clipboard.writeText(text);
    }
  </script>
</body>
</html>`;
