import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  FiUsers, FiPlus, FiTrash2, FiUserCheck,
  FiFilter, FiSearch, FiBook, FiCheck
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminTeacherAssignments = () => {
  const [loading, setLoading] = useState(true);
  const [assignments, setAssignments] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [unassignedSections, setUnassignedSections] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    teacher_id: '',
    section_id: '',
    is_primary: true
  });
  const [filters, setFilters] = useState({
    academic_year: '',
    semester: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  const academicYears = ['2024-2025', '2025-2026', '2026-2027'];
  const semesters = ['Fall 2024', 'Spring 2025', 'Fall 2025', 'Spring 2026'];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [assignmentsRes, teachersRes, sectionsRes] = await Promise.all([
        api.get('/admin/teacher-assignments'),
        api.get('/admin/teacher-assignments/teachers'),
        api.get('/admin/teacher-assignments/unassigned-sections', { params: filters })
      ]);
      
      setAssignments(assignmentsRes.data.assignments || []);
      setTeachers(teachersRes.data.teachers || []);
      setUnassignedSections(sectionsRes.data.sections || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (filters.academic_year || filters.semester) {
      fetchUnassignedSections();
    }
  }, [filters]);

  const fetchUnassignedSections = async () => {
    try {
      const response = await api.get('/admin/teacher-assignments/unassigned-sections', { params: filters });
      setUnassignedSections(response.data.sections || []);
    } catch (error) {
      console.error('Failed to fetch unassigned sections:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.teacher_id || !formData.section_id) {
      toast.error('Please select both teacher and section');
      return;
    }

    try {
      await api.post('/admin/teacher-assignments', formData);
      toast.success('Teacher assigned successfully');
      setFormData({ teacher_id: '', section_id: '', is_primary: true });
      setShowForm(false);
      fetchData();
    } catch (error) {
      console.error('Failed to assign teacher:', error);
      toast.error(error.response?.data?.error || 'Failed to assign teacher');
    }
  };

  const handleRemove = async (assignmentId) => {
    if (!window.confirm('Remove this teacher assignment?')) return;

    try {
      await api.delete(`/admin/teacher-assignments/${assignmentId}`);
      toast.success('Assignment removed');
      fetchData();
    } catch (error) {
      console.error('Failed to remove assignment:', error);
      toast.error('Failed to remove assignment');
    }
  };

  const filteredAssignments = assignments.filter(assignment => {
    let matches = true;

    if (filters.academic_year) {
      matches = matches && assignment.academic_year === filters.academic_year;
    }
    if (filters.semester) {
      matches = matches && assignment.academic_semester === filters.semester;
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      matches = matches && (
        assignment.teacher_name?.toLowerCase().includes(term) ||
        assignment.subject_name?.toLowerCase().includes(term) ||
        assignment.course_name?.toLowerCase().includes(term)
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
              <FiUserCheck className="mr-2 text-primary-600" />
              Teacher Assignments
            </h1>
            <p className="text-gray-600 mt-1">
              Assign teachers to course sections
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="mt-4 md:mt-0 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
          >
            <FiPlus className="mr-2" />
            New Assignment
          </button>
        </div>
      </div>

      {/* Assignment Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Assign Teacher to Section</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Teacher
                </label>
                <select
                  name="teacher_id"
                  value={formData.teacher_id}
                  onChange={handleInputChange}
                  className="input-field"
                  required
                >
                  <option value="">-- Choose Teacher --</option>
                  {teachers.map(teacher => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name} - {teacher.department} ({teacher.employee_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Section
                </label>
                <select
                  name="section_id"
                  value={formData.section_id}
                  onChange={handleInputChange}
                  className="input-field"
                  required
                >
                  <option value="">-- Choose Section --</option>
                  {unassignedSections.map(section => (
                    <option key={section.id} value={section.id}>
                      {section.course_name} - {section.subject_code} ({section.subject_name}) - Section {section.name}
                    </option>
                  ))}
                </select>
                {unassignedSections.length === 0 && (
                  <p className="mt-1 text-xs text-yellow-600">
                    No unassigned sections available
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="is_primary"
                checked={formData.is_primary}
                onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label className="ml-2 text-sm text-gray-700">
                Primary Instructor
              </label>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center"
              >
                <FiCheck className="mr-2" />
                Assign Teacher
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative md:col-span-2">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by teacher, subject, course..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field w-full"
            />
          </div>

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

      {/* Assignments Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teacher</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Course</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Section</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Semester</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Students</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAssignments.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center">
                    <FiUsers className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-gray-500">No assignments found</p>
                  </td>
                </tr>
              ) : (
                filteredAssignments.map((assignment) => (
                  <tr key={assignment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                          <FiUserCheck className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{assignment.teacher_name}</p>
                          <p className="text-xs text-gray-500">{assignment.employee_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {assignment.course_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-sm font-medium text-gray-900">{assignment.subject_code}</p>
                      <p className="text-xs text-gray-500">{assignment.subject_name}</p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Section {assignment.section_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {assignment.academic_semester}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {assignment.enrolled_count || 0}/{assignment.capacity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        assignment.is_primary 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {assignment.is_primary ? 'Primary' : 'Assistant'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleRemove(assignment.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Remove Assignment"
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

export default AdminTeacherAssignments;