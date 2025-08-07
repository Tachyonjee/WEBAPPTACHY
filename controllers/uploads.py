from flask import Blueprint, request, jsonify
from services.security import security_service
from services.storage import storage_service
import os

uploads_bp = Blueprint('uploads', __name__)

@uploads_bp.route('/file', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def upload_file():
    """Upload a file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'documents')
        custom_name = request.form.get('custom_name')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not storage_service.validate_file_type(file.filename, file_type):
            allowed_extensions = storage_service.get_allowed_extensions(file_type)
            return jsonify({
                'error': f'Invalid file type. Allowed extensions: {", ".join(allowed_extensions)}'
            }), 400
        
        # Validate file size and security
        validation_result = security_service.validate_file_upload(
            file,
            allowed_extensions=storage_service.get_allowed_extensions(file_type),
            max_size_mb=50
        )
        
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        # Save file
        result = storage_service.save_file(file, file_type, custom_name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'file_info': {
                    'filename': result['filename'],
                    'file_size': result['file_size'],
                    'file_type': result['file_type'],
                    'url': result['url']
                }
            })
        else:
            return jsonify({'error': result['error']}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/video', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def upload_video():
    """Upload a video file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate video file
        video_extensions = storage_service.get_allowed_extensions('videos')
        if not storage_service.validate_file_type(file.filename, 'videos'):
            return jsonify({
                'error': f'Invalid video format. Allowed: {", ".join(video_extensions)}'
            }), 400
        
        # Validate file size (larger limit for videos)
        validation_result = security_service.validate_file_upload(
            file,
            allowed_extensions=video_extensions,
            max_size_mb=100  # 100MB for videos
        )
        
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        # Save video
        result = storage_service.save_file(file, 'videos')
        
        if result['success']:
            # Generate thumbnail URL (placeholder - would need video processing)
            thumbnail_url = result['url'].replace('/videos/', '/images/').replace('.mp4', '_thumb.jpg')
            
            return jsonify({
                'success': True,
                'message': 'Video uploaded successfully',
                'video_info': {
                    'filename': result['filename'],
                    'file_size': result['file_size'],
                    'url': result['url'],
                    'thumbnail_url': thumbnail_url
                }
            })
        else:
            return jsonify({'error': result['error']}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/csv-template')
@security_service.require_role(['operator', 'admin'])
def download_csv_template():
    """Download CSV template for question import"""
    try:
        from services.csv_importer import csv_importer
        template_content = csv_importer.get_template_csv()
        
        from flask import Response
        return Response(
            template_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=questions_template.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/validate-csv', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def validate_csv():
    """Validate CSV file before import"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = ['csv', 'xlsx']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({'error': 'Only CSV and XLSX files are allowed'}), 400
        
        # Save file temporarily
        result = storage_service.save_file(file, 'temp')
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        file_path = result['file_path']
        
        try:
            # Validate file
            from services.csv_importer import csv_importer
            validation_result = csv_importer.validate_file(file_path)
            
            # Clean up temp file
            storage_service.delete_file(file_path)
            
            return jsonify(validation_result)
            
        except Exception as e:
            # Clean up temp file on error
            storage_service.delete_file(file_path)
            raise e
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/file-info/<path:file_path>')
@security_service.require_role(['operator', 'admin', 'mentor'])
def get_file_info(file_path):
    """Get information about an uploaded file"""
    try:
        # Construct full file path
        from config import Config
        full_path = os.path.join(Config.UPLOAD_FOLDER, file_path)
        
        file_info = storage_service.get_file_info(full_path)
        
        if file_info:
            return jsonify({
                'success': True,
                'file_info': file_info
            })
        else:
            return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/cleanup-temp', methods=['POST'])
@security_service.require_role(['admin'])
def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        max_age_hours = request.json.get('max_age_hours', 24)
        
        storage_service.cleanup_temp_files(max_age_hours)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up temp files older than {max_age_hours} hours'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/storage-stats')
@security_service.require_role(['admin'])
def get_storage_stats():
    """Get storage usage statistics"""
    try:
        from config import Config
        upload_folder = Config.UPLOAD_FOLDER
        
        stats = {
            'total_size': 0,
            'file_count': 0,
            'folders': {}
        }
        
        if os.path.exists(upload_folder):
            for folder_name in ['videos', 'documents', 'images', 'temp']:
                folder_path = os.path.join(upload_folder, folder_name)
                folder_size = 0
                folder_files = 0
                
                if os.path.exists(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                size = os.path.getsize(file_path)
                                folder_size += size
                                folder_files += 1
                            except:
                                pass
                
                stats['folders'][folder_name] = {
                    'size_mb': round(folder_size / (1024 * 1024), 2),
                    'file_count': folder_files
                }
                
                stats['total_size'] += folder_size
                stats['file_count'] += folder_files
        
        stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'storage_stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
