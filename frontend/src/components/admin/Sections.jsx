import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiPlus, FiEdit2, FiTrash2, FiSave, FiX,
  FiUsers, FiCalendar, FiMapPin, FiFilter, FiSearch,
  FiChevronDown, FiChevronUp
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminSections = () => {
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState([]);
  const [courses, setCourses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [filteredSubjects, setFilteredSubjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingSection, setEditingSection] = useState(null);
  const [filters, setFilters] = useState({
    course_id: '',
    academic_year: '',
    semester: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  const [formData, setFormData] = useState({
    subject_id: '',
    name: '',
    academic_year: '2024-2025',
    semester: 'Fall 2024',
    capacity: 30,
    room: '',
    is_active: true
  });

  const academicYears = ['2024-2025', '2025-2026', '2026-2027', '2027-2028'];
  const semesters = ['Fall 2024', 'Spring 2025', 'Fall 2025', 'Spring 2026', 'Fall 2026'];

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (formData.course_id) {
      const filtered = subjects.filter(s => s.course_id === parseInt(formData.course_id));
      setFilteredSubjects(filtered);
      setFormData(prev => ({ ...prev, subject_id: '' }));
    } else {
      setFilteredSubjects([]);
    }
  }, [formData.course_id, subjects]);

  const fetchData = async () => {
    try {
      const [sectionsRes, coursesRes, subjectsRes] = await Promise.all([
        api.get('/admin/sections'),
        api.get('/admin/courses'),
        api.get('/admin/subjects')
      ]);
      
      setSections(sectionsRes.data.sections || []);
      setCourses(coursesRes.data.courses || []);
      setSubjects(subjectsRes.data.subjects || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load sections');
    } finally {
      setLoading(false);
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
      subject_id: '',
      name: '',
      academic_year: '2024-2025',
      semester: 'Fall 2024',
      capacity: 30,
      room: '',
      is_active: true
    });
    setEditingSection(null);
    setShowForm(false);
  };

  const handleEdit = (section) => {
    setEditingSection(section);
    setFormData({
      subject_id: section.subject_id,
      name: section.section_name,
      academic_year: section.academic_year,
      semester: section.academic_semester,
      capacity: section.capacity,
      room: section.room || '',
      is_active: section.is_active === 1 || section.is_active === true
    });
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.subject_id || !formData.name) {
      toast.error('Subject and section name are required');
      return;
    }

    setLoading(true);

    try {
      if (editingSection) {
        await api.put(`/admin/sections/${editingSection.section_id}`, formData);
        toast.success('Section updated successfully');
      } else {
        await api.post('/admin/sections', formData);
        toast.success('Section created successfully');
      }
      
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Failed to save section:', error);
      toast.error(error.response?.data?.error || 'Failed to save section');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sectionId, sectionName) => {
    if (!window.confirm(`Are you sure you want to delete Section ${sectionName}?`)) {
      return;
    }

    try {
      await api.delete(`/admin/sections/${sectionId}`);
      toast.success('Section deleted successfully');
      fetchData();
    } catch (error) {
      console.error('Failed to delete section:', error);
      toast.error(error.response?.data?.error || 'Cannot delete section with enrolled students');
    }
  };

  const filteredSections = sections.filter(section => {
    let matches = true;

    if (filters.course_id) {
      matches = matches && section.course_id === parseInt(filters.course_id);
    }
    if (filters.academic_year) {
      matches = matches && section.academic_year === filters.academic_year;
    }
    if (filters.semester) {
      matches = matches && section.academic_semester === filters.semester;
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      matches = matches && (
        section.subject_name?.toLowerCase().includes(term) ||
        section.subject_code?.toLowerCase().includes(term) ||
        section.section_name?.toLowerCase().includes(term) ||
        section.course_name?.toLowerCase().includes(term) ||
        section.teachers?.toLowerCase().includes(term)
      );
    }

    return matches;
  });

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <FiBook className="mr-2 text-primary-600" />
              Section Management
            </h1>
            <p className="text-gray-600 mt-1">
              Create and manage class sections with capacity and rooms
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="mt-4 md:mt-0 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
          >
            <FiPlus className="mr-2" />
            Create New Section
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingSection ? 'Edit Section' : 'Create New Section'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Course
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
                  Subject
                </label>
                <select
                  name="subject_id"
                  value={formData.subject_id}
                  onChange={handleInputChange}
                  className="input-field"
                  required
                  disabled={!formData.course_id}
                >
                  <option value="">-- Select Subject --</option>
                  {filteredSubjects.map(subject => (
                    <option key={subject.id} value={subject.id}>
                      {subject.code} - {subject.name} (Sem {subject.semester})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Section Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., A, B, C"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Academic Year
                </label>
                <select
                  name="academic_year"
                  value={formData.academic_year}
                  onChange={handleInputChange}
                  className="input-field"
                  required
                >
                  {academicYears.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
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
                  required
                >
                  {semesters.map(sem => (
                    <option key={sem} value={sem}>{sem}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Capacity
                </label>
                <input
                  type="number"
                  name="capacity"
                  value={formData.capacity}
                  onChange={handleInputChange}
                  className="input-field"
                  min="1"
                  max="200"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Room
                </label>
                <input
                  type="text"
                  name="room"
                  value={formData.room}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="e.g., 101, Lab 2"
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
                  Active (available for enrollment)
                </label>
              </div>
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
                {editingSection ? 'Update Section' : 'Create Section'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative md:col-span-2">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search sections..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field w-full"
            />
          </div>

          <select
            value={filters.course_id}
            onChange={(e) => setFilters({ ...filters, course_id: e.target.value })}
            className="input-field"
          >
            <option value="">All Courses</option>
            {courses.map(course => (
              <option key={course.id} value={course.id}>
                {course.code}
              </option>
            ))}
          </select>

          <select
            value={filters.academic_year}
            onChange={(e) => setFilters({ ...filters, academic_year: e.target.value })}
            className="input-field"
          >
            <option value="">All Years</option>
            {academicYears.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>

          <select
            value={filters.semester}
            onChange={(e) => setFilters({ ...filters, semester: e.target.value })}
            className="input-field"
          >
            <option value="">All Semesters</option>
            {semesters.map(sem => (
              <option key={sem} value={sem}>{sem}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Sections Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Section</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Course</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Semester</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Capacity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enrolled</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teacher</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Room</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSections.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-6 py-12 text-center">
                    <FiBook className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-gray-500">No sections found</p>
                  </td>
                </tr>
              ) : (
                filteredSections.map((section) => (
                  <tr key={section.section_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        Section {section.section_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {section.course_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{section.subject_code}</div>
                      <div className="text-xs text-gray-500">{section.subject_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {section.academic_semester}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {section.capacity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        section.enrolled_count >= section.capacity 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {section.enrolled_count || 0}/{section.capacity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {section.teachers || 'Not Assigned'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {section.room || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(section)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        <FiEdit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(section.section_id, section.section_name)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <FiTrash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminSections;