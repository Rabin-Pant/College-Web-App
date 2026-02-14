import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  FiBook, FiUsers, FiClipboard, FiClock, 
  FiPlus, FiCalendar, FiUserCheck, FiVideo,
  FiChevronRight, FiBell
} from 'react-icons/fi';
import Loader from '../common/Loader';
import SendNotificationModal from '../notifications/SendNotificationModal';

const TeacherDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    assigned_sections: [],
    total_students: 0,
    pending_enrollments: [],
    upcoming_meetings: [],
    pending_grading: []
  });
  const [showSendModal, setShowSendModal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [sectionsRes, statsRes, pendingRes, meetingsRes, gradingRes] = await Promise.all([
        api.get('/teacher/sections/'),
        api.get('/teacher/sections/stats'),
        api.get('/teacher/enrollments/pending'),
        api.get('/teacher/zoom/upcoming'),
        api.get('/teacher/grading/pending')
      ]);

      setDashboardData({
        assigned_sections: sectionsRes.data.sections || [],
        total_students: statsRes.data.total_students || 0,
        pending_enrollments: pendingRes.data.enrollments || [],
        upcoming_meetings: meetingsRes.data.meetings || [],
        pending_grading: gradingRes.data.submissions || []
      });
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader />;

  const totalSections = dashboardData.assigned_sections.length;
  const pendingCount = dashboardData.pending_enrollments.length;
  const gradingCount = dashboardData.pending_grading.length;

  return (
    <div className="space-y-6">
      {/* Welcome Section with Send Notification Button */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-lg p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">Welcome back, {user?.name?.split(' ')[0]}! 👨‍🏫</h1>
            <p className="mt-2 text-primary-100">Manage your assigned sections and students</p>
          </div>
          <button
            onClick={() => setShowSendModal(true)}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 flex items-center"
          >
            <FiBell className="mr-2" />
            Send Notification
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Assigned Sections</p>
              <p className="text-3xl font-bold text-gray-900">{totalSections}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <FiBook className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Students</p>
              <p className="text-3xl font-bold text-gray-900">{dashboardData.total_students}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Pending Enrollments</p>
              <p className="text-3xl font-bold text-yellow-600">{pendingCount}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <FiUserCheck className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Pending Grading</p>
              <p className="text-3xl font-bold text-red-600">{gradingCount}</p>
            </div>
            <div className="bg-red-100 p-3 rounded-full">
              <FiClipboard className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Pending Enrollments */}
      {dashboardData.pending_enrollments.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-yellow-800 mb-3 flex items-center">
            <FiUserCheck className="mr-2" />
            Pending Enrollment Requests ({pendingCount})
          </h2>
          <div className="space-y-2">
            {dashboardData.pending_enrollments.map((request) => (
              <div key={request.id} className="bg-white p-3 rounded-lg flex justify-between items-center">
                <div>
                  <p className="font-medium text-gray-900">{request.student_name}</p>
                  <p className="text-sm text-gray-600">
                    {request.subject_name} • Section {request.section_name}
                  </p>
                </div>
                <Link
                  to={`/teacher/section/${request.section_id}`}
                  className="text-primary-600 hover:text-primary-700 text-sm"
                >
                  Review
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assigned Sections */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">📚 My Assigned Sections</h2>

        {dashboardData.assigned_sections.length === 0 ? (
          <div className="text-center py-8">
            <FiBook className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-500">No sections assigned yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboardData.assigned_sections.map((section) => (
              <Link
                key={section.section_id}
                to={`/teacher/section/${section.section_id}`}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-gray-900">{section.subject_name}</h3>
                    <p className="text-sm text-gray-600">{section.course_name}</p>
                  </div>
                  <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full">
                    Section {section.section_name}
                  </span>
                </div>
                <div className="mt-3 space-y-2">
                  <div className="flex items-center text-sm text-gray-500">
                    <FiUsers className="mr-2" />
                    <span>{section.enrolled_count}/{section.capacity} students</span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <FiClipboard className="mr-2" />
                    <span>{section.assignment_count || 0} assignments</span>
                  </div>
                  {section.room && (
                    <div className="flex items-center text-sm text-gray-500">
                      <FiCalendar className="mr-2" />
                      <span>Room {section.room}</span>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Meetings & Pending Grading */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upcoming Zoom Meetings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <FiVideo className="mr-2 text-primary-600" />
            Upcoming Zoom Meetings
          </h2>
          
          {dashboardData.upcoming_meetings.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No upcoming meetings</p>
          ) : (
            <div className="space-y-3">
              {dashboardData.upcoming_meetings.map((meeting) => (
                <div key={meeting.id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">{meeting.topic}</p>
                  <p className="text-sm text-gray-600">{meeting.subject_name}</p>
                  <div className="mt-2 flex items-center text-xs text-gray-500">
                    <FiCalendar className="mr-1" />
                    {new Date(meeting.meeting_date).toLocaleDateString()} at {meeting.start_time}
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* 🚫 REMOVED - Schedule New Meeting Link */}
        </div>

        {/* Pending Grading */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <FiClipboard className="mr-2 text-yellow-600" />
            Pending Grading
          </h2>
          
          {dashboardData.pending_grading.length === 0 ? (
            <p className="text-gray-500 text-center py-4">All caught up! 🎉</p>
          ) : (
            <div className="space-y-3">
              {dashboardData.pending_grading.slice(0, 5).map((item) => (
                <div key={item.submission_id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">{item.assignment_title}</p>
                  <p className="text-sm text-gray-600">{item.student_name}</p>
                  <div className="mt-2 flex justify-between items-center">
                    <span className="text-xs text-gray-500">
                      Submitted: {new Date(item.submitted_at).toLocaleDateString()}
                    </span>
                    <Link
                      to={`/teacher/assignment/${item.assignment_id}/grade`}
                      className="text-xs text-primary-600 hover:text-primary-700"
                    >
                      Grade Now
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Send Notification Modal */}
      <SendNotificationModal
        isOpen={showSendModal}
        onClose={() => setShowSendModal(false)}
      />
    </div>
  );
};

export default TeacherDashboard;