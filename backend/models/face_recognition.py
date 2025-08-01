import cv2
import numpy as np
import os
import json
from typing import Optional, Tuple, List
import base64
from PIL import Image
import io

class FaceRecognitionSystem:
    """Core face recognition system using OpenCV"""
    
    def __init__(self, tolerance: float = 0.6):
        self.tolerance = tolerance
        self.known_encodings = []
        self.known_employee_ids = []
        
        # Initialize OpenCV face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # Initialize face recognizer
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.is_trained = False
        
        print("✅ Face Recognition System initialized")
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in an image using OpenCV Haar Cascades"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return faces.tolist()
    
    def extract_face_features(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract face features using Local Binary Patterns"""
        x, y, w, h = face_location
        
        # Extract face region
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize face to standard size
        face_roi = cv2.resize(face_roi, (100, 100))
        
        # Enhance image quality
        face_roi = cv2.equalizeHist(face_roi)
        
        return face_roi
    
    def encode_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Create face encoding from image"""
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            return None
        
        # Use the largest face detected
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        
        # Extract features
        face_features = self.extract_face_features(image, largest_face)
        
        # Convert to feature vector (flatten the image)
        face_encoding = face_features.flatten()
        
        # Normalize the encoding
        face_encoding = face_encoding / np.linalg.norm(face_encoding)
        
        return face_encoding
    
    def compare_faces(self, known_encoding: np.ndarray, unknown_encoding: np.ndarray) -> float:
        """Compare two face encodings and return similarity score"""
        # Calculate Euclidean distance
        distance = np.linalg.norm(known_encoding - unknown_encoding)
        
        # Convert distance to similarity (0-1 scale, higher = more similar)
        similarity = 1 / (1 + distance)
        
        return similarity
    
    def load_known_faces(self, encodings: List[np.ndarray], employee_ids: List[str]):
        """Load known face encodings"""
        self.known_encodings = encodings
        self.known_employee_ids = employee_ids
        
        print(f"✅ Loaded {len(encodings)} known face encodings")
    
    def train_recognizer(self, faces: List[np.ndarray], labels: List[int]):
        """Train the face recognizer with face images and labels"""
        if len(faces) == 0:
            print("⚠️ No faces provided for training")
            return False
        
        try:
            self.face_recognizer.train(faces, np.array(labels))
            self.is_trained = True
            print(f"✅ Face recognizer trained with {len(faces)} face samples")
            return True
        except Exception as e:
            print(f"❌ Error training face recognizer: {e}")
            return False
    
    def recognize_face(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """Recognize face in image and return employee_id and confidence"""
        # Detect faces in image
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            return None, 0.0
        
        # Use the largest face
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        
        # Extract face encoding
        unknown_encoding = self.encode_face(image)
        
        if unknown_encoding is None:
            return None, 0.0
        
        # Compare with known faces
        best_match = None
        best_confidence = 0.0
        
        for i, known_encoding in enumerate(self.known_encodings):
            confidence = self.compare_faces(known_encoding, unknown_encoding)
            
            if confidence > best_confidence and confidence > self.tolerance:
                best_confidence = confidence
                best_match = self.known_employee_ids[i]
        
        return best_match, best_confidence
    
    def process_image_from_base64(self, base64_string: str) -> np.ndarray:
        """Convert base64 string to OpenCV image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_string)
            
            # Convert bytes to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return opencv_image
            
        except Exception as e:
            print(f"❌ Error processing base64 image: {e}")
            return None
    
    def process_image_from_file(self, file_path: str) -> np.ndarray:
        """Load image from file path"""
        try:
            image = cv2.imread(file_path)
            if image is None:
                print(f"❌ Could not load image from {file_path}")
                return None
            return image
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return None
    
    def validate_face_quality(self, image: np.ndarray) -> Tuple[bool, str]:
        """Validate if the face in image is of good quality for recognition"""
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            return False, "No face detected in image"
        
        if len(faces) > 1:
            return False, "Multiple faces detected. Please use image with single face"
        
        face = faces[0]
        x, y, w, h = face
        
        # Check face size (should be at least 100x100 pixels)
        if w < 100 or h < 100:
            return False, "Face is too small. Please use a clearer image"
        
        # Check if face is roughly square (not too elongated)
        aspect_ratio = w / h
        if aspect_ratio < 0.7 or aspect_ratio > 1.4:
            return False, "Face shape is unusual. Please face the camera directly"
        
        # Extract face region for eye detection
        face_roi = image[y:y+h, x:x+w]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Detect eyes to ensure face is frontal
        eyes = self.eye_cascade.detectMultiScale(gray_roi, 1.1, 3)
        
        if len(eyes) < 1:
            return False, "Could not detect eyes. Please face the camera directly"
        
        return True, "Face quality is good"
    
    def save_face_encoding(self, employee_id: str, encoding: np.ndarray, file_path: str = "face_encodings.json"):
        """Save face encoding to file"""
        try:
            # Load existing encodings
            encodings_data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    encodings_data = json.load(f)
            
            # Add new encoding
            encodings_data[employee_id] = encoding.tolist()
            
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(encodings_data, f, indent=2)
            
            print(f"✅ Face encoding saved for employee {employee_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving face encoding: {e}")
            return False
    
    def load_face_encodings(self, file_path: str = "face_encodings.json"):
        """Load face encodings from file"""
        try:
            if not os.path.exists(file_path):
                print("⚠️ No face encodings file found")
                return False
            
            with open(file_path, 'r') as f:
                encodings_data = json.load(f)
            
            encodings = []
            employee_ids = []
            
            for emp_id, encoding_list in encodings_data.items():
                encodings.append(np.array(encoding_list))
                employee_ids.append(emp_id)
            
            self.load_known_faces(encodings, employee_ids)
            return True
            
        except Exception as e:
            print(f"❌ Error loading face encodings: {e}")
            return False
    
    def get_face_preview(self, image: np.ndarray) -> np.ndarray:
        """Get image with face detection boxes drawn"""
        faces = self.detect_faces(image)
        preview_image = image.copy()
        
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(preview_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw text
            cv2.putText(preview_image, 'Face Detected', (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return preview_image
    
    def update_tolerance(self, new_tolerance: float):
        """Update recognition tolerance"""
        self.tolerance = max(0.0, min(1.0, new_tolerance))  # Keep between 0 and 1
        print(f"✅ Recognition tolerance updated to {self.tolerance}")

# Utility functions for the face recognition system
class FaceRecognitionUtils:
    """Utility functions for face recognition operations"""
    
    @staticmethod
    def resize_image(image: np.ndarray, max_width: int = 800, max_height: int = 600) -> np.ndarray:
        """Resize image while maintaining aspect ratio"""
        height, width = image.shape[:2]
        
        if width > max_width or height > max_height:
            # Calculate scaling factor
            scale_w = max_width / width
            scale_h = max_height / height
            scale = min(scale_w, scale_h)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized
        
        return image
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """Enhance image quality for better face recognition"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels and convert back to BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    @staticmethod
    def image_to_base64(image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{image_base64}"

# Test the face recognition system
if __name__ == "__main__":
    # Initialize face recognition system
    face_system = FaceRecognitionSystem()
    
    print("Face Recognition System is ready!")
    print(f"Recognition tolerance: {face_system.tolerance}")
    print("✅ File 4 (Face Recognition Core) completed successfully")