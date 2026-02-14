import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  FiBook, FiClock, FiCheckCircle, FiAlertCircle,
  FiCalendar, FiUsers, FiFileText, FiVideo,
  FiChevronRight, FiAward, FiUser, FiMapPin
} from 'react-icons/fi';
import Loader from '../common/Loader';  
import toast from 'react-hot-toast';

const StudentDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    enrolled_sections: [],
    pending_requests: [],
    upcoming_assignments: [],
    recent_grades: [],
    attendance_summary: {}
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [sectionsRes, pendingRes, assignmentsRes, gradesRes] = await Promise.all([
        api.get('/student/sections'),
        api.get('/student/enrollments/pending'),
        api.get('/student/assignments/upcoming'),
        api.get('/student/grades/recent')
      ]);

      setDashboardData({
        enrolled_sections: sectionsRes.data.sections || [],
        pending_requests: pendingRes.data.enrollments || [],
        upcoming_assignments: assignmentsRes.data.assignments || [],
        recent_grades: gradesRes.data.grades || []
      });
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader />;

  const totalEnrolled = dashboardData.enrolled_sections.length;
  const pendingCount = dashboardData.pending_requests.length;
  const upcomingCount = dashboardData.upcoming_assignments.length;

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-3xl font-bold">Welcome back, {user?.name?.split(' ')[0]}! 👋</h1>
        <p className="mt-2 text-primary-100">Track your enrolled sections, assignments, and grades</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Enrolled Sections</p>
              <p className="text-3xl font-bold text-gray-900">{totalEnrolled}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <FiBook className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Pending Requests</p>
              <p className="text-3xl font-bold text-yellow-600">{pendingCount}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <FiClock className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Upcoming Assignments</p>
              <p className="text-3xl font-bold text-gray-900">{upcomingCount}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <FiFileText className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Average Grade</p>
              <p className="text-3xl font-bold text-green-600">85%</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <FiAward className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Pending Enrollment Requests */}
      {dashboardData.pending_requests.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-yellow-800 mb-3 flex items-center">
            <FiClock className="mr-2" />
            Pending Enrollment Requests ({pendingCount})
          </h2>
          <div className="space-y-2">
            {dashboardData.pending_requests.map((request) => (
              <div key={request.id} className="bg-white p-3 rounded-lg flex justify-between items-center">
                <div>
                  <p className="font-medium text-gray-900">{request.subject_name}</p>
                  <p className="text-sm text-gray-600">{request.course_name} • Section {request.section_name}</p>
                </div>
                <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full">
                  Waiting for approval
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Enrolled Sections */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">My Enrolled Sections</h2>
          <Link to="/student/available-sections" className="text-primary-600 hover:text-primary-700 text-sm flex items-center">
            Browse More <FiChevronRight className="ml-1" />
          </Link>
        </div>

        {dashboardData.enrolled_sections.length === 0 ? (
          <div className="text-center py-8">
            <FiBook className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-500">You're not enrolled in any sections yet</p>
            <Link to="/student/available-sections" className="mt-4 inline-block btn-primary">
              Browse Available Sections
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dashboardData.enrolled_sections.map((section) => (
              <Link
                key={section.section_id}
                 to={`/student/section/${section.section_id}`}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-gray-900">{section.subject_name}</h3>
                    <p className="text-sm text-gray-600">{section.course_name} • Section {section.section_name}</p>
                  </div>
                  <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                    {section.schedule?.day || 'Schedule TBA'}
                  </span>
                </div>
                <div className="mt-3 flex items-center text-sm text-gray-500">
                  <FiUser className="mr-1" />
                  <span>{section.teacher_name}</span>
                  {section.room && (
                    <>
                      <FiMapPin className="ml-3 mr-1" />
                      <span>Room {section.room}</span>
                    </>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Assignments */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">📝 Upcoming Assignments</h2>
        
        {dashboardData.upcoming_assignments.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No upcoming assignments</p>
        ) : (
          <div className="space-y-3">
            {dashboardData.upcoming_assignments.map((assignment) => (
              <div key={assignment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{assignment.title}</p>
                  <p className="text-sm text-gray-600">{assignment.subject_name}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium text-red-600">
                    Due: {new Date(assignment.due_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;