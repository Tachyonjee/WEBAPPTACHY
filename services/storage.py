import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from services.security import SecurityService

class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        from config import Config
        self.upload_folder = Config.UPLOAD_FOLDER
        self.max_file_size = Config.MAX_CONTENT_LENGTH
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Create subdirectories
        self.subdirs = {
            'videos': os.path.join(self.upload_folder, 'videos'),
            'documents': os.path.join(self.upload_folder, 'documents'),
            'images': os.path.join(self.upload_folder, 'images'),
            'temp': os.path.join(self.upload_folder, 'temp')
        }
        
        for subdir in self.subdirs.values():
            os.makedirs(subdir, exist_ok=True)
    
    def save_file(self, file, file_type='document', custom_name=None):
        """
        Save uploaded file to storage
        
        Args:
            file: Flask file object
            file_type: Type of file ('video', 'document', 'image', 'temp')
            custom_name: Custom filename (optional)
            
        Returns:
            {
                'success': bool,
                'file_path': str,
                'file_url': str,
                'original_filename': str,
                'error': str (if failed)
            }
        """
        try:
            if not file or not file.filename:
                return {
                    'success': False,
                    'error': 'No file provided'
                }
            
            # Validate file type
            if file_type not in self.subdirs:
                return {
                    'success': False,
                    'error': f'Invalid file type: {file_type}'
                }
            
            # Get file extension
            original_filename = file.filename
            file_ext = os.path.splitext(original_filename)[1].lower()
            
            # Validate file extension based on type
            allowed_extensions = self._get_allowed_extensions(file_type)
            if file_ext not in allowed_extensions:
                return {
                    'success': False,
                    'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                }
            
            # Generate unique filename
            if custom_name:
                base_name = SecurityService.sanitize_filename(custom_name)
                if not base_name.endswith(file_ext):
                    base_name += file_ext
            else:
                base_name = f"{uuid.uuid4()}{file_ext}"
            
            filename = secure_filename(base_name)
            
            # Determine storage path
            storage_dir = self.subdirs[file_type]
            file_path = os.path.join(storage_dir, filename)
            
            # Check if file already exists
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
                filename = os.path.basename(file_path)
            
            # Save file
            file.save(file_path)
            
            # Generate URL (relative to upload folder)
            relative_path = os.path.relpath(file_path, self.upload_folder)
            file_url = f"/uploads/{relative_path.replace(os.sep, '/')}"
            
            return {
                'success': True,
                'file_path': file_path,
                'file_url': file_url,
                'filename': filename,
                'original_filename': original_filename
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to save file: {str(e)}'
            }
    
    def delete_file(self, file_path):
        """
        Delete file from storage
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_info(self, file_path):
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            dict: File information or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'mime_type': mime_type,
                'extension': os.path.splitext(file_path)[1].lower()
            }
        
        except Exception:
            return None
    
    def _get_allowed_extensions(self, file_type):
        """Get allowed file extensions for each file type"""
        extensions = {
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'temp': ['.csv', '.xlsx', '.xls', '.txt']  # For temporary uploads like bulk import
        }
        
        return extensions.get(file_type, [])
    
    def get_video_url(self, file_path):
        """
        Get URL for video file with proper MIME type headers
        This is a placeholder for more sophisticated video serving
        """
        if not os.path.exists(file_path):
            return None
        
        relative_path = os.path.relpath(file_path, self.upload_folder)
        return f"/uploads/{relative_path.replace(os.sep, '/')}"
    
    def cleanup_temp_files(self, older_than_hours=24):
        """
        Clean up temporary files older than specified hours
        
        Args:
            older_than_hours: Delete files older than this many hours
            
        Returns:
            int: Number of files deleted
        """
        import time
        
        temp_dir = self.subdirs['temp']
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        
        deleted_count = 0
        
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
        
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
        
        return deleted_count

# Singleton instance
storage_service = StorageService()
