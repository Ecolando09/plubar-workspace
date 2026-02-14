# Add project specific ProGuard rules here.
-keepattributes Signature
-keepattributes *Annotation*

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# Gson
-keepattributes Signature
-keep class com.transcriber.video.MainActivity$TranscriptionResult { *; }
