import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiPlus, FiEdit2, FiTrash2, FiSave, FiX,
  FiArrowLeft, FiFilter, FiSearch
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminSubjects = () => {
  const [searchParams] = useSearchParams();
  const courseFilter = searchParams.get('course');
  const editId = searchParams.get('edit');

  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [filteredSubjects, setFilteredSubjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCourse, setSelectedCourse] = useState(courseFilter || '');
  const [selectedSemester, setSelectedSemester] = useState('');
  
  const [formData, setFormData] = useState({
    course_id: courseFilter || '',
    code: '',
    name: '',
    description: '',
    credits: 3,
    semester: '',
    is_active: true
  });

  useEffect(() => {
    fetchCourses();
    fetchSubjects();
  }, []);

  useEffect(() => {
    if (editId && subjects.length > 0) {
      const subject = subjects.find(s => s.id === parseInt(editId));
      if (subject) {
        handleEdit(subject);
      }
    }
  }, [editId, subjects]);

  useEffect(() => {
    filterSubjects();
  }, [subjects, selectedCourse, selectedSemester, searchTerm]);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/courses/');
      setCourses(response.data.courses || []);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      toast.error('Failed to load courses');
    }
  };

  const fetchSubjects = async () => {
    try {
      const response = await api.get('/subjects/');
      setSubjects(response.data.subjects || []);
    } catch (error) {
      console.error('Failed to fetch subjects:', error);
      toast.error('Failed to load subjects');
    } finally {
      setLoading(false);
    }
  };

  const filterSubjects = () => {
    let filtered = [...subjects];

    // Filter by course
    if (selectedCourse) {
      filtered = filtered.filter(s => s.course_id === parseInt(selectedCourse));
    }

    // Filter by semester
    if (selectedSemester) {
      filtered = filtered.filter(s => s.semester === parseInt(selectedSemester));
    }

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(term) ||
        s.code.toLowerCase().includes(term) ||
        s.course_name?.toLowerCase().includes(term)
      );
    }

    setFilteredSubjects(filtered);
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
      course_id: courseFilter || '',
      code: '',
      name: '',
      description: '',
      credits: 3,
      semester: '',
      is_active: true
    });
    setEditingSubject(null);
    setShowForm(false);
  };

  const handleEdit = (subject) => {
    setEditingSubject(subject);
    setFormData({
      course_id: subject.course_id,
      code: subject.code || '',
      name: subject.name || '',
      description: subject.description || '',
      credits: subject.credits || 3,
      semester: subject.semester || '',
      is_active: subject.is_active === 1 || subject.is_active === true
    });
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.course_id || !formData.code || !formData.name) {
      toast.error('Course, code and name are required');
      return;
    }

    setLoading(true);

    try {
      if (editingSubject) {
        // Update existing subject
        await api.put(`/subjects/${editingSubject.id}`, formData);
        toast.success('Subject updated successfully');
      } else {
        // Create new subject
        await api.post('/subjects/', formData);
        toast.success('Subject created successfully');
      }
      
      resetForm();
      fetchSubjects();
    } catch (error) {
      console.error('Failed to save subject:', error);
      toast.error(error.response?.data?.error || 'Failed to save subject');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (subjectId, subjectName) => {
    if (!window.confirm(`Are you sure you want to delete "${subjectName}"?`)) {
      return;
    }

    try {
      await api.delete(`/subjects/${subjectId}`);
      toast.success('Subject deleted successfully');
      fetchSubjects();
    } catch (error) {
      console.error('Failed to delete subject:', error);
      toast.error(error.response?.data?.error || 'Failed to delete subject');
    }
  };

  const semesters = [1, 2, 3, 4, 5, 6, 7, 8];

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div className="flex items-center">
            <Link
              to="/admin/courses"
              className="mr-4 text-gray-400 hover:text-gray-600"
            >
              <FiArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <FiBook className="mr-2 text-primary-600" />
                Subject Management
              </h1>
              <p className="text-gray-600 mt-1">
                Manage subjects/classes under each course
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="mt-4 md:mt-0 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
          >
            <FiPlus className="mr-2" />
            Add New Subject
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingSubject ? 'Edit Subject' : 'Create New Subject'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Course <span className="text-red-500">*</span>
                </label>
                <select
                  name="course_id"
                  value={formData.course_id}
                  onChange={handleInputChange}
                  className="input-field"
                  required
                >
                  <option value="">-- Select Course --</option>
                  {courses.map(course => (
                    <option key={course.id} value={course.id}>
                      {course.code} - {course.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., CS101"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., Introduction to Programming"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Semester
                </label>
                <select
                  name="semester"
                  value={formData.semester}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  <option value="">-- Select Semester --</option>
                  {semesters.map(s => (
                    <option key={s} value={s}>Semester {s}</option>
                  ))}
                </select>
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
                  min="1"
                  max="6"
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
                placeholder="Subject description..."
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
                {editingSubject ? 'Update Subject' : 'Create Subject'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search subjects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field w-full"
            />
          </div>

          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="input-field"
          >
            <option value="">All Courses</option>
            {courses.map(course => (
              <option key={course.id} value={course.id}>
                {course.code} - {course.name}
              </option>
            ))}
          </select>

          <select
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
            className="input-field"
          >
            <option value="">All Semesters</option>
            {semesters.map(s => (
              <option key={s} value={s}>Semester {s}</option>
            ))}
          </select>

          <button
            onClick={() => {
              setSelectedCourse('');
              setSelectedSemester('');
              setSearchTerm('');
            }}
            className="btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Subjects List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            All Subjects ({filteredSubjects.length})
          </h2>
        </div>

        {filteredSubjects.length === 0 ? (
          <div className="p-12 text-center">
            <FiBook className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No subjects found</h3>
            <p className="mt-2 text-gray-500">Try adjusting your filters or add a new subject.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subject Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Course
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Semester
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credits
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSubjects.map((subject) => (
                  <tr key={subject.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {subject.code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {subject.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {subject.course_code} - {subject.course_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {subject.semester ? `Semester ${subject.semester}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {subject.credits || 3}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        subject.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {subject.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(subject)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        <FiEdit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(subject.id, subject.name)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <FiTrash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminSubjects;