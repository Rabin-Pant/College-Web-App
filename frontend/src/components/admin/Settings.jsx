import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { FiSave, FiGlobe, FiMail, FiShield, FiDatabase, FiBell, FiRefreshCw } from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    // General Settings
    site_name: 'CollegeApp',
    site_url: 'http://localhost:3000',
    contact_email: 'admin@yourcollege.edu',
    
    // File Settings
    max_file_size: '50',
    allowed_file_types: 'pdf,doc,docx,ppt,pptx,jpg,png,zip',
    
    // Security Settings
    enable_registration: 'true',
    require_email_verification: 'false',
    allow_password_reset: 'true',
    session_timeout: '30',
    
    // Email Settings
    smtp_server: 'smtp.gmail.com',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    
    // Notification Settings
    enable_email_notifications: 'true',
    enable_push_notifications: 'false',
    notification_digest: 'daily'
  });

  // Fetch settings on component mount
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      console.log('📡 Fetching settings from API...');
      const response = await api.get('/admin/settings/');
      console.log('✅ Settings received:', response.data);
      
      // Update state with fetched settings
      setSettings(prev => ({
        ...prev,
        ...response.data
      }));
    } catch (error) {
      console.error('❌ Failed to fetch settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (checked ? 'true' : 'false') : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      console.log('📡 Saving settings:', settings);
      const response = await api.post('/admin/settings/', settings);
      console.log('✅ Save response:', response.data);
      
      toast.success('Settings saved successfully!');
      
      // Update with any values returned from server
      if (response.data.settings) {
        setSettings(prev => ({ ...prev, ...response.data.settings }));
      }
    } catch (error) {
      console.error('❌ Failed to save settings:', error);
      console.error('❌ Error response:', error.response?.data);
      toast.error(error.response?.data?.error || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <FiGlobe className="mr-2 text-primary-600" />
            System Settings
          </h1>
          <button
            onClick={fetchSettings}
            className="text-gray-600 hover:text-gray-900 p-2"
            title="Refresh"
          >
            <FiRefreshCw className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* General Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <FiGlobe className="mr-2" />
              General Settings
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Site Name
                </label>
                <input
                  type="text"
                  name="site_name"
                  value={settings.site_name}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Site URL
                </label>
                <input
                  type="url"
                  name="site_url"
                  value={settings.site_url}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contact Email
                </label>
                <input
                  type="email"
                  name="contact_email"
                  value={settings.contact_email}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* File Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <FiDatabase className="mr-2" />
              File Upload Settings
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max File Size (MB)
                </label>
                <input
                  type="number"
                  name="max_file_size"
                  value={settings.max_file_size}
                  onChange={handleChange}
                  className="input-field"
                  min="1"
                  max="500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Current value: {settings.max_file_size}MB
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Allowed File Types
                </label>
                <input
                  type="text"
                  name="allowed_file_types"
                  value={settings.allowed_file_types}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="pdf,doc,docx,zip"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Comma-separated list of file extensions
                </p>
              </div>
            </div>
          </div>

          {/* Security Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <FiShield className="mr-2" />
              Security Settings
            </h2>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="enable_registration"
                  checked={settings.enable_registration === 'true'}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Enable new user registration
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="require_email_verification"
                  checked={settings.require_email_verification === 'true'}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Require email verification
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="allow_password_reset"
                  checked={settings.allow_password_reset === 'true'}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Allow password reset
                </span>
              </label>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Session Timeout (minutes)
                </label>
                <input
                  type="number"
                  name="session_timeout"
                  value={settings.session_timeout}
                  onChange={handleChange}
                  className="input-field w-32"
                  min="5"
                  max="120"
                />
              </div>
            </div>
          </div>

          {/* Email Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <FiMail className="mr-2" />
              Email Configuration
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Server
                </label>
                <input
                  type="text"
                  name="smtp_server"
                  value={settings.smtp_server}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Port
                </label>
                <input
                  type="text"
                  name="smtp_port"
                  value={settings.smtp_port}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Username
                </label>
                <input
                  type="text"
                  name="smtp_username"
                  value={settings.smtp_username}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="your-email@gmail.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Password
                </label>
                <input
                  type="password"
                  name="smtp_password"
                  value={settings.smtp_password}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <FiBell className="mr-2" />
              Notification Settings
            </h2>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="enable_email_notifications"
                  checked={settings.enable_email_notifications === 'true'}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Enable email notifications
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="enable_push_notifications"
                  checked={settings.enable_push_notifications === 'true'}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Enable push notifications
                </span>
              </label>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notification Digest
                </label>
                <select
                  name="notification_digest"
                  value={settings.notification_digest}
                  onChange={handleChange}
                  className="input-field w-48"
                >
                  <option value="realtime">Real-time</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-6 border-t">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminSettings;