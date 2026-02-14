import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import Loader from '../common/Loader';
import { 
  FiDownload, FiCheckCircle, FiXCircle, FiUser,
  FiFile, FiSave, FiClock
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const GradeSubmissions = () => {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [assignment, setAssignment] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [grade, setGrade] = useState('');
  const [feedback, setFeedback] = useState('');

  useEffect(() => {
    if (assignmentId) {
      fetchSubmissions();
    } else {
      toast.error('Invalid assignment ID');
      navigate('/teacher/dashboard');
    }
  }, [assignmentId]);

  const fetchSubmissions = async () => {
    try {
      console.log('📡 Fetching submissions for assignment:', assignmentId);
      
      const [assignmentRes, submissionsRes] = await Promise.all([
        api.get(`/teacher/assignments/${assignmentId}`),  // ✅ Fixed
        api.get(`/teacher/grading/assignment/${assignmentId}`)  // ✅ Fixed
      ]);

      console.log('✅ Assignment data:', assignmentRes.data);
      console.log('✅ Submissions data:', submissionsRes.data);

      setAssignment(assignmentRes.data);
      setSubmissions(submissionsRes.data.submissions || []);
    } catch (error) {
      console.error('❌ Failed to fetch submissions:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      toast.error(error.response?.data?.error || 'Failed to load submissions');
    } finally {
      setLoading(false);
    }
  };

  const handleGradeSubmit = async (submissionId) => {
    if (!grade || parseFloat(grade) < 0 || parseFloat(grade) > assignment.points_possible) {
      toast.error(`Grade must be between 0 and ${assignment.points_possible}`);
      return;
    }

    setSubmitting(true);
    try {
      await api.put(`/teacher/grading/${submissionId}`, {
        grade: parseFloat(grade),
        feedback: feedback
      });

      toast.success('Submission graded successfully!');
      setSelectedSubmission(null);
      setGrade('');
      setFeedback('');
      fetchSubmissions();
    } catch (error) {
      console.error('Failed to grade submission:', error);
      toast.error(error.response?.data?.error || 'Failed to save grade');
    } finally {
      setSubmitting(false);
    }
  };

  const downloadFile = async (submissionId) => {
    try {
      const response = await api.get(`/teacher/submissions/${submissionId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'submission.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download file:', error);
      toast.error('Failed to download file');
    }
  };

  if (loading) return <Loader />;
  if (!assignment) return <div>Assignment not found</div>;

  const submitted = submissions.filter(s => s.has_submitted).length;
  const graded = submissions.filter(s => s.status === 'graded').length;
  const pending = submissions.filter(s => s.status === 'submitted').length;

  return (
    <div className="space-y-6">
      {/* Assignment Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900">{assignment.title}</h1>
        <p className="text-gray-600 mt-1">
          {assignment.subject_name} • {assignment.course_name}
        </p>
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Total Students</p>
            <p className="text-2xl font-bold text-gray-900">{submissions.length}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600">Submitted</p>
            <p className="text-2xl font-bold text-blue-700">{submitted}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <p className="text-sm text-yellow-600">Pending</p>
            <p className="text-2xl font-bold text-yellow-700">{pending}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600">Graded</p>
            <p className="text-2xl font-bold text-green-700">{graded}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <p className="text-sm text-purple-600">Average</p>
            <p className="text-2xl font-bold text-purple-700">
              {assignment.average_grade ? `${assignment.average_grade}%` : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Submissions List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Student Submissions</h2>

        {submissions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No students in this section</p>
        ) : (
          <div className="space-y-4">
            {submissions.map((student) => (
              <div key={student.student_id} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Student Info */}
                <div className="bg-gray-50 p-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                      {student.profile_pic ? (
                        <img src={student.profile_pic} alt={student.student_name} className="h-10 w-10 rounded-full" />
                      ) : (
                        <FiUser className="h-5 w-5 text-primary-600" />
                      )}
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">{student.student_name}</p>
                      <p className="text-xs text-gray-500">{student.student_email}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {!student.has_submitted ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Not Submitted
                      </span>
                    ) : student.status === 'graded' ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 flex items-center">
                        <FiCheckCircle className="mr-1" />
                        Graded
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800 flex items-center">
                        <FiClock className="mr-1" />
                        Pending
                      </span>
                    )}
                    {student.is_late && (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                        Late
                      </span>
                    )}
                  </div>
                </div>

                {/* Submission Content */}
                {student.has_submitted && (
                  <div className="p-4">
                    {student.content && (
                      <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Text Submission:</h3>
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{student.content}</p>
                      </div>
                    )}

                    {student.attachments && (
                      <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Attachments:</h3>
                        <button
                          onClick={() => downloadFile(student.submission_id)}
                          className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                        >
                          <FiDownload className="mr-2" />
                          Download Files
                        </button>
                      </div>
                    )}

                    <div className="text-xs text-gray-500">
                      Submitted: {new Date(student.submitted_at).toLocaleString()}
                    </div>
                  </div>
                )}

                {/* Grading Section */}
                {student.has_submitted && selectedSubmission === student.submission_id ? (
                  <div className="border-t border-gray-200 p-4 bg-gray-50">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Grade Submission</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Grade (out of {assignment.points_possible})
                        </label>
                        <input
                          type="number"
                          value={grade}
                          onChange={(e) => setGrade(e.target.value)}
                          className="input-field text-sm"
                          placeholder="Enter grade"
                          min="0"
                          max={assignment.points_possible}
                          step="0.1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Feedback
                        </label>
                        <textarea
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                          rows={3}
                          className="input-field text-sm"
                          placeholder="Provide feedback to student..."
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setSelectedSubmission(null)}
                          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleGradeSubmit(student.submission_id)}
                          disabled={submitting}
                          className="px-3 py-1 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 flex items-center"
                        >
                          {submitting ? 'Saving...' : <><FiSave className="mr-1" /> Save Grade</>}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : student.has_submitted && student.status !== 'graded' ? (
                  <div className="border-t border-gray-200 p-4 flex justify-end">
                    <button
                      onClick={() => {
                        setSelectedSubmission(student.submission_id);
                        setGrade(student.grade || '');
                        setFeedback(student.feedback || '');
                      }}
                      className="btn-primary text-sm"
                    >
                      Grade Submission
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GradeSubmissions;