package com.transcriber.video;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import com.google.gson.Gson;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

public class MainActivity extends AppCompatActivity {

    private static final String ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/speech-to-text";
    private static final MediaType MEDIA_TYPE_OGG = MediaType.parse("audio/ogg");
    private static final MediaType MEDIA_TYPE_VIDEO = MediaType.parse("video/*");

    private TextView selectedFileText;
    private TextView statusText;
    private TextView transcriptText;
    private Button selectButton;
    private Button transcribeButton;
    private Uri selectedVideoUri;

    private final ActivityResultLauncher<Intent> videoPickerLauncher = registerForActivityResult(
        new ActivityResultContracts.StartActivityForResult(),
        result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                selectedVideoUri = result.getData().getData();
                if (selectedVideoUri != null) {
                    String fileName = getFileName(selectedVideoUri);
                    selectedFileText.setText("Selected: " + fileName);
                    selectedFileText.setVisibility(View.VISIBLE);
                    transcribeButton.setEnabled(true);
                    statusText.setText("Ready to transcribe");
                    transcriptText.setText("");
                }
            }
        }
    );

    private final ActivityResultLauncher<Intent> saveFileLauncher = registerForActivityResult(
        new ActivityResultContracts.StartActivityForResult(),
        result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri saveUri = result.getData().getData();
                if (saveUri != null) {
                    saveTranscriptToFile(saveUri);
                }
            }
        }
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        selectedFileText = findViewById(R.id.selectedFileText);
        statusText = findViewById(R.id.statusText);
        transcriptText = findViewById(R.id.transcriptText);
        selectButton = findViewById(R.id.selectButton);
        transcribeButton = findViewById(R.id.transcribeButton);
        Button saveButton = findViewById(R.id.saveButton);

        transcribeButton.setEnabled(false);
        saveButton.setEnabled(false);

        selectButton.setOnClickListener(v -> openVideoPicker());
        transcribeButton.setOnClickListener(v -> transcribeVideo());
        saveButton.setOnClickListener(v -> saveTranscript());
    }

    private void openVideoPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("video/*");
        videoPickerLauncher.launch(intent);
    }

    private void transcribeVideo() {
        if (selectedVideoUri == null) {
            Toast.makeText(this, "Please select a video first", Toast.LENGTH_SHORT).show();
            return;
        }

        statusText.setText("Extracting audio...");
        transcriptText.setText("");
        transcribeButton.setEnabled(false);

        // Extract audio and transcribe in background thread
        new Thread(() -> {
            try {
                // Create temp directory
                File tempDir = new File(getCacheDir(), "temp");
                if (!tempDir.exists()) tempDir.mkdirs();

                // Copy video to temp file
                File videoFile = new File(tempDir, "video.ogg");
                copyUriToFile(selectedVideoUri, videoFile);

                // Run transcription on main thread
                runOnUiThread(() -> sendToElevenLabs(videoFile));

            } catch (Exception e) {
                runOnUiThread(() -> {
                    statusText.setText("Error: " + e.getMessage());
                    transcribeButton.setEnabled(true);
                });
            }
        }).start();
    }

    private void sendToElevenLabs(File audioFile) {
        OkHttpClient client = new OkHttpClient();

        RequestBody requestBody = new MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", audioFile.getName(),
                RequestBody.create(audioFile, MEDIA_TYPE_OGG))
            .addFormDataPart("model_id", "scribe_v2")
            .addFormDataPart("language_code", "en")
            .build();

        Request request = new Request.Builder()
            .url(ELEVENLABS_API_URL)
            .addHeader("xi-api-key", BuildConfig.ELEVENLABS_API_KEY)
            .post(requestBody)
            .build();

        statusText.setText("Transcribing...");

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    statusText.setText("Network error: " + e.getMessage());
                    transcribeButton.setEnabled(true);
                });
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                String responseBody = response.body() != null ? response.body().string() : "";

                if (response.isSuccessful()) {
                    Gson gson = new Gson();
                    TranscriptionResult result = gson.fromJson(responseBody, TranscriptionResult.class);
                    final String transcript = result.text;

                    runOnUiThread(() -> {
                        transcriptText.setText(transcript);
                        statusText.setText("✅ Transcription complete!");
                        transcribeButton.setEnabled(true);
                        findViewById(R.id.saveButton).setEnabled(true);
                    });
                } else {
                    runOnUiThread(() -> {
                        statusText.setText("Error: " + responseBody);
                        transcribeButton.setEnabled(true);
                    });
                }
            }
        });
    }

    private void saveTranscript() {
        String transcript = transcriptText.getText().toString();
        if (transcript.isEmpty()) {
            Toast.makeText(this, "No transcript to save", Toast.LENGTH_SHORT).show();
            return;
        }

        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TITLE, "transcription.txt");
        saveFileLauncher.launch(intent);
    }

    private void saveTranscriptToFile(Uri uri) {
        try {
            String transcript = transcriptText.getText().toString();
            try (InputStream is = getContentResolver().openInputStream(uri);
                 FileOutputStream fos = new FileOutputStream(getContentResolver().openFileDescriptor(uri, "w").getFileDescriptor())) {
                fos.write(transcript.getBytes());
            }
            Toast.makeText(this, "Saved!", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Save failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void copyUriToFile(Uri uri, File dest) throws IOException {
        try (InputStream is = getContentResolver().openInputStream(uri);
             FileOutputStream fos = new FileOutputStream(dest)) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = is.read(buffer)) != -1) {
                fos.write(buffer, 0, bytesRead);
            }
        }
    }

    private String getFileName(Uri uri) {
        String result = null;
        if (uri.getScheme().equals("content")) {
            try (android.database.Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
                if (cursor != null && cursor.moveToFirst()) {
                    int index = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
                    if (index >= 0) {
                        result = cursor.getString(index);
                    }
                }
            }
        }
        if (result == null) {
            result = uri.getPath();
            int cut = result.lastIndexOf('/');
            if (cut != -1) {
                result = result.substring(cut + 1);
            }
        }
        return result != null ? result : "video.ogg";
    }

    static class TranscriptionResult {
        String text;
        String language_code;
    }
}
