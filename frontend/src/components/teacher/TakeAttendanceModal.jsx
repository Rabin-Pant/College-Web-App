import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { FiUsers, FiX, FiCheck, FiClock, FiSave, FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';

const TakeAttendanceModal = ({ isOpen, onClose, sectionId, students, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [attendance, setAttendance] = useState({});
  const [attendanceDate, setAttendanceDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [savedAttendance, setSavedAttendance] = useState({});

  // Fetch existing attendance when date changes
  useEffect(() => {
    if (isOpen && sectionId && attendanceDate) {
      fetchExistingAttendance();
    }
  }, [isOpen, sectionId, attendanceDate]);

  // Initialize attendance state when students change
  useEffect(() => {
    if (students.length > 0) {
      const initialAttendance = {};
      students.forEach(student => {
        // Use saved attendance if available, otherwise default to 'present'
        initialAttendance[student.id] = savedAttendance[student.id] || 'present';
      });
      setAttendance(initialAttendance);
    }
  }, [students, savedAttendance]);

  const fetchExistingAttendance = async () => {
    setFetching(true);
    try {
      const response = await api.get(`/teacher/attendance/section/${sectionId}?date=${attendanceDate}`);
      
      // Create a map of student_id -> attendance_status from response
      const attendanceMap = {};
      response.data.students.forEach(student => {
        attendanceMap[student.id] = student.attendance_status;
      });
      
      setSavedAttendance(attendanceMap);
      setAttendance(attendanceMap);
      
      console.log('✅ Fetched attendance for', attendanceDate, ':', attendanceMap);
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
      // If error, just use defaults
    } finally {
      setFetching(false);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const attendanceList = Object.entries(attendance).map(([studentId, status]) => ({
      student_id: parseInt(studentId),
      status
    }));

    setLoading(true);

    try {
      const response = await api.post('/teacher/attendance/bulk', {
        section_id: parseInt(sectionId),
        date: attendanceDate,
        attendance: attendanceList
      });
      
      toast.success(`✅ Attendance marked for ${response.data.success_count} students`);
      if (response.data.errors && response.data.errors.length > 0) {
        console.warn('Some errors:', response.data.errors);
      }
      onSuccess();
      onClose();
    } catch (error) {
      console.error('❌ Failed to mark attendance:', error);
      toast.error(error.response?.data?.error || 'Failed to mark attendance');
    } finally {
      setLoading(false);
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white z-10">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <FiUsers className="mr-2 text-primary-600" />
            Take Attendance
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Date Selection and Summary */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Attendance Date
                </label>
                <input
                  type="date"
                  value={attendanceDate}
                  onChange={(e) => setAttendanceDate(e.target.value)}
                  className="input-field"
                  required
                />
              </div>
              
              {fetching && (
                <div className="flex items-center text-sm text-gray-500">
                  <FiRefreshCw className="animate-spin mr-2" />
                  Loading...
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm">
                <span className="font-medium text-gray-700">Summary: </span>
                <span className="text-green-600 ml-2">P: {counts.present}</span>
                <span className="text-red-600 ml-2">A: {counts.absent}</span>
                <span className="text-yellow-600 ml-2">L: {counts.late}</span>
                <span className="text-blue-600 ml-2">E: {counts.excused}</span>
              </div>

              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => markAll('present')}
                  className="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm font-medium"
                >
                  All Present
                </button>
                <button
                  type="button"
                  onClick={() => markAll('absent')}
                  className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium"
                >
                  All Absent
                </button>
              </div>
            </div>
          </div>

          {/* Attendance Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {students.map((student) => (
                  <tr key={student.id} className="hover:bg-gray-50">
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
                        disabled={fetching}
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

          {/* Instructions */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800 mb-2">📌 Tips:</h3>
            <ul className="text-xs text-blue-700 space-y-1 list-disc list-inside">
              <li>Attendance is saved per student per date</li>
              <li>Changing the date will load existing attendance records</li>
              <li>Use "All Present" or "All Absent" buttons for quick marking</li>
              <li>You can edit attendance anytime - it will overwrite previous records</li>
            </ul>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || fetching}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  Save Attendance
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TakeAttendanceModal;