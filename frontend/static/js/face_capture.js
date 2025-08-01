// frontend/static/js/face_capture.js

class FaceCapture {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.captureBtn = document.getElementById('captureBtn');
        this.startCameraBtn = document.getElementById('startCamera');
        this.retryBtn = document.getElementById('retryBtn');
        this.result = document.getElementById('result');
        this.loadingSection = document.getElementById('loadingSection');
        this.cameraStatus = document.getElementById('cameraStatus');
        
        this.stream = null;
        this.isProcessing = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        if (this.startCameraBtn) {
            this.startCameraBtn.addEventListener('click', () => this.startCamera());
        }
        
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.captureAndRecognize());
        }
        
        if (this.retryBtn) {
            this.retryBtn.addEventListener('click', () => this.resetCapture());
        }
        
        // Handle page unload to stop camera
        window.addEventListener('beforeunload', () => this.stopCamera());
    }
    
    async startCamera() {
        try {
            this.updateCameraStatus('Starting camera...', 'warning');
            
            const constraints = {
                video: {
                    width: { ideal: 640, min: 320, max: 1280 },
                    height: { ideal: 480, min: 240, max: 720 },
                    facingMode: 'user',
                    frameRate: { ideal: 30, min: 15 }
                },
                audio: false
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            // Wait for video to be ready
            this.video.onloadedmetadata = () => {
                this.video.play();
                this.updateCameraStatus('Camera ready', 'success');
                this.startCameraBtn.style.display = 'none';
                this.captureBtn.style.display = 'inline-block';
                
                // Start face detection preview
                this.startFaceDetectionPreview();
            };
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            let errorMessage = 'Error accessing camera: ';
            
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Camera permission denied. Please allow camera access and try again.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No camera found. Please connect a camera and try again.';
            } else if (error.name === 'NotReadableError') {
                errorMessage += 'Camera is already in use by another application.';
            } else {
                errorMessage += error.message;
            }
            
            this.showResult(errorMessage, 'danger');
            this.updateCameraStatus('Camera error', 'danger');
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    captureImage() {
        if (!this.video.videoWidth || !this.video.videoHeight) {
            throw new Error('Video not ready');
        }
        
        const context = this.canvas.getContext('2d');
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // Draw video frame to canvas
        context.drawImage(this.video, 0, 0);
        
        // Convert to base64 with good quality
        return this.canvas.toDataURL('image/jpeg', 0.8);
    }
    
    async captureAndRecognize() {
        if (this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.showLoading(true);
            this.showResult('Processing your face...', 'info');
            
            const imageData = this.captureImage();
            
            const response = await fetch('/api/recognize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showResult(
                    `<div class="d-flex align-items-center">
                        <i class="fas fa-check-circle text-success me-3 fa-2x"></i>
                        <div>
                            <h5 class="mb-1">Welcome back, ${result.employee_name}!</h5>
                            <p class="mb-0">Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
                        </div>
                    </div>`,
                    'success'
                );
                
                // Stop camera
                this.stopCamera();
                
                // Redirect to dashboard after 2 seconds
                setTimeout(() => {
                    window.location.href = result.redirect_url;
                }, 2000);
                
            } else {
                this.showResult(
                    `<div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle text-warning me-3 fa-2x"></i>
                        <div>
                            <h6 class="mb-1">Recognition Failed</h6>
                            <p class="mb-0">${result.message}</p>
                        </div>
                    </div>`,
                    'warning'
                );
                
                // Show retry button
                this.retryBtn.style.display = 'inline-block';
            }
            
        } catch (error) {
            console.error('Error during face recognition:', error);
            this.showResult(
                `<div class="d-flex align-items-center">
                    <i class="fas fa-times-circle text-danger me-3 fa-2x"></i>
                    <div>
                        <h6 class="mb-1">Connection Error</h6>
                        <p class="mb-0">Please check your connection and try again.</p>
                    </div>
                </div>`,
                'danger'
            );
        } finally {
            this.isProcessing = false;
            this.showLoading(false);
        }
    }
    
    resetCapture() {
        this.showResult('', '');
        this.retryBtn.style.display = 'none';
        this.captureBtn.style.display = 'inline-block';
    }
    
    startFaceDetectionPreview() {
        // Simple face detection indicator (visual feedback)
        const scannerLine = document.getElementById('scannerLine');
        if (scannerLine) {
            scannerLine.style.display = 'block';
            scannerLine.style.animation = 'scan 2s linear infinite';
        }
    }
    
    updateCameraStatus(message, type) {
        if (!this.cameraStatus) return;
        
        const iconClass = {
            'success': 'fas fa-video text-success',
            'warning': 'fas fa-exclamation-triangle text-warning',
            'danger': 'fas fa-video-slash text-danger'
        }[type] || 'fas fa-camera-slash text-muted';
        
        this.cameraStatus.innerHTML = `
            <i class="${iconClass}"></i>
            <span>${message}</span>
        `;
    }
    
    showResult(message, type) {
        if (!this.result) return;
        
        if (!message) {
            this.result.innerHTML = '';
            return;
        }
        
        const alertClass = type ? `alert-${type}` : '';
        this.result.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    }
    
    showLoading(show) {
        if (this.loadingSection) {
            this.loadingSection.style.display = show ? 'block' : 'none';
        }
        
        if (this.captureBtn) {
            this.captureBtn.disabled = show;
            if (show) {
                this.captureBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            } else {
                this.captureBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Capture & Login';
            }
        }
    }
}

