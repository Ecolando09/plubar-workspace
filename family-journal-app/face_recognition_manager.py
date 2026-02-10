import face_recognition
import os
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class FaceRecognitionManager:
    def __init__(self, profiles_dir="static/uploads/profiles"):
        self.profiles_dir = profiles_dir
        self.profiles_file = "face_profiles.pkl"
        self.profiles = {}  # kid_name -> {name, encoding, email}
        
        # Create profiles directory
        os.makedirs(profiles_dir, exist_ok=True)
        
        # Load existing profiles
        self.load_profiles()
    
    def load_profiles(self):
        """Load kid profiles from pickle file."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'rb') as f:
                    self.profiles = pickle.load(f)
                print(f"Loaded {len(self.profiles)} kid profiles")
            except Exception as e:
                print(f"Error loading profiles: {e}")
                self.profiles = {}
    
    def save_profiles(self):
        """Save kid profiles to pickle file."""
        with open(self.profiles_file, 'wb') as f:
            pickle.dump(self.profiles, f)
    
    def add_kid_profile(self, name: str, photo_path: str, email: str = "") -> Tuple[bool, str]:
        """
        Add a new kid profile with a reference photo.
        
        Args:
            name: Kid's name
            photo_path: Path to reference photo
            email: Kid's email address (optional)
        
        Returns:
            (success, message)
        """
        if not os.path.exists(photo_path):
            return False, f"Photo not found: {photo_path}"
        
        # Load and encode face
        image = face_recognition.load_image_file(photo_path)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) == 0:
            return False, f"No face detected in photo: {photo_path}"
        
        if len(encodings) > 1:
            return False, f"Multiple faces detected in photo: {photo_path}"
        
        # Save profile photo to profiles directory
        profile_photo_path = os.path.join(self.profiles_dir, f"{name.lower().replace(' ', '_')}.jpg")
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        from PIL import Image
        img = Image.open(photo_path)
        img.save(profile_photo_path, 'JPEG')
        
        # Store profile
        self.profiles[name.lower()] = {
            'name': name,
            'encoding': encodings[0],
            'email': email,
            'photo_path': profile_photo_path
        }
        self.save_profiles()
        
        return True, f"Profile added for {name}"
    
    def remove_kid_profile(self, name: str) -> Tuple[bool, str]:
        """Remove a kid profile."""
        name_lower = name.lower()
        if name_lower in self.profiles:
            # Remove photo file
            photo_path = self.profiles[name_lower].get('photo_path')
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
            
            del self.profiles[name_lower]
            self.save_profiles()
            return True, f"Profile removed for {name}"
        return False, f"Profile not found for {name}"
    
    def get_kids_list(self) -> List[Dict]:
        """Get list of all kids with their info."""
        return [
            {'name': p['name'], 'email': p.get('email', ''), 'has_photo': os.path.exists(p.get('photo_path', ''))}
            for p in self.profiles.values()
        ]
    
    def detect_faces_in_image(self, image_path: str) -> Dict:
        """
        Detect faces in an image and identify which kids are present.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dict with 'detected' (list of names) and 'unknown' (count)
        """
        if not os.path.exists(image_path):
            return {'detected': [], 'unknown': 0, 'error': 'Image not found'}
        
        try:
            image = face_recognition.load_image_file(image_path)
            unknown_encodings = face_recognition.face_encodings(image)
            
            detected_kids = []
            unknown_count = 0
            
            for unknown_encoding in unknown_encodings:
                matched = False
                for name, profile in self.profiles.items():
                    match = face_recognition.compare_faces([profile['encoding']], unknown_encoding)
                    if match[0]:
                        detected_kids.append(profile['name'])
                        matched = True
                        break
                
                if not matched:
                    unknown_count += 1
            
            return {
                'detected': detected_kids,
                'unknown': unknown_count,
                'total_faces': len(unknown_encodings)
            }
        except Exception as e:
            return {'detected': [], 'unknown': 0, 'error': str(e)}
    
    def detect_faces_in_video_frame(self, video_path: str, sample_interval: int = 30) -> Dict:
        """
        Sample frames from video and detect faces across them.
        
        Args:
            video_path: Path to video file
            sample_interval: Check every Nth frame
        
        Returns:
            Dict with 'detected' (list of names) and 'unknown' (count)
        """
        import cv2
        
        if not os.path.exists(video_path):
            return {'detected': [], 'unknown': 0, 'error': 'Video not found'}
        
        try:
            video = cv2.VideoCapture(video_path)
            frame_count = 0
            all_detected = set()
            all_unknown = 0
            
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                if frame_count % sample_interval == 0:
                    # Convert BGR to RGB
                    rgb_frame = frame[:, :, ::-1]
                    encodings = face_recognition.face_encodings(rgb_frame)
                    
                    for encoding in encodings:
                        matched = False
                        for name, profile in self.profiles.items():
                            if face_recognition.compare_faces([profile['encoding']], encoding)[0]:
                                all_detected.add(profile['name'])
                                matched = True
                                break
                        if not matched:
                            all_unknown += 1
                
                frame_count += 1
            
            video.release()
            
            return {
                'detected': list(all_detected),
                'unknown': all_unknown,
                'total_faces': len(all_detected) + all_unknown
            }
        except Exception as e:
            return {'detected': [], 'unknown': 0, 'error': str(e)}
    
    def update_kid_email(self, name: str, email: str) -> Tuple[bool, str]:
        """Update a kid's email address."""
        name_lower = name.lower()
        if name_lower in self.profiles:
            self.profiles[name_lower]['email'] = email
            self.save_profiles()
            return True, f"Email updated for {name}"
        return False, f"Profile not found for {name}"
