import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FiLock, FiSave, FiX, FiAlertCircle } from 'react-icons/fi';
import toast from 'react-hot-toast';

const ChangePassword = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};

    if (!formData.current_password) {
      newErrors.current_password = 'Current password is required';
    }

    if (!formData.new_password) {
      newErrors.new_password = 'New password is required';
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.new_password)) {
      newErrors.new_password = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(formData.new_password)) {
      newErrors.new_password = 'Password must contain at least one lowercase letter';
    } else if (!/[0-9]/.test(formData.new_password)) {
      newErrors.new_password = 'Password must contain at least one number';
    } else if (!/[!@#$%^&*]/.test(formData.new_password)) {
      newErrors.new_password = 'Password must contain at least one special character';
    }

    if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await api.put('/auth/change-password', {
        current_password: formData.current_password,
        new_password: formData.new_password
      });
      
      toast.success('Password changed successfully!');
      navigate('/profile');
    } catch (error) {
      console.error('Failed to change password:', error);
      
      if (error.response?.status === 401) {
        setErrors({ current_password: 'Current password is incorrect' });
        toast.error('Current password is incorrect');
      } else {
        toast.error('Failed to change password');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Change Password</h1>
          <button
            onClick={() => navigate('/profile')}
            className="text-gray-400 hover:text-gray-600"
          >
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Password
            </label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="password"
                name="current_password"
                value={formData.current_password}
                onChange={handleChange}
                className={`pl-10 input-field ${errors.current_password ? 'border-red-500 focus:ring-red-500' : ''}`}
                placeholder="Enter current password"
              />
            </div>
            {errors.current_password && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <FiAlertCircle className="mr-1" /> {errors.current_password}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Password
            </label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="password"
                name="new_password"
                value={formData.new_password}
                onChange={handleChange}
                className={`pl-10 input-field ${errors.new_password ? 'border-red-500 focus:ring-red-500' : ''}`}
                placeholder="Enter new password"
              />
            </div>
            {errors.new_password ? (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <FiAlertCircle className="mr-1" /> {errors.new_password}
              </p>
            ) : (
              <p className="mt-1 text-xs text-gray-500">
                Minimum 8 characters with uppercase, lowercase, number & special character
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm New Password
            </label>
            <div className="relative">
              <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="password"
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                className={`pl-10 input-field ${errors.confirm_password ? 'border-red-500 focus:ring-red-500' : ''}`}
                placeholder="Confirm new password"
              />
            </div>
            {errors.confirm_password && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <FiAlertCircle className="mr-1" /> {errors.confirm_password}
              </p>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">Password Requirements:</h3>
            <ul className="text-xs text-blue-700 space-y-1">
              <li className="flex items-center">
                <span className={`mr-2 ${formData.new_password.length >= 8 ? 'text-green-600' : ''}`}>
                  {formData.new_password.length >= 8 ? '✓' : '○'}
                </span>
                At least 8 characters
              </li>
              <li className="flex items-center">
                <span className={`mr-2 ${/[A-Z]/.test(formData.new_password) ? 'text-green-600' : ''}`}>
                  {/[A-Z]/.test(formData.new_password) ? '✓' : '○'}
                </span>
                One uppercase letter
              </li>
              <li className="flex items-center">
                <span className={`mr-2 ${/[a-z]/.test(formData.new_password) ? 'text-green-600' : ''}`}>
                  {/[a-z]/.test(formData.new_password) ? '✓' : '○'}
                </span>
                One lowercase letter
              </li>
              <li className="flex items-center">
                <span className={`mr-2 ${/[0-9]/.test(formData.new_password) ? 'text-green-600' : ''}`}>
                  {/[0-9]/.test(formData.new_password) ? '✓' : '○'}
                </span>
                One number
              </li>
              <li className="flex items-center">
                <span className={`mr-2 ${/[!@#$%^&*]/.test(formData.new_password) ? 'text-green-600' : ''}`}>
                  {/[!@#$%^&*]/.test(formData.new_password) ? '✓' : '○'}
                </span>
                One special character (!@#$%^&*)
              </li>
            </ul>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Changing...
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  Change Password
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePassword;