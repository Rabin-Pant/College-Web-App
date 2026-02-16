from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.settings import Settings

admin_settings_bp = Blueprint('admin_settings', __name__)

@admin_settings_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_settings():
    """Get all system settings"""
    try:
        settings = Settings.get_all()
        return jsonify(settings), 200
    except Exception as e:
        print(f"Error getting settings: {e}")
        return jsonify({'error': str(e)}), 500


@admin_settings_bp.route('/<key>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_setting(key):
    """Get a specific setting"""
    try:
        value = Settings.get(key)
        if value is None:
            return jsonify({'error': 'Setting not found'}), 404
        return jsonify({key: value}), 200
    except Exception as e:
        print(f"Error getting setting: {e}")
        return jsonify({'error': str(e)}), 500


@admin_settings_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def update_settings():
    """Update multiple settings at once"""
    try:
        data = request.get_json()
        print(f"📡 Updating settings: {data}")
        
        # Filter out non-setting fields
        settings_data = {}
        allowed_settings = [
            'site_name', 'site_url', 'contact_email', 'max_file_size',
            'allowed_file_types', 'enable_registration', 'require_email_verification',
            'allow_password_reset', 'session_timeout', 'smtp_server', 'smtp_port',
            'smtp_username', 'smtp_password', 'enable_email_notifications',
            'enable_push_notifications', 'notification_digest'
        ]
        
        for key in allowed_settings:
            if key in data:
                settings_data[key] = str(data[key])
        
        if settings_data:
            Settings.set_many(settings_data)
            print(f"✅ Settings updated: {settings_data}")
        
        # Get updated settings to return
        updated_settings = Settings.get_all()
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': updated_settings
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_settings_bp.route('/<key>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_setting(key):
    """Update a single setting"""
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({'error': 'Value is required'}), 400
        
        Settings.set(key, str(value))
        
        return jsonify({
            'message': f'Setting {key} updated successfully',
            key: value
        }), 200
        
    except Exception as e:
        print(f"Error updating setting: {e}")
        return jsonify({'error': str(e)}), 500