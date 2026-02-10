import os
import uuid
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import json

class MediaStorage:
    def __init__(self, base_dir="static/uploads"):
        self.base_dir = base_dir
        self.audio_dir = os.path.join(base_dir, "audio")
        self.photos_dir = os.path.join(base_dir, "photos")
        self.videos_dir = os.path.join(base_dir, "videos")
        
        # Create directories
        for d in [self.audio_dir, self.photos_dir, self.videos_dir]:
            os.makedirs(d, exist_ok=True)
        
        # Allowed extensions
        self.allowed_audio = {'mp3', 'wav', 'm4a', 'ogg', 'flac'}
        self.allowed_photos = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        self.allowed_videos = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
    
    def _generate_filename(self, original_name):
        """Generate a unique filename."""
        ext = Path(original_name).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}{ext}"
    
    def save_audio(self, file_obj, original_name):
        """Save an audio file and return the path."""
        if not self._allowed_file(original_name, self.allowed_audio):
            raise ValueError(f"Invalid audio file type: {original_name}")
        
        filename = self._generate_filename(original_name)
        filepath = os.path.join(self.audio_dir, filename)
        file_obj.save(filepath)
        return filepath
    
    def save_photo(self, file_obj, original_name):
        """Save a photo file and return the path."""
        if not self._allowed_file(original_name, self.allowed_photos):
            raise ValueError(f"Invalid photo file type: {original_name}")
        
        filename = self._generate_filename(original_name)
        filepath = os.path.join(self.photos_dir, filename)
        file_obj.save(filepath)
        return filepath
    
    def save_video(self, file_obj, original_name):
        """Save a video file and return the path."""
        if not self._allowed_file(original_name, self.allowed_videos):
            raise ValueError(f"Invalid video file type: {original_name}")
        
        filename = self._generate_filename(original_name)
        filepath = os.path.join(self.videos_dir, filename)
        file_obj.save(filepath)
        return filepath
    
    def _allowed_file(self, filename, allowed_set):
        """Check if file extension is allowed."""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in allowed_set
    
    def list_files(self, category):
        """List all files in a category."""
        dir_map = {
            'audio': self.audio_dir,
            'photos': self.photos_dir,
            'videos': self.videos_dir
        }
        
        if category not in dir_map:
            return []
        
        dir_path = dir_map[category]
        if not os.path.exists(dir_path):
            return []
        
        files = []
        for f in os.listdir(dir_path):
            filepath = os.path.join(dir_path, f)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    'name': f,
                    'path': filepath,
                    'url': f'/static/uploads/{category}/{f}',
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return files
    
    def delete_file(self, category, filename):
        """Delete a file."""
        dir_map = {
            'audio': self.audio_dir,
            'photos': self.photos_dir,
            'videos': self.videos_dir
        }
        
        if category not in dir_map:
            return False
        
        filepath = os.path.join(dir_map[category], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
