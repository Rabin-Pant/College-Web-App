import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiUsers, FiCalendar, FiMapPin, 
  FiUser, FiFileText, FiVideo, FiDownload,
  FiClock, FiCheckCircle, FiAlertCircle
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const StudentSectionView = () => {
  const { sectionId } = useParams();
  const [loading, setLoading] = useState(true);
  const [section, setSection] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [schedule, setSchedule] = useState([]);

  // Debug logging
  useEffect(() => {
    console.log('📌 SectionView mounted');
    console.log('🔍 sectionId from URL:', sectionId);
    console.log('🔍 Type of sectionId:', typeof sectionId);
    console.log('🔍 Full URL:', window.location.pathname);
    
    if (!sectionId) {
      console.error('❌ No sectionId provided in URL!');
      toast.error('Invalid section ID');
    }
  }, [sectionId]);

  useEffect(() => {
    if (sectionId) {
      fetchSectionData();
    }
  }, [sectionId]);

  const fetchSectionData = async () => {
    try {
      console.log('📡 Fetching data for section ID:', sectionId);
      
      const [sectionRes, materialsRes, assignmentsRes, meetingsRes] = await Promise.all([
        api.get(`/student/sections/${sectionId}`),
        api.get(`/student/materials/section/${sectionId}`),
        api.get(`/student/assignments/section/${sectionId}`),
        api.get(`/student/zoom/section/${sectionId}`)
      ]);

      console.log('✅ Section data received:', sectionRes.data);
      console.log('✅ Materials received:', materialsRes.data);
      console.log('✅ Assignments received:', assignmentsRes.data);
      console.log('✅ Meetings received:', meetingsRes.data);

      setSection(sectionRes.data.section);
      setMaterials(materialsRes.data.materials || []);
      setSchedule(sectionRes.data.schedule || []);
      setAssignments(assignmentsRes.data.assignments || []);
      setMeetings(meetingsRes.data.meetings || []);
    } catch (error) {
      console.error('❌ Failed to fetch section data:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      toast.error(error.response?.data?.error || 'Failed to load section details');
    } finally {
      setLoading(false);
    }
  };

  const getDayOrder = (day) => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return days.indexOf(day);
  };

  if (loading) return <Loader />;
  
  if (!section) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <FiBook className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Section not found</h3>
          <p className="mt-2 text-gray-500">The section you're looking for doesn't exist or you don't have access.</p>
          <Link to="/student/sections" className="mt-4 inline-block btn-primary">
            Go to My Sections
          </Link>
        </div>
      </div>
    );
  }

  const sortedSchedule = [...schedule].sort((a, b) => 
    getDayOrder(a.day) - getDayOrder(b.day) || a.start_time?.localeCompare(b.start_time || '')
  );

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{section.subject_name}</h1>
            <p className="text-gray-600 mt-1">
              {section.course_name} • Section {section.section_name}
            </p>
          </div>
          <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
            Enrolled
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center text-gray-600">
            <FiUser className="mr-2 flex-shrink-0" />
            <span className="truncate">Instructor: {section.teacher_name || 'TBA'}</span>
          </div>
          <div className="flex items-center text-gray-600">
            <FiCalendar className="mr-2 flex-shrink-0" />
            <span>{section.academic_year} • {section.semester}</span>
          </div>
          <div className="flex items-center text-gray-600">
            <FiUsers className="mr-2 flex-shrink-0" />
            <span>{section.enrolled_count || 0} Students</span>
          </div>
          {section.room && (
            <div className="flex items-center text-gray-600">
              <FiMapPin className="mr-2 flex-shrink-0" />
              <span>Room {section.room}</span>
            </div>
          )}
        </div>
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
              <div key={index} className="flex flex-wrap items-center p-3 bg-gray-50 rounded-lg">
                <div className="w-24 font-medium text-gray-700">{sch.day}</div>
                <div className="flex-1 flex items-center">
                  <FiClock className="mr-2 text-gray-400" />
                  <span>{sch.start_time?.substring(0,5) || 'TBA'} - {sch.end_time?.substring(0,5) || 'TBA'}</span>
                </div>
                {sch.room && (
                  <div className="flex items-center text-gray-600 ml-4">
                    <FiMapPin className="mr-2" />
                    <span>Room {sch.room}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Materials */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <FiFileText className="mr-2" />
          Study Materials
        </h2>
        
        {materials.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No materials uploaded yet</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {materials.map((material) => (
              <div key={material.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{material.title}</h3>
                    {material.description && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">{material.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                      <FiCalendar className="mr-1" />
                      <span>{material.created_at ? new Date(material.created_at).toLocaleDateString() : 'N/A'}</span>
                      {material.topic && (
                        <>
                          <span className="mx-1">•</span>
                          <span>Topic: {material.topic}</span>
                        </>
                      )}
                      {material.type && (
                        <>
                          <span className="mx-1">•</span>
                          <span className="capitalize">{material.type}</span>
                        </>
                      )}
                    </div>
                  </div>
                  {material.file_path && (
                    <a
                      href={`http://127.0.0.1:5000${material.file_path}`}
                      download
                      className="ml-4 text-primary-600 hover:text-primary-700"
                      title="Download"
                    >
                      <FiDownload className="h-5 w-5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assignments */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <FiBook className="mr-2" />
          Assignments
        </h2>
        
        {assignments.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No assignments yet</p>
        ) : (
          <div className="space-y-4">
            {assignments.map((assignment) => {
              const dueDate = assignment.due_date ? new Date(assignment.due_date) : null;
              const isOverdue = dueDate && dueDate < new Date();
              const hasSubmitted = assignment.submission_status === 'submitted';
              const isGraded = assignment.submission_status === 'graded';

              return (
                <Link
                  key={assignment.id}
                  to={`/student/assignment/${assignment.id}`}
                  className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                >
                  <div className="flex flex-wrap justify-between items-start gap-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{assignment.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{assignment.points_possible} points</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {isGraded ? (
                        <span className="bg-green-100 text-green-700 px-2 py-1 text-xs rounded-full flex items-center">
                          <FiCheckCircle className="mr-1" />
                          Graded
                        </span>
                      ) : hasSubmitted ? (
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 text-xs rounded-full">
                          Submitted
                        </span>
                      ) : isOverdue ? (
                        <span className="bg-red-100 text-red-700 px-2 py-1 text-xs rounded-full flex items-center">
                          <FiAlertCircle className="mr-1" />
                          Overdue
                        </span>
                      ) : (
                        <span className="bg-yellow-100 text-yellow-700 px-2 py-1 text-xs rounded-full">
                          Pending
                        </span>
                      )}
                    </div>
                  </div>
                  {dueDate && (
                    <div className="mt-2 flex items-center text-sm text-gray-500">
                      <FiClock className="mr-1" />
                      Due: {dueDate.toLocaleDateString()} {dueDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Zoom Meetings */}
      {meetings.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <FiVideo className="mr-2" />
            Upcoming Zoom Meetings
          </h2>
          <div className="space-y-3">
            {meetings.map((meeting) => (
              <div key={meeting.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex flex-wrap justify-between items-start gap-2">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{meeting.topic}</h3>
                    {meeting.description && (
                      <p className="text-sm text-gray-600 mt-1">{meeting.description}</p>
                    )}
                  </div>
                  {meeting.meeting_link && (
                    <a
                      href={meeting.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 text-sm whitespace-nowrap"
                    >
                      Join Meeting
                    </a>
                  )}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <FiCalendar className="mr-2" />
                    <span>{meeting.meeting_date ? new Date(meeting.meeting_date).toLocaleDateString() : 'TBA'}</span>
                  </div>
                  <div className="flex items-center">
                    <FiClock className="mr-2" />
                    <span>{meeting.start_time?.substring(0,5) || 'TBA'}</span>
                  </div>
                  {meeting.duration_minutes && (
                    <span>{meeting.duration_minutes} minutes</span>
                  )}
                </div>
                {meeting.recording_link && (
                  <div className="mt-2">
                    <a
                      href={meeting.recording_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-700 flex items-center"
                    >
                      <FiVideo className="mr-1" />
                      View Recording
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentSectionView;