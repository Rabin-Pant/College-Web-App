import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiUsers, FiCalendar, FiMapPin,
  FiUser, FiClock, FiChevronRight
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const StudentSections = () => {
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState([]);

  useEffect(() => {
    fetchSections();
  }, []);

  const fetchSections = async () => {
    try {
      console.log('📡 Fetching student sections...');
      const response = await api.get('/student/sections');
      console.log('✅ Sections received:', response.data);
      setSections(response.data.sections || []);
    } catch (error) {
      console.error('❌ Failed to fetch sections:', error);
      toast.error('Failed to load sections');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Enrolled Sections</h1>
            <p className="text-gray-600 mt-1">View all sections you are enrolled in</p>
          </div>
          <Link
            to="/student/available-sections"
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            Browse More Sections
          </Link>
        </div>
      </div>

      {/* Sections List */}
      {sections.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FiBook className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No enrolled sections</h3>
          <p className="mt-2 text-gray-500">You haven't enrolled in any sections yet.</p>
          <Link
            to="/student/available-sections"
            className="mt-4 inline-block btn-primary"
          >
            Browse Available Sections
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sections.map((section) => {
            // Debug log to see what properties are available
            console.log('Section data:', section);
            
            return (
              <Link
                key={section.section_id}  // ← Using section_id as key
                to={`/student/section/${section.section_id}`}  // ← Using section_id in URL
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition overflow-hidden"
              >
                {/* Colored Header */}
                <div className="h-32 bg-gradient-to-r from-green-600 to-green-800 p-4">
                  <h3 className="text-xl font-bold text-white">{section.subject_code || 'Subject'}</h3>
                  <p className="text-green-100">{section.subject_name || 'Unknown'}</p>
                </div>
                
                {/* Content */}
                <div className="p-4 space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <FiBook className="mr-2 flex-shrink-0" />
                    <span className="truncate">{section.course_name || 'Course'}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <FiUser className="mr-2 flex-shrink-0" />
                    <span className="truncate">{section.teacher_name || 'TBA'}</span>
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <FiCalendar className="mr-2 flex-shrink-0" />
                    <span>{section.semester || 'N/A'}</span>
                  </div>

                  {section.room && (
                    <div className="flex items-center text-sm text-gray-600">
                      <FiMapPin className="mr-2 flex-shrink-0" />
                      <span>Room {section.room}</span>
                    </div>
                  )}

                  {section.day && (
                    <div className="flex items-center text-sm text-gray-600">
                      <FiClock className="mr-2 flex-shrink-0" />
                      <span>
                        {section.day} {section.start_time ? section.start_time.substring(0,5) : ''}
                        {section.end_time ? ` - ${section.end_time.substring(0,5)}` : ''}
                      </span>
                    </div>
                  )}

                  {/* View Details Link */}
                  <div className="pt-2 flex justify-end">
                    <span className="text-green-600 text-sm font-medium flex items-center hover:text-green-700">
                      View Section <FiChevronRight className="ml-1" />
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StudentSections;