// Employee Registration Class
class EmployeeRegistration {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.startCameraBtn = document.getElementById('startCamera');
        this.captureBtn = document.getElementById('captureBtn');
        this.retakeBtn = document.getElementById('retakeBtn');
        this.submitBtn = document.getElementById('submitBtn');
        this.form = document.getElementById('registrationForm');
        this.result = document.getElementById('result');
        this.loadingSection = document.getElementById('loadingSection');
        this.facePreview = document.getElementById('facePreview');
        this.capturedImage = document.getElementById('capturedImage');
        this.faceQuality = document.getElementById('faceQuality');
        this.qualityMessage = document.getElementById('qualityMessage');
        
        this.stream = null;
        this.capturedImageData = null;
        this.isProcessing = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        if (this.startCameraBtn) {
            this.startCameraBtn.addEventListener('click', () => this.startCamera());
        }
        
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.captureFace());
        }
        
        if (this.retakeBtn) {
            this.retakeBtn.addEventListener('click', () => this.retakeFace());
        }
        
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        // Form validation
        const requiredFields = ['employeeId', 'fullName', 'email', 'department'];
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('input', () => this.validateForm());
            }
        });
        
        window.addEventListener('beforeunload', () => this.stopCamera());
    }
    
    async startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 640, min: 320 },
                    height: { ideal: 480, min: 240 },
                    facingMode: 'user'
                },
                audio: false
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            this.video.onloadedmetadata = () => {
                this.video.play();
                this.startCameraBtn.style.display = 'none';
                this.captureBtn.style.display = 'inline-block';
                this.showFaceQuality('Position your face in the camera frame', 'info');
            };
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            let errorMessage = 'Camera access error: ';
            
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Please allow camera access and refresh the page.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No camera device found.';
            } else {
                errorMessage += error.message;
            }
            
            this.showResult(errorMessage, 'danger');
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    captureFace() {
        try {
            const context = this.canvas.getContext('2d');
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            
            context.drawImage(this.video, 0, 0);
            this.capturedImageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Show preview
            this.capturedImage.src = this.capturedImageData;
            this.facePreview.style.display = 'block';
            this.video.style.display = 'none';
            
            // Update buttons
            this.captureBtn.style.display = 'none';
            this.retakeBtn.style.display = 'inline-block';
            
            // Stop camera
            this.stopCamera();
            
            // Show success message
            this.showFaceQuality('Face captured successfully!', 'success');
            
            // Validate form
            this.validateForm();
            
        } catch (error) {
            console.error('Error capturing face:', error);
            this.showResult('Error capturing face. Please try again.', 'danger');
        }
    }
    
    retakeFace() {
        // Reset capture state
        this.capturedImageData = null;
        this.facePreview.style.display = 'none';
        this.video.style.display = 'block';
        this.retakeBtn.style.display = 'none';
        this.startCameraBtn.style.display = 'inline-block';
        
        // Reset form validation
        this.validateForm();
        this.showFaceQuality('Click "Start Camera" to begin face capture', 'info');
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.showLoading(true);
            this.showResult('Registering employee...', 'info');
            
            const formData = {
                employee_id: document.getElementById('employeeId').value,
                name: document.getElementById('fullName').value,
                email: document.getElementById('email').value,
                department: document.getElementById('department').value,
                image: this.capturedImageData
            };
            
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showResult(
                    `<div class="d-flex align-items-center">
                        <i class="fas fa-check-circle text-success me-3 fa-2x"></i>
                        <div>
                            <h5 class="mb-1">Registration Successful!</h5>
                            <p class="mb-0">${result.message}</p>
                        </div>
                    </div>`,
                    'success'
                );
                
                // Reset form after 3 seconds
                setTimeout(() => {
                    if (confirm('Registration successful! Would you like to register another employee?')) {
                        window.location.reload();
                    } else {
                        window.location.href = '/';
                    }
                }, 3000);
                
            } else {
                this.showResult(
                    `<div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle text-warning me-3 fa-2x"></i>
                        <div>
                            <h6 class="mb-1">Registration Failed</h6>
                            <p class="mb-0">${result.message}</p>
                        </div>
                    </div>`,
                    'warning'
                );
            }
            
        } catch (error) {
            console.error('Error during registration:', error);
            this.showResult(
                `<div class="d-flex align-items-center">
                    <i class="fas fa-times-circle text-danger me-3 fa-2x"></i>
                    <div>
                        <h6 class="mb-1">Connection Error</h6>
                        <p class="mb-0">Please check your connection and try again.</p>
                    </div>
                </div>`,
                'danger'
            );
        } finally {
            this.isProcessing = false;
            this.showLoading(false);
        }
    }
    
    validateForm() {
        const employeeId = document.getElementById('employeeId').value;
        const fullName = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const department = document.getElementById('department').value;
        
        const isFormValid = employeeId && fullName && email && department && this.capturedImageData;
        
        if (this.submitBtn) {
            this.submitBtn.disabled = !isFormValid;
        }
        
        return isFormValid;
    }
    
    showResult(message, type) {
        if (!this.result) return;
        
        if (!message) {
            this.result.innerHTML = '';
            return;
        }
        
        const alertClass = type ? `alert-${type}` : '';
        this.result.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    }
    
    showLoading(show) {
        if (this.loadingSection) {
            this.loadingSection.style.display = show ? 'block' : 'none';
        }
        
        if (this.submitBtn) {
            this.submitBtn.disabled = show || !this.validateForm();
            if (show) {
                this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Registering...';
            } else {
                this.submitBtn.innerHTML = '<i class="fas fa-user-plus me-2"></i>Register Employee';
            }
        }
    }
    
    showFaceQuality(message, type) {
        if (!this.faceQuality || !this.qualityMessage) return;
        
        this.qualityMessage.textContent = message;
        this.faceQuality.style.display = 'block';
        
        const alertClasses = {
            'info': 'alert-info',
            'success': 'alert-success',
            'warning': 'alert-warning',
            'danger': 'alert-danger'
        };
        
        const alert = this.faceQuality.querySelector('.alert');
        if (alert) {
            alert.className = `alert ${alertClasses[type] || 'alert-info'}`;
        }
    }
}

// Utility functions
class CameraUtils {
    static async checkCameraSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera not supported by this browser');
        }
        
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (videoDevices.length === 0) {
                throw new Error('No camera devices found');
            }
            
            return videoDevices;
        } catch (error) {
            throw new Error('Error checking camera support: ' + error.message);
        }
    }
    
    static async requestCameraPermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            return false;
        }
    }
}

// Initialize based on page
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the login page
    if (document.getElementById('video') && document.querySelector('.login-card')) {
        new FaceCapture();
    }
    
    // Check if we're on the registration page
    if (document.getElementById('registrationForm')) {
        new EmployeeRegistration();
    }
    
    // Check camera support
    CameraUtils.checkCameraSupport()
        .then(devices => {
            console.log(`Found ${devices.length} camera device(s)`);
        })
        .catch(error => {
            console.warn('Camera support check failed:', error.message);
        });
});
