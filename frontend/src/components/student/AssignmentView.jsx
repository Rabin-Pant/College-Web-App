import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import Loader from '../common/Loader';
import { FiFile, FiUpload, FiCheckCircle, FiClock } from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

const AssignmentView = () => {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [files, setFiles] = useState([]);
  const [textEntry, setTextEntry] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (assignmentId) {
      fetchAssignmentData();
    } else {
      console.error('No assignmentId provided');
      toast.error('Invalid assignment');
      navigate('/student/dashboard');
    }
  }, [assignmentId]);

  const fetchAssignmentData = async () => {
    try {
      console.log('📡 Fetching assignment:', assignmentId);
      
      const [assignmentRes, submissionRes] = await Promise.all([
        api.get(`/student/assignments/${assignmentId}`),  // ✅ Fixed
        api.get(`/student/assignments/${assignmentId}/submissions`) // ✅ Fixed
      ]);

      console.log('✅ Assignment data received:', assignmentRes.data);
      
      setAssignment(assignmentRes.data.assignment || assignmentRes.data);
      setSubmission(submissionRes.data.submission);
      
      if (submissionRes.data.submission) {
        setTextEntry(submissionRes.data.submission.content || '');
      }
    } catch (error) {
      console.error('❌ Failed to fetch assignment:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      toast.error(error.response?.data?.error || 'Failed to load assignment');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (acceptedFiles) => {
    setFiles([...files, ...acceptedFiles]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 10485760, // 10MB
    multiple: true
  });

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!textEntry && files.length === 0) {
      toast.error('Please add text or upload files');
      return;
    }

    setSubmitting(true);
    const formData = new FormData();
    formData.append('text_entry', textEntry);
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      await api.post(`/student/assignments/${assignmentId}/submit`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Assignment submitted successfully!');
      fetchAssignmentData();
      setFiles([]);
    } catch (error) {
      console.error('Failed to submit:', error);
      toast.error(error.response?.data?.error || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loader />;
  if (!assignment) return <div>Assignment not found</div>;

  const isLate = new Date() > new Date(assignment.due_date);
  const isSubmitted = submission && submission.status === 'submitted';
  const isGraded = submission && submission.status === 'graded';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Assignment Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{assignment.title}</h1>
            <p className="text-gray-600 mt-2">{assignment.class_name} • {assignment.course_code}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
            isGraded ? 'bg-green-100 text-green-800' :
            isSubmitted ? 'bg-blue-100 text-blue-800' :
            isLate ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {isGraded ? 'Graded' : isSubmitted ? 'Submitted' : isLate ? 'Late' : 'Pending'}
          </span>
        </div>

        <div className="mt-4 flex items-center space-x-4 text-sm text-gray-600">
          <span className="flex items-center">
            <FiClock className="mr-1" />
            Due: {new Date(assignment.due_date).toLocaleString()}
          </span>
          <span>{assignment.points_possible} points</span>
        </div>

        <div className="mt-6 prose max-w-none">
          <h3 className="text-lg font-semibold text-gray-900">Instructions</h3>
          <p className="mt-2 text-gray-700 whitespace-pre-wrap">{assignment.instructions}</p>
        </div>
      </div>

      {/* Submission Area */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Your Submission</h2>

        {isGraded ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Grade: {submission.grade}/{assignment.points_possible}</h3>
              {submission.feedback && (
                <p className="mt-2 text-green-700">{submission.feedback}</p>
              )}
            </div>
          </div>
        ) : (
          <>
            {/* Text Entry */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text Entry
              </label>
              <textarea
                value={textEntry}
                onChange={(e) => setTextEntry(e.target.value)}
                rows={6}
                className="input-field"
                placeholder="Type your answer here..."
                disabled={isSubmitted}
              />
            </div>

            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File Upload
              </label>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition duration-200 ${
                  isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
                } ${isSubmitted ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input {...getInputProps()} disabled={isSubmitted} />
                <FiUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                {isDragActive ? (
                  <p className="text-primary-600">Drop files here...</p>
                ) : (
                  <>
                    <p className="text-gray-600">Drag & drop files here, or click to select</p>
                    <p className="text-sm text-gray-500 mt-2">PDF, DOC, ZIP, images (Max 10MB)</p>
                  </>
                )}
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Files to upload ({files.length})</h3>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <FiFile className="text-gray-400 mr-2" />
                        <span className="text-sm text-gray-700">{file.name}</span>
                        <span className="text-xs text-gray-500 ml-2">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-600 hover:text-red-700 text-sm"
                        disabled={isSubmitted}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Button */}
            {!isSubmitted && (
              <button
                onClick={handleSubmit}
                disabled={submitting || (!textEntry && files.length === 0)}
                className="w-full btn-primary flex items-center justify-center"
              >
                {submitting ? (
                  'Submitting...'
                ) : (
                  <>
                    <FiCheckCircle className="mr-2" />
                    Submit Assignment
                  </>
                )}
              </button>
            )}

            {isSubmitted && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800 flex items-center">
                  <FiCheckCircle className="mr-2" />
                  You have already submitted this assignment.
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Previous Submissions */}
      {submission && submission.attempt_number > 1 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Submission History</h3>
          <p className="text-sm text-gray-600">
            Attempt #{submission.attempt_number} • Submitted: {new Date(submission.submitted_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
};

export default AssignmentView;