import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiFile, FiUpload, FiLink, FiYoutube, 
  FiTrash2, FiSave, FiX, FiFileText 
} from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import Loader from '../common/Loader';

const UploadMaterial = () => {
  const { sectionId } = useParams();  // Changed from classId to sectionId
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [sectionData, setSectionData] = useState(null);
  const [files, setFiles] = useState([]);
  const [materialType, setMaterialType] = useState('document');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'document',
    url: '',
    week: '',
    topic: '',
    tags: ''
  });

  useEffect(() => {
    if (sectionId) {
      fetchSectionDetails();
    } else {
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
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTypeChange = (type) => {
    setMaterialType(type);
    setFormData(prev => ({ ...prev, type }));
  };

  const onDrop = (acceptedFiles) => {
    setFiles([...files, ...acceptedFiles]);
    toast.success(`${acceptedFiles.length} file(s) added`);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 104857600, // 100MB
    multiple: true,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt', '.pptx'],
      'video/*': ['.mp4', '.mov', '.avi', '.webm'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif'],
      'application/zip': ['.zip'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc', '.docx']
    }
  });

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (materialType === 'link' || materialType === 'video') {
        // Upload link/video
        const materialData = {
          ...formData,
          section_id: parseInt(sectionId),  // Changed from class_id to section_id
          type: materialType
        };

        await api.post('/teacher/materials/', materialData);
        toast.success('Material added successfully!');
      } else {
        // Upload files
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('section_id', sectionId);  // Changed from class_id
          formData.append('title', formData.title || file.name);
          formData.append('description', formData.description);
          formData.append('type', materialType);
          formData.append('week', formData.week);
          formData.append('topic', formData.topic);
          formData.append('tags', formData.tags);

          await api.post('/teacher/materials/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
        }
        toast.success(`${files.length} material(s) uploaded successfully!`);
      }

      navigate(`/teacher/section/${sectionId}`);  // Changed to section path
    } catch (error) {
      console.error('Failed to upload material:', error);
      toast.error(error.response?.data?.error || 'Failed to upload material');
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
            <h1 className="text-2xl font-bold text-gray-900">Upload Study Material</h1>
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

        {/* Material Type Selection */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <button
            type="button"
            onClick={() => handleTypeChange('document')}
            className={`p-4 rounded-lg border-2 transition duration-200 ${
              materialType === 'document'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <FiFileText className={`h-6 w-6 mx-auto mb-2 ${
              materialType === 'document' ? 'text-primary-600' : 'text-gray-400'
            }`} />
            <span className={`text-sm font-medium ${
              materialType === 'document' ? 'text-primary-600' : 'text-gray-600'
            }`}>
              Document
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleTypeChange('presentation')}
            className={`p-4 rounded-lg border-2 transition duration-200 ${
              materialType === 'presentation'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <FiFile className={`h-6 w-6 mx-auto mb-2 ${
              materialType === 'presentation' ? 'text-primary-600' : 'text-gray-400'
            }`} />
            <span className={`text-sm font-medium ${
              materialType === 'presentation' ? 'text-primary-600' : 'text-gray-600'
            }`}>
              Presentation
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleTypeChange('video')}
            className={`p-4 rounded-lg border-2 transition duration-200 ${
              materialType === 'video'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <FiYoutube className={`h-6 w-6 mx-auto mb-2 ${
              materialType === 'video' ? 'text-primary-600' : 'text-gray-400'
            }`} />
            <span className={`text-sm font-medium ${
              materialType === 'video' ? 'text-primary-600' : 'text-gray-600'
            }`}>
              Video
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleTypeChange('link')}
            className={`p-4 rounded-lg border-2 transition duration-200 ${
              materialType === 'link'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <FiLink className={`h-6 w-6 mx-auto mb-2 ${
              materialType === 'link' ? 'text-primary-600' : 'text-gray-400'
            }`} />
            <span className={`text-sm font-medium ${
              materialType === 'link' ? 'text-primary-600' : 'text-gray-600'
            }`}>
              Link
            </span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              Material Information
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g., Chapter 1 Slides, Lecture Video, Reading Material"
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
                placeholder="Brief description of the material..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Week/Module
                </label>
                <input
                  type="text"
                  name="week"
                  value={formData.week}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="e.g., Week 1, Module 2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Topic
                </label>
                <input
                  type="text"
                  name="topic"
                  value={formData.topic}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="e.g., Introduction, Arrays, Variables"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g., lecture, reading, exam, separated by commas"
              />
            </div>
          </div>

          {/* File/Link Upload */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">
              {materialType === 'link' || materialType === 'video' ? 'URL' : 'Files'}
            </h2>

            {materialType === 'link' || materialType === 'video' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {materialType === 'video' ? 'Video URL' : 'Link URL'} <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <FiLink className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="url"
                    name="url"
                    value={formData.url}
                    onChange={handleChange}
                    className="pl-10 input-field"
                    placeholder={materialType === 'video' 
                      ? "https://youtube.com/watch?v=..." 
                      : "https://example.com/document"}
                    required
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {materialType === 'video' 
                    ? 'Supports YouTube, Vimeo, and other video platforms'
                    : 'Enter the full URL including https://'}
                </p>
              </div>
            ) : (
              <>
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
                        PDF, PPT, Video, Images, ZIP (Max 100MB)
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
              </>
            )}
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
              disabled={loading || !formData.title || (materialType !== 'link' && materialType !== 'video' && files.length === 0)}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  Upload Material
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UploadMaterial;