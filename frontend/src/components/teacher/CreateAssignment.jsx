import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiFile, FiCalendar, FiClock, FiUpload, 
  FiTrash2, FiSave, FiX 
} from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import Loader from '../common/Loader';

const CreateAssignment = () => {
  const { sectionId } = useParams();  // Changed from classId to sectionId
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [sectionData, setSectionData] = useState(null);
  const [files, setFiles] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    instructions: '',
    due_date: '',
    due_time: '23:59',
    points_possible: 100,
    late_policy: 'no_submissions',
    late_penalty: 10,
    allow_late: false,
    is_published: false
  });

  useEffect(() => {
    if (sectionId) {
      fetchSectionDetails();
    } else {
      console.error('No sectionId provided');
      toast.error('Invalid section');
      navigate('/teacher/dashboard');
    }
  }, [sectionId]);

  const fetchSectionDetails = async () => {
    try {
      const response = await api.get(`/teacher/sections/${sectionId}`);
      setSectionData(response.data.section);
    } catch (error) {
      console.error('Failed to fetch section:', error);
      toast.error('Section not found');
      navigate('/teacher/dashboard');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const onDrop = (acceptedFiles) => {
    setFiles([...files, ...acceptedFiles]);
    toast.success(`${acceptedFiles.length} file(s) added`);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 52428800, // 50MB
    multiple: true,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'image/*': ['.jpg', '.jpeg', '.png'],
      'video/*': ['.mp4', '.mov'],
      'application/zip': ['.zip']
    }
  });

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const dueDateTime = `${formData.due_date}T${formData.due_time}:00`;

      const assignmentData = {
        ...formData,
        section_id: parseInt(sectionId),  // Changed from class_id to section_id
        due_date: dueDateTime
      };

      const response = await api.post('/teacher/assignments/', assignmentData);
      const assignmentId = response.data.assignment_id;

      // Upload attachments if any
      if (files.length > 0) {
        const fileData = new FormData();
        files.forEach(file => {
          fileData.append('files', file);
        });
        
        await api.post(`/teacher/assignments/${assignmentId}/attachments`, fileData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }

      toast.success('Assignment created successfully!');
      navigate(`/teacher/section/${sectionId}`);  // Navigate to section view
    } catch (error) {
      console.error('Failed to create assignment:', error);
      toast.error(error.response?.data?.error || 'Failed to create assignment');
    } finally {
      setLoading(false);
    }
  };

  if (!sectionData) return <Loader />;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Assignment</h1>
            <p className="text-gray-600 mt-1">
              {sectionData?.subject_name} • {sectionData?.course_name} • Section {sectionData?.section_name}
            </p>
          </div>
          <button
            onClick={() => navigate(`/teacher/section/${sectionId}`)}
            className="text-gray-400 hover:text-gray-600"
          >
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Basic Information
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assignment Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g., Chapter 1 Quiz, Final Project, Research Paper"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Instructions
              </label>
              <textarea
                name="instructions"
                value={formData.instructions}
                onChange={handleChange}
                rows={8}
                className="input-field"
                placeholder="Provide detailed instructions for students..."
              />
            </div>
          </div>

          {/* Due Date & Points */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Due Date & Points
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Due Date <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <FiCalendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="date"
                    name="due_date"
                    value={formData.due_date}
                    onChange={handleChange}
                    className="pl-10 input-field"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Due Time
                </label>
                <div className="relative">
                  <FiClock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="time"
                    name="due_time"
                    value={formData.due_time}
                    onChange={handleChange}
                    className="pl-10 input-field"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Points Possible <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="points_possible"
                  value={formData.points_possible}
                  onChange={handleChange}
                  min="0"
                  max="1000"
                  className="input-field"
                  required
                />
              </div>
            </div>
          </div>

          {/* Late Submission Policy */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Late Submission Policy
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Late Policy
                </label>
                <select
                  name="late_policy"
                  value={formData.late_policy}
                  onChange={handleChange}
                  className="input-field"
                >
                  <option value="no_submissions">❌ No submissions after due date</option>
                  <option value="accept">✅ Accept late submissions</option>
                  <option value="deduct">📉 Deduct points for late submissions</option>
                </select>
              </div>

              {formData.late_policy === 'deduct' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Late Penalty (% per day)
                  </label>
                  <input
                    type="number"
                    name="late_penalty"
                    value={formData.late_penalty}
                    onChange={handleChange}
                    min="0"
                    max="100"
                    className="input-field"
                    placeholder="e.g., 10"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Attachments */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Attachments
            </h2>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition duration-200 ${
                isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <FiUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {isDragActive ? (
                <p className="text-primary-600 font-medium">Drop files here...</p>
              ) : (
                <>
                  <p className="text-gray-600">Drag & drop files here, or click to select</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Supported: PDF, DOC, PPT, Images, Videos, ZIP (Max 50MB)
                  </p>
                </>
              )}
            </div>

            {files.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Files to upload ({files.length})
                </h3>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center flex-1">
                        <FiFile className="text-gray-400 mr-2" />
                        <span className="text-sm text-gray-700 truncate max-w-xs">{file.name}</span>
                        <span className="text-xs text-gray-500 ml-2">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="text-red-600 hover:text-red-700 p-1"
                      >
                        <FiTrash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Publish Settings */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Publish Settings
            </h2>
            
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_published"
                  checked={formData.is_published}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Publish immediately (students can see and submit)
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="allow_late"
                  checked={formData.allow_late}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Allow late submissions (overrides late policy)
                </span>
              </label>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={() => navigate(`/teacher/section/${sectionId}`)}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.title || !formData.due_date}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  Create Assignment
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAssignment;