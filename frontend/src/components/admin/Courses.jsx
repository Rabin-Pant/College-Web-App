import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiPlus, FiEdit2, FiTrash2, FiSave, FiX,
  FiChevronDown, FiChevronUp, FiEye, FiEyeOff
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminCourses = () => {
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [expandedCourse, setExpandedCourse] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    department: '',
    duration: '',
    credits: '',
    is_active: true
  });

  useEffect(() => {
    fetchCourses();
    fetchSubjects();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/courses/');
      setCourses(response.data.courses || []);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      toast.error('Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const response = await api.get('/subjects/');
      setSubjects(response.data.subjects || []);
    } catch (error) {
      console.error('Failed to fetch subjects:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      description: '',
      department: '',
      duration: '',
      credits: '',
      is_active: true
    });
    setEditingCourse(null);
    setShowForm(false);
  };

  const handleEdit = (course) => {
    setEditingCourse(course);
    setFormData({
      name: course.name || '',
      code: course.code || '',
      description: course.description || '',
      department: course.department || '',
      duration: course.duration || '',
      credits: course.credits || '',
      is_active: course.is_active === 1 || course.is_active === true
    });
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code) {
      toast.error('Name and code are required');
      return;
    }

    setLoading(true);

    try {
      if (editingCourse) {
        // Update existing course
        await api.put(`/courses/${editingCourse.id}`, formData);
        toast.success('Course updated successfully');
      } else {
        // Create new course
        await api.post('/courses/', formData);
        toast.success('Course created successfully');
      }
      
      resetForm();
      fetchCourses();
    } catch (error) {
      console.error('Failed to save course:', error);
      toast.error(error.response?.data?.error || 'Failed to save course');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (courseId, courseName) => {
    if (!window.confirm(`Are you sure you want to delete "${courseName}"?\n\nThis will also delete all subjects under this course!`)) {
      return;
    }

    try {
      await api.delete(`/courses/${courseId}`);
      toast.success('Course deleted successfully');
      fetchCourses();
      if (expandedCourse === courseId) {
        setExpandedCourse(null);
      }
    } catch (error) {
      console.error('Failed to delete course:', error);
      toast.error(error.response?.data?.error || 'Failed to delete course');
    }
  };

  const toggleExpand = (courseId) => {
    setExpandedCourse(expandedCourse === courseId ? null : courseId);
  };

  const getCourseSubjects = (courseId) => {
    return subjects.filter(s => s.course_id === courseId);
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <FiBook className="mr-2 text-primary-600" />
              Course Management
            </h1>
            <p className="text-gray-600 mt-1">
              Manage academic programs and their subjects
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="mt-4 md:mt-0 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
          >
            <FiPlus className="mr-2" />
            Add New Course
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingCourse ? 'Edit Course' : 'Create New Course'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Course Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., Artificial Intelligence"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Course Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., AI"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Department
                </label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., Computing"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration
                </label>
                <input
                  type="text"
                  name="duration"
                  value={formData.duration}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., 4 years"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Credits
                </label>
                <input
                  type="number"
                  name="credits"
                  value={formData.credits}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., 120"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">
                  Active (visible to teachers)
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className="input-field"
                placeholder="Course description..."
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center"
              >
                <FiX className="mr-2" />
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
              >
                <FiSave className="mr-2" />
                {editingCourse ? 'Update Course' : 'Create Course'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Courses List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">All Courses</h2>
        </div>

        {courses.length === 0 ? (
          <div className="p-12 text-center">
            <FiBook className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No courses yet</h3>
            <p className="mt-2 text-gray-500">Click "Add New Course" to create your first course.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {courses.map((course) => {
              const courseSubjects = getCourseSubjects(course.id);
              const isExpanded = expandedCourse === course.id;
              
              return (
                <div key={course.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <button
                          onClick={() => toggleExpand(course.id)}
                          className="mr-2 text-gray-400 hover:text-gray-600"
                        >
                          {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                        </button>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {course.name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Code: {course.code} | Department: {course.department || 'N/A'} | 
                            Credits: {course.credits || 'N/A'} | Duration: {course.duration || 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/admin/subjects?course=${course.id}`}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Manage Subjects"
                      >
                        <FiBook className="h-5 w-5" />
                      </Link>
                      <button
                        onClick={() => handleEdit(course)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                        title="Edit Course"
                      >
                        <FiEdit2 className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(course.id, course.name)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                        title="Delete Course"
                      >
                        <FiTrash2 className="h-5 w-5" />
                      </button>
                      <span className={`ml-2 px-2 py-1 text-xs font-semibold rounded-full ${
                        course.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {course.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>

                  {/* Subjects List */}
                  {isExpanded && (
                    <div className="mt-4 ml-8">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Subjects ({courseSubjects.length})
                      </h4>
                      {courseSubjects.length === 0 ? (
                        <p className="text-sm text-gray-500">No subjects added yet.</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {courseSubjects.map((subject) => (
                            <div
                              key={subject.id}
                              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                            >
                              <div>
                                <p className="text-sm font-medium text-gray-900">
                                  {subject.code} - {subject.name}
                                </p>
                                <p className="text-xs text-gray-500">
                                  Semester {subject.semester || 'N/A'} | {subject.credits} credits
                                </p>
                              </div>
                              <Link
                                to={`/admin/subjects?edit=${subject.id}`}
                                className="text-primary-600 hover:text-primary-700"
                              >
                                <FiEdit2 className="h-4 w-4" />
                              </Link>
                            </div>
                          ))}
                        </div>
                      )}
                      <Link
                        to={`/admin/subjects?course=${course.id}`}
                        className="mt-3 inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
                      >
                        <FiPlus className="mr-1" />
                        Add Subject to {course.code}
                      </Link>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminCourses;