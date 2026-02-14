import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  FiBook, FiUsers, FiClipboard, FiCalendar,
  FiMapPin, FiFileText, FiChevronRight
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const TeacherSections = () => {
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    total_students: 0,
    total_assignments: 0
  });

  useEffect(() => {
    fetchSections();
  }, []);

  const fetchSections = async () => {
    try {
      const sectionsRes = await api.get('/teacher/sections/');
      setSections(sectionsRes.data.sections || []);
      
      const statsRes = await api.get('/teacher/sections/stats');
      setStats({
        total: sectionsRes.data.total || 0,
        total_students: statsRes.data.total_students || 0,
        total_assignments: statsRes.data.total_assignments || 0
      });
    } catch (error) {
      console.error('Failed to fetch sections:', error);
      toast.error('Failed to load sections');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900">My Sections</h1>
        <p className="text-gray-600 mt-1">View and manage your assigned sections</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-50 rounded-lg p-6">
          <p className="text-sm text-blue-600">Total Sections</p>
          <p className="text-3xl font-bold text-blue-700">{stats.total}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-6">
          <p className="text-sm text-green-600">Total Students</p>
          <p className="text-3xl font-bold text-green-700">{stats.total_students}</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-6">
          <p className="text-sm text-purple-600">Assignments</p>
          <p className="text-3xl font-bold text-purple-700">{stats.total_assignments}</p>
        </div>
      </div>

      {sections.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FiBook className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No sections assigned</h3>
          <p className="mt-2 text-gray-500">You haven't been assigned to any sections yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sections.map((section) => (
            <Link
              key={section.section_id}
              to={`/teacher/section/${section.section_id}`}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition overflow-hidden"
            >
              <div className="h-32 bg-gradient-to-r from-blue-600 to-blue-800 p-4">
                <h3 className="text-xl font-bold text-white">{section.subject_code}</h3>
                <p className="text-blue-100">{section.subject_name}</p>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex items-center text-sm text-gray-600">
                  <FiBook className="mr-2" />
                  <span>{section.course_name}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <FiUsers className="mr-2" />
                  <span>{section.enrolled_count || 0}/{section.capacity} students</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <FiCalendar className="mr-2" />
                  <span>{section.academic_semester}</span>
                </div>
                {section.room && (
                  <div className="flex items-center text-sm text-gray-600">
                    <FiMapPin className="mr-2" />
                    <span>Room {section.room}</span>
                  </div>
                )}
                <div className="pt-2 flex justify-end">
                  <span className="text-blue-600 text-sm flex items-center">
                    Manage Section <FiChevronRight className="ml-1" />
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default TeacherSections;