import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiFile, FiDownload, FiTrash2, FiLink, 
  FiYoutube, FiFileText, FiVideo, FiImage 
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import Loader from '../common/Loader';

const MaterialsList = () => {
  const { classId } = useParams();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMaterials();
  }, [classId]);

  const fetchMaterials = async () => {
    try {
      const response = await api.get(`/materials/class/${classId}`);
      setMaterials(response.data.materials || []);
    } catch (error) {
      console.error('Failed to fetch materials:', error);
      toast.error('Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  const deleteMaterial = async (materialId, title) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }

    try {
      await api.delete(`/materials/${materialId}`);
      toast.success('Material deleted successfully');
      fetchMaterials();
    } catch (error) {
      console.error('Failed to delete material:', error);
      toast.error('Failed to delete material');
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'pdf':
        return <FiFileText className="h-5 w-5 text-red-500" />;
      case 'ppt':
      case 'presentation':
        return <FiFile className="h-5 w-5 text-orange-500" />;
      case 'video':
        return <FiVideo className="h-5 w-5 text-blue-500" />;
      case 'link':
        return <FiLink className="h-5 w-5 text-green-500" />;
      case 'youtube':
        return <FiYoutube className="h-5 w-5 text-red-600" />;
      case 'image':
        return <FiImage className="h-5 w-5 text-purple-500" />;
      default:
        return <FiFile className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const groupedByWeek = materials.reduce((acc, material) => {
    const week = material.week || 'Uncategorized';
    if (!acc[week]) acc[week] = [];
    acc[week].push(material);
    return acc;
  }, {});

  if (loading) return <Loader />;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900">📚 Study Materials</h2>
        <Link
          to={`/teacher/class/${classId}/upload-material`}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
        >
          <FiFile className="mr-2" />
          Upload Material
        </Link>
      </div>

      {Object.keys(groupedByWeek).length === 0 ? (
        <div className="text-center py-12">
          <FiFile className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No materials yet</h3>
          <p className="mt-2 text-gray-500">Upload study materials for your students</p>
          <Link
            to={`/teacher/class/${classId}/upload-material`}
            className="mt-4 inline-block btn-primary"
          >
            Upload First Material
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedByWeek).map(([week, items]) => (
            <div key={week}>
              <h3 className="text-lg font-semibold text-gray-800 mb-3 bg-gray-50 p-2 rounded">
                {week === 'Uncategorized' ? '📁 Other Materials' : `📅 ${week}`}
              </h3>
              <div className="space-y-2">
                {items.map((material) => (
                  <div
                    key={material.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition duration-200"
                  >
                    <div className="flex items-center flex-1">
                      {getIcon(material.type)}
                      <div className="ml-3 flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{material.title}</h4>
                        <div className="flex items-center mt-1 text-xs text-gray-500">
                          <span>{material.topic && `Topic: ${material.topic}`}</span>
                          {material.file_size && (
                            <span className="ml-2">• {formatFileSize(material.file_size)}</span>
                          )}
                          {material.download_count > 0 && (
                            <span className="ml-2">• {material.download_count} downloads</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {material.file_path && (
                        <a
                          href={`http://127.0.0.1:5000${material.file_path}`}
                          download
                          className="p-2 text-gray-600 hover:text-primary-600 rounded-full hover:bg-white"
                          title="Download"
                        >
                          <FiDownload className="h-4 w-4" />
                        </a>
                      )}
                      {material.url && (
                        <a
                          href={material.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-gray-600 hover:text-primary-600 rounded-full hover:bg-white"
                          title="Open Link"
                        >
                          <FiLink className="h-4 w-4" />
                        </a>
                      )}
                      <button
                        onClick={() => deleteMaterial(material.id, material.title)}
                        className="p-2 text-gray-600 hover:text-red-600 rounded-full hover:bg-white"
                        title="Delete"
                      >
                        <FiTrash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MaterialsList;