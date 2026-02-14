import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';
import { FiVideo, FiX, FiCalendar, FiClock, FiLink } from 'react-icons/fi';
import toast from 'react-hot-toast';

const CreateZoomModal = ({ isOpen, onClose, sectionId: propSectionId, onSuccess }) => {
  const { sectionId: paramSectionId } = useParams();
  const sectionId = propSectionId || paramSectionId;
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    topic: '',
    description: '',
    meeting_date: '',
    start_time: '',
    duration_minutes: 60,
    meeting_link: '',
    meeting_id: '',
    password: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setFormData({
      topic: '',
      description: '',
      meeting_date: '',
      start_time: '',
      duration_minutes: 60,
      meeting_link: '',
      meeting_id: '',
      password: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.topic || !formData.meeting_date || !formData.start_time) {
      toast.error('Topic, date and time are required');
      return;
    }

    if (!sectionId) {
      toast.error('Section ID is missing');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/teacher/zoom/', {
        ...formData,
        section_id: parseInt(sectionId)
      });
      
      toast.success('Zoom meeting scheduled successfully');
      if (onSuccess) onSuccess();
      resetForm();
      onClose();
    } catch (error) {
      console.error('Failed to schedule meeting:', error);
      toast.error(error.response?.data?.error || 'Failed to schedule meeting');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <FiVideo className="mr-2 text-primary-600" />
            Schedule Zoom Meeting
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Meeting Topic <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="topic"
              value={formData.topic}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g., Lecture 1: Introduction"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="input-field"
              placeholder="Meeting description..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiCalendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="date"
                  name="meeting_date"
                  value={formData.meeting_date}
                  onChange={handleChange}
                  className="pl-10 input-field"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Time <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiClock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleChange}
                  className="pl-10 input-field"
                  required
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (minutes)
            </label>
            <select
              name="duration_minutes"
              value={formData.duration_minutes}
              onChange={handleChange}
              className="input-field"
            >
              <option value="30">30 minutes</option>
              <option value="60">1 hour</option>
              <option value="90">1.5 hours</option>
              <option value="120">2 hours</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Meeting Link
            </label>
            <div className="relative">
              <FiLink className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="url"
                name="meeting_link"
                value={formData.meeting_link}
                onChange={handleChange}
                className="pl-10 input-field"
                placeholder="https://zoom.us/j/..."
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meeting ID
              </label>
              <input
                type="text"
                name="meeting_id"
                value={formData.meeting_id}
                onChange={handleChange}
                className="input-field"
                placeholder="123 456 7890"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="text"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input-field"
                placeholder="Meeting password"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
            >
              {loading ? 'Scheduling...' : 'Schedule Meeting'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateZoomModal;