import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FiArrowLeft, FiCalendar, FiUsers, FiCheck, FiX, FiClock } from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const TeacherAttendance = () => {
  const { sectionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [section, setSection] = useState(null);
  const [students, setStudents] = useState([]);
  const [attendance, setAttendance] = useState({});
  const [attendanceDate, setAttendanceDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  useEffect(() => {
    if (sectionId) {
      fetchSectionData();
      fetchAttendance();
    }
  }, [sectionId, attendanceDate]);

  const fetchSectionData = async () => {
    try {
      const response = await api.get(`/teacher/sections/${sectionId}`);
      setSection(response.data.section);
      setStudents(response.data.students || []);
      
      // Initialize attendance with 'present' for all students
      const initialAttendance = {};
      response.data.students.forEach(student => {
        initialAttendance[student.id] = 'present';
      });
      setAttendance(initialAttendance);
    } catch (error) {
      console.error('Failed to fetch section:', error);
      toast.error('Failed to load section');
    }
  };

  const fetchAttendance = async () => {
    try {
      const response = await api.get(`/teacher/attendance/section/${sectionId}?date=${attendanceDate}`);
      
      // Update attendance with fetched data
      const fetchedAttendance = {};
      response.data.students.forEach(student => {
        fetchedAttendance[student.id] = student.attendance_status;
      });
      setAttendance(fetchedAttendance);
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = (studentId, status) => {
    setAttendance(prev => ({ ...prev, [studentId]: status }));
  };

  const markAll = (status) => {
    const newAttendance = {};
    students.forEach(student => {
      newAttendance[student.id] = status;
    });
    setAttendance(newAttendance);
  };

  const handleSubmit = async () => {
    const attendanceList = Object.entries(attendance).map(([studentId, status]) => ({
      student_id: parseInt(studentId),
      status
    }));

    setSaving(true);
    try {
      await api.post('/teacher/attendance/bulk', {
        section_id: parseInt(sectionId),
        date: attendanceDate,
        attendance: attendanceList
      });
      toast.success('Attendance saved successfully');
    } catch (error) {
      console.error('Failed to save attendance:', error);
      toast.error('Failed to save attendance');
    } finally {
      setSaving(false);
    }
  };

  const getStatusCount = () => {
    const counts = { present: 0, absent: 0, late: 0, excused: 0 };
    Object.values(attendance).forEach(status => {
      if (counts[status] !== undefined) counts[status]++;
    });
    return counts;
  };

  const counts = getStatusCount();

  if (loading) return <Loader />;
  if (!section) return <div>Section not found</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => navigate(`/teacher/section/${sectionId}`)}
              className="mr-4 text-gray-600 hover:text-gray-900"
            >
              <FiArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Take Attendance</h1>
              <p className="text-gray-600 mt-1">
                {section.subject_name} • Section {section.section_name}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <input
              type="date"
              value={attendanceDate}
              onChange={(e) => setAttendanceDate(e.target.value)}
              className="input-field w-auto"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center space-x-6">
          <span className="text-sm">
            <span className="font-medium text-gray-700">Present:</span>{' '}
            <span className="text-green-600 font-bold">{counts.present}</span>
          </span>
          <span className="text-sm">
            <span className="font-medium text-gray-700">Absent:</span>{' '}
            <span className="text-red-600 font-bold">{counts.absent}</span>
          </span>
          <span className="text-sm">
            <span className="font-medium text-gray-700">Late:</span>{' '}
            <span className="text-yellow-600 font-bold">{counts.late}</span>
          </span>
          <span className="text-sm">
            <span className="font-medium text-gray-700">Excused:</span>{' '}
            <span className="text-blue-600 font-bold">{counts.excused}</span>
          </span>
        </div>

        {/* Quick Actions */}
        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => markAll('present')}
            className="px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm"
          >
            All Present
          </button>
          <button
            onClick={() => markAll('absent')}
            className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
          >
            All Absent
          </button>
        </div>
      </div>

      {/* Attendance Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
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
                <td className="px-6 py-4 whitespace-nowrap">
                  <select
                    value={attendance[student.id] || 'present'}
                    onChange={(e) => handleStatusChange(student.id, e.target.value)}
                    className="input-field text-sm py-1 w-32"
                  >
                    <option value="present" className="text-green-600">✅ Present</option>
                    <option value="absent" className="text-red-600">❌ Absent</option>
                    <option value="late" className="text-yellow-600">⏰ Late</option>
                    <option value="excused" className="text-blue-600">📝 Excused</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Attendance'}
        </button>
      </div>
    </div>
  );
};

export default TeacherAttendance;