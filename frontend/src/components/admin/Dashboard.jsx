import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  FiUsers, FiBook, FiClipboard, FiCheckCircle, 
  FiUserCheck, FiUserX, FiBarChart2, FiSettings,
  FiTrendingUp, FiCalendar, FiDownload, FiGrid,
  FiAward
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_courses: 0,
    total_subjects: 0,
    total_sections: 0,
    total_users: 0,
    total_teachers: 0,
    total_students: 0,
    total_enrollments: 0,
    total_assignments: 0
  });
  const [recentCourses, setRecentCourses] = useState([]);
  const [recentSections, setRecentSections] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      console.log('📡 Fetching admin dashboard data...');
      
      // Fetch real data from API
      const [coursesRes, subjectsRes, sectionsRes, usersRes, enrollmentsRes] = await Promise.all([
        api.get('/admin/courses/?limit=5'),
        api.get('/admin/subjects/?limit=5'),
        api.get('/admin/sections/?limit=5'),
        api.get('/admin/users/?limit=100'),
        api.get('/admin/enrollments/')
      ]);

      // Calculate real stats
      const total_courses = coursesRes.data.total || coursesRes.data.courses?.length || 0;
      const total_subjects = subjectsRes.data.total || subjectsRes.data.subjects?.length || 0;
      const total_sections = sectionsRes.data.total || sectionsRes.data.sections?.length || 0;
      
      // Calculate user counts from real data
      const users = usersRes.data.users || [];
      const total_users = users.length;
      const total_teachers = users.filter(u => u.role === 'teacher').length;
      const total_students = users.filter(u => u.role === 'student').length;
      
      // Calculate enrollment counts
      const enrollments = enrollmentsRes.data.enrollments || [];
      const total_enrollments = enrollments.length;

      setStats({
        total_courses,
        total_subjects,
        total_sections,
        total_users,
        total_teachers,
        total_students,
        total_enrollments,
        total_assignments: 0 // You'll need to add this endpoint
      });

      setRecentCourses(coursesRes.data.courses?.slice(0, 5) || []);
      setRecentSections(sectionsRes.data.sections?.slice(0, 5) || []);
      
      console.log('✅ Admin dashboard data loaded with real stats:', stats);
    } catch (error) {
      console.error('❌ Failed to fetch admin dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 rounded-lg shadow-lg p-8 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">Admin Dashboard 👑</h1>
            <p className="mt-2 text-purple-100">Welcome back, {user?.name || 'Admin'}. Manage the entire system from here.</p>
          </div>
          <div className="flex space-x-2">
            <Link
              to="/admin/reports"
              className="bg-white text-purple-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition duration-200 flex items-center"
            >
              <FiBarChart2 className="mr-2" />
              Reports
            </Link>
            <Link
              to="/admin/settings"
              className="bg-white text-purple-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition duration-200 flex items-center"
            >
              <FiSettings className="mr-2" />
              Settings
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid - Now with REAL data! */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Courses</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_courses}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <FiBook className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <Link to="/admin/courses" className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center">
            Manage Courses →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Subjects</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_subjects}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <FiGrid className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <Link to="/admin/subjects" className="mt-4 text-sm text-green-600 hover:text-green-700 flex items-center">
            Manage Subjects →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Sections</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_sections}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <FiClipboard className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <Link to="/admin/sections" className="mt-4 text-sm text-purple-600 hover:text-purple-700 flex items-center">
            Manage Sections →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Users</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_users}</p>
              <div className="mt-2 text-xs text-gray-600">
                <span className="text-green-600">{stats.total_students} Students</span> • 
                <span className="text-blue-600"> {stats.total_teachers} Teachers</span>
              </div>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
          <Link to="/admin/users" className="mt-4 text-sm text-yellow-600 hover:text-yellow-700 flex items-center">
            Manage Users →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Teacher Assignments</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_teachers}</p>
              <p className="text-xs text-gray-500 mt-1">Teachers in system</p>
            </div>
            <div className="bg-indigo-100 p-3 rounded-full">
              <FiUserCheck className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
          <Link to="/admin/teacher-assignments" className="mt-4 text-sm text-indigo-600 hover:text-indigo-700 flex items-center">
            Assign Teachers →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Enrollments</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_enrollments}</p>
              <p className="text-xs text-gray-500 mt-1">Students enrolled</p>
            </div>
            <div className="bg-pink-100 p-3 rounded-full">
              <FiAward className="h-6 w-6 text-pink-600" />
            </div>
          </div>
          <Link to="/admin/enrollments" className="mt-4 text-sm text-pink-600 hover:text-pink-700 flex items-center">
            View Enrollments →
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <FiSettings className="mr-2 text-gray-600" />
          Quick Actions
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link 
            to="/admin/courses" 
            className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition duration-200"
          >
            <div className="flex items-center">
              <div className="bg-blue-200 p-3 rounded-full mr-3">
                <FiBook className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">Manage Courses</h3>
                <p className="text-sm text-blue-700">Add or edit courses</p>
              </div>
            </div>
          </Link>
          
          <Link 
            to="/admin/subjects" 
            className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition duration-200"
          >
            <div className="flex items-center">
              <div className="bg-green-200 p-3 rounded-full mr-3">
                <FiGrid className="h-5 w-5 text-green-700" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900">Manage Subjects</h3>
                <p className="text-sm text-green-700">Add subjects to courses</p>
              </div>
            </div>
          </Link>
          
          <Link 
            to="/admin/sections" 
            className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition duration-200"
          >
            <div className="flex items-center">
              <div className="bg-purple-200 p-3 rounded-full mr-3">
                <FiClipboard className="h-5 w-5 text-purple-700" />
              </div>
              <div>
                <h3 className="font-semibold text-purple-900">Create Sections</h3>
                <p className="text-sm text-purple-700">Add class sections</p>
              </div>
            </div>
          </Link>
          
          <Link 
            to="/admin/teacher-assignments" 
            className="p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition duration-200"
          >
            <div className="flex items-center">
              <div className="bg-indigo-200 p-3 rounded-full mr-3">
                <FiUserCheck className="h-5 w-5 text-indigo-700" />
              </div>
              <div>
                <h3 className="font-semibold text-indigo-900">Assign Teachers</h3>
                <p className="text-sm text-indigo-700">Assign to sections</p>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Courses */}
      {recentCourses.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📚 Recent Courses</h2>
          <div className="space-y-3">
            {recentCourses.map((course) => (
              <div key={course.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{course.name}</p>
                  <p className="text-sm text-gray-500">Code: {course.code}</p>
                </div>
                <span className="text-xs text-gray-400">
                  {course.subjects_count || 0} subjects
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Sections */}
      {recentSections.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Recent Sections</h2>
          <div className="space-y-3">
            {recentSections.map((section) => (
              <div key={section.section_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{section.subject_name}</p>
                  <p className="text-sm text-gray-500">
                    Section {section.section_name} • {section.academic_semester}
                  </p>
                </div>
                <span className="text-xs text-gray-400">
                  {section.enrolled_count || 0}/{section.capacity} students
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;