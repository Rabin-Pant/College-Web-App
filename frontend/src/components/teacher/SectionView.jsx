import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiUsers, FiClipboard, FiPlus, FiCalendar,
  FiBook, FiFile, FiVideo, FiBell,
  FiCheckCircle, FiXCircle, FiUserCheck,
  FiDownload, FiEdit2, FiTrash2, FiMapPin,
  FiClock
} from 'react-icons/fi';
import Loader from '../common/Loader';
import SendNotificationModal from '../notifications/SendNotificationModal';
import CreateZoomModal from './CreateZoomModal';
import TakeAttendanceModal from './TakeAttendanceModal';
import toast from 'react-hot-toast';

const TeacherSectionView = () => {
  const { sectionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [section, setSection] = useState(null);
  const [students, setStudents] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [pendingEnrollments, setPendingEnrollments] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showZoomModal, setShowZoomModal] = useState(false);
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);

  useEffect(() => {
    fetchSectionData();
  }, [sectionId]);

  const fetchSectionData = async () => {
    try {
      const response = await api.get(`/teacher/sections/${sectionId}`);
      setSection(response.data.section);
      setStudents(response.data.students || []);
      setSchedule(response.data.schedule || []);
      setPendingEnrollments(response.data.pending_enrollments || []);
      
      const [assignmentsRes, materialsRes] = await Promise.all([
        api.get(`/teacher/assignments/section/${sectionId}`),
        api.get(`/teacher/materials/section/${sectionId}`)
      ]);
      
      setAssignments(assignmentsRes.data.assignments || []);
      setMaterials(materialsRes.data.materials || []);
    } catch (error) {
      console.error('Failed to fetch section data:', error);
      toast.error('Failed to load section details');
      navigate('/teacher/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const approveEnrollment = async (enrollmentId) => {
    try {
      await api.post(`/teacher/enrollments/${enrollmentId}/approve`);
      toast.success('Enrollment approved');
      fetchSectionData();
    } catch (error) {
      console.error('Failed to approve enrollment:', error);
      toast.error('Failed to approve enrollment');
    }
  };

  const rejectEnrollment = async (enrollmentId) => {
    try {
      await api.post(`/teacher/enrollments/${enrollmentId}/reject`);
      toast.success('Enrollment rejected');
      fetchSectionData();
    } catch (error) {
      console.error('Failed to reject enrollment:', error);
      toast.error('Failed to reject enrollment');
    }
  };

  const removeStudent = async (studentId, studentName) => {
    if (!window.confirm(`Remove ${studentName} from this section?`)) return;
    
    try {
      await api.delete(`/teacher/sections/${sectionId}/students/${studentId}`);
      toast.success('Student removed');
      fetchSectionData();
    } catch (error) {
      console.error('Failed to remove student:', error);
      toast.error('Failed to remove student');
    }
  };

  const getDayOrder = (day) => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return days.indexOf(day);
  };

  if (loading) return <Loader />;
  if (!section) return <div>Section not found</div>;

  const sortedSchedule = [...schedule].sort((a, b) => 
    getDayOrder(a.day) - getDayOrder(b.day) || a.start_time.localeCompare(b.start_time)
  );

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:justify-between md:items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{section.subject_name}</h1>
            <p className="text-gray-600 mt-1">
              {section.course_name} • Section {section.section_name} • {section.academic_semester}
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex flex-wrap gap-2">
            <button
              onClick={() => setShowAttendanceModal(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center"
            >
              <FiUsers className="mr-2" />
              Take Attendance
            </button>
            <button
              onClick={() => setShowZoomModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
            >
              <FiVideo className="mr-2" />
              Schedule Zoom
            </button>
            <button
              onClick={() => setShowSendModal(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
            >
              <FiBell className="mr-2" />
              Send Notification
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Total Students</p>
            <p className="text-xl font-bold text-gray-900">{students.length}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Pending Requests</p>
            <p className="text-xl font-bold text-yellow-600">{pendingEnrollments.length}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Assignments</p>
            <p className="text-xl font-bold text-gray-900">{assignments.length}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Materials</p>
            <p className="text-xl font-bold text-gray-900">{materials.length}</p>
          </div>
        </div>

        {section.room && (
          <div className="mt-4 text-sm text-gray-600 flex items-center">
            <FiMapPin className="mr-2" />
            Room: {section.room}
          </div>
        )}
      </div>

      {/* Schedule */}
      {sortedSchedule.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <FiCalendar className="mr-2" />
            Class Schedule
          </h2>
          <div className="space-y-3">
            {sortedSchedule.map((sch, index) => (
              <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                <div className="w-24 font-medium text-gray-700">{sch.day}</div>
                <div className="flex-1 flex items-center">
                  <FiClock className="mr-2 text-gray-400" />
                  {sch.start_time} - {sch.end_time}
                </div>
                {sch.room && (
                  <div className="text-gray-600 flex items-center">
                    <FiMapPin className="mr-2" />
                    Room {sch.room}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Enrollments */}
      {pendingEnrollments.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-yellow-800 mb-3 flex items-center">
            <FiUserCheck className="mr-2" />
            Pending Enrollment Requests ({pendingEnrollments.length})
          </h2>
          <div className="space-y-3">
            {pendingEnrollments.map((request) => (
              <div key={request.enrollment_id} className="bg-white p-4 rounded-lg flex justify-between items-center">
                <div>
                  <p className="font-medium text-gray-900">{request.student_name}</p>
                  <p className="text-sm text-gray-600">{request.student_email}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Requested: {new Date(request.enrollment_date).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => approveEnrollment(request.enrollment_id)}
                    className="bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700 text-sm flex items-center"
                  >
                    <FiCheckCircle className="mr-1" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectEnrollment(request.enrollment_id)}
                    className="bg-red-600 text-white px-3 py-1 rounded-lg hover:bg-red-700 text-sm flex items-center"
                  >
                    <FiXCircle className="mr-1" />
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to={`/teacher/section/${sectionId}/upload-material`}
          className="bg-blue-50 p-4 rounded-lg hover:bg-blue-100 transition flex items-center"
        >
          <FiFile className="h-8 w-8 text-blue-600 mr-3" />
          <div>
            <h3 className="font-semibold text-blue-900">Upload Material</h3>
            <p className="text-sm text-blue-700">Add study materials</p>
          </div>
        </Link>

        <Link
          to={`/teacher/section/${sectionId}/create-assignment`}
          className="bg-green-50 p-4 rounded-lg hover:bg-green-100 transition flex items-center"
        >
          <FiClipboard className="h-8 w-8 text-green-600 mr-3" />
          <div>
            <h3 className="font-semibold text-green-900">Create Assignment</h3>
            <p className="text-sm text-green-700">Add new assignment</p>
          </div>
        </Link>

        <Link
          to={`/teacher/section/${sectionId}/attendance`}
          className="bg-purple-50 p-4 rounded-lg hover:bg-purple-100 transition flex items-center"
        >
          <FiUsers className="h-8 w-8 text-purple-600 mr-3" />
          <div>
            <h3 className="font-semibold text-purple-900">Attendance</h3>
            <p className="text-sm text-purple-700">View attendance records</p>
          </div>
        </Link>
      </div>

      {/* Assignments List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">📝 Assignments</h2>
          <Link
            to={`/teacher/section/${sectionId}/create-assignment`}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 text-sm flex items-center"
          >
            <FiPlus className="mr-2" />
            New Assignment
          </Link>
        </div>

        {assignments.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No assignments yet</p>
        ) : (
          <div className="space-y-3">
            {assignments.map((assignment) => (
              <div key={assignment.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-gray-900">{assignment.title}</h3>
                    <p className="text-sm text-gray-600">{assignment.points_possible} points</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/teacher/assignment/${assignment.id}/grade`}
                      className="text-primary-600 hover:text-primary-700 text-sm"
                    >
                      Grade ({assignment.submitted_count || 0} submissions)
                    </Link>
                    <button className="text-gray-400 hover:text-red-600">
                      <FiTrash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  Due: {new Date(assignment.due_date).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Student List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <FiUsers className="mr-2" />
          Enrolled Students ({students.length})
        </h2>

        {students.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No students enrolled yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Major</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enrolled</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {students.map((student) => (
                  <tr key={student.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                          {student.profile_pic ? (
                            <img src={student.profile_pic} alt="" className="h-8 w-8 rounded-full" />
                          ) : (
                            <FiUsers className="h-4 w-4 text-gray-500" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{student.name}</p>
                          <p className="text-xs text-gray-500">{student.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {student.student_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {student.major || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(student.enrollment_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => removeStudent(student.id, student.name)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      <SendNotificationModal
        isOpen={showSendModal}
        onClose={() => setShowSendModal(false)}
        sectionId={sectionId}
        sectionName={section?.subject_name}
      />

      {showZoomModal && (
        <CreateZoomModal
          isOpen={showZoomModal}
          onClose={() => setShowZoomModal(false)}
          sectionId={sectionId}
          onSuccess={fetchSectionData}
        />
      )}

      {showAttendanceModal && (
        <TakeAttendanceModal
          isOpen={showAttendanceModal}
          onClose={() => setShowAttendanceModal(false)}
          sectionId={sectionId}
          students={students}
          onSuccess={fetchSectionData}
        />
      )}
    </div>
  );
};

export default TeacherSectionView;