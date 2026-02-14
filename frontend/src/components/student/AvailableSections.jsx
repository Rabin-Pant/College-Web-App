import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  FiBook, FiUsers, FiClock, FiCalendar, 
  FiMapPin, FiUser, FiFilter, FiSearch,
  FiCheckCircle, FiXCircle, FiAlertCircle
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AvailableSections = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState([]);
  const [filteredSections, setFilteredSections] = useState([]);
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [pendingRequests, setPendingRequests] = useState([]);

  const semesters = ['Fall 2024', 'Spring 2025', 'Fall 2025', 'Spring 2026'];

  useEffect(() => {
    fetchData();
    fetchPendingRequests();
  }, []);

  useEffect(() => {
    filterSections();
  }, [sections, selectedCourse, selectedSemester, searchTerm]);

  const fetchData = async () => {
    try {
      // ✅ FIXED: Use the correct student endpoint
      const [sectionsRes, coursesRes] = await Promise.all([
        api.get('/student/sections/available'),  // Changed from /sections/available
        api.get('/courses/')
      ]);
      
      setSections(sectionsRes.data.sections || []);
      setFilteredSections(sectionsRes.data.sections || []);
      setCourses(coursesRes.data.courses || []);
    } catch (error) {
      console.error('Failed to fetch sections:', error);
      toast.error('Failed to load available sections');
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingRequests = async () => {
    try {
      // ✅ FIXED: Use the correct student endpoint
      const response = await api.get('/student/enrollments/pending');
      setPendingRequests(response.data.enrollments || []);
    } catch (error) {
      console.error('Failed to fetch pending requests:', error);
    }
  };

  const filterSections = () => {
    let filtered = [...sections];

    if (selectedCourse) {
      filtered = filtered.filter(s => s.course_id === parseInt(selectedCourse));
    }

    if (selectedSemester) {
      filtered = filtered.filter(s => s.semester === selectedSemester);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.subject_name?.toLowerCase().includes(term) ||
        s.subject_code?.toLowerCase().includes(term) ||
        s.course_name?.toLowerCase().includes(term) ||
        s.teacher_name?.toLowerCase().includes(term)
      );
    }

    setFilteredSections(filtered);
  };

  const requestEnrollment = async (sectionId) => {
    try {
      await api.post('/student/enrollments', { section_id: sectionId });
      toast.success('Enrollment request sent! Waiting for approval.');
      fetchPendingRequests();
      fetchData(); // Refresh available seats
    } catch (error) {
      console.error('Failed to request enrollment:', error);
      toast.error(error.response?.data?.error || 'Failed to request enrollment');
    }
  };

  const isPending = (sectionId) => {
    return pendingRequests.some(r => r.section_id === sectionId);
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold">Available Sections</h1>
        <p className="mt-2 text-primary-100">Browse and request enrollment in available classes</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by subject, code, teacher..."
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
            {semesters.map(sem => (
              <option key={sem} value={sem}>{sem}</option>
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

      {/* Sections Grid */}
      {filteredSections.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FiBook className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No sections available</h3>
          <p className="mt-2 text-gray-500">Check back later for new sections</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSections.map((section) => (
            <div key={section.section_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition">
              <div className="h-32 bg-gradient-to-r from-primary-600 to-primary-800 p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-white">{section.subject_code}</h3>
                    <p className="text-primary-100">{section.subject_name}</p>
                  </div>
                  <span className="bg-white text-primary-600 px-2 py-1 rounded text-xs font-semibold">
                    {section.credits} credits
                  </span>
                </div>
              </div>
              
              <div className="p-4 space-y-3">
                <div className="flex items-center text-sm text-gray-600">
                  <FiBook className="mr-2" />
                  <span>{section.course_name}</span>
                </div>
                
                <div className="flex items-center text-sm text-gray-600">
                  <FiUser className="mr-2" />
                  <span>{section.teacher_name || 'TBA'}</span>
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <FiCalendar className="mr-2" />
                  <span>{section.semester}</span>
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <FiUsers className="mr-2" />
                  <span>
                    {section.enrolled_count}/{section.capacity} students
                    {section.available_seats > 0 && (
                      <span className="ml-2 text-green-600 font-semibold">
                        ({section.available_seats} seats left)
                      </span>
                    )}
                  </span>
                </div>

                {section.room && (
                  <div className="flex items-center text-sm text-gray-600">
                    <FiMapPin className="mr-2" />
                    <span>Room {section.room}</span>
                  </div>
                )}

                <div className="pt-4">
                  {isPending(section.section_id) ? (
                    <button
                      disabled
                      className="w-full bg-yellow-100 text-yellow-700 px-4 py-2 rounded-lg font-medium flex items-center justify-center"
                    >
                      <FiClock className="mr-2" />
                      Pending Approval
                    </button>
                  ) : section.available_seats > 0 ? (
                    <button
                      onClick={() => requestEnrollment(section.section_id)}
                      className="w-full btn-primary flex items-center justify-center"
                    >
                      <FiCheckCircle className="mr-2" />
                      Request Enrollment
                    </button>
                  ) : (
                    <button
                      disabled
                      className="w-full bg-gray-100 text-gray-500 px-4 py-2 rounded-lg font-medium flex items-center justify-center cursor-not-allowed"
                    >
                      <FiXCircle className="mr-2" />
                      Section Full
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AvailableSections;