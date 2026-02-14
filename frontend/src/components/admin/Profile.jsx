import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  FiUser, FiMail, FiShield, FiEdit2, 
  FiUpload, FiCalendar, FiActivity, FiBook,
  FiUsers, FiSettings, FiLogOut
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminProfile = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState({
    total_courses: 0,
    total_subjects: 0,
    total_sections: 0,
    total_users: 0,
    total_teachers: 0,
    total_students: 0
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      // Fetch user profile
      const profileRes = await api.get('/auth/profile');
      setProfile(profileRes.data);
      
      // Fetch stats from admin endpoints
      try {
        const [coursesRes, subjectsRes, sectionsRes, usersRes] = await Promise.all([
          api.get('/admin/courses/?limit=1'),
          api.get('/admin/subjects/?limit=1'),
          api.get('/admin/sections/?limit=1'),
          api.get('/admin/users/?limit=1')
        ]);
        
        setStats({
          total_courses: coursesRes.data.total || 0,
          total_subjects: subjectsRes.data.total || 0,
          total_sections: sectionsRes.data.total || 0,
          total_users: usersRes.data.total || 0,
          total_teachers: usersRes.data.users?.filter(u => u.role === 'teacher').length || 0,
          total_students: usersRes.data.users?.filter(u => u.role === 'student').length || 0
        });
      } catch (statsError) {
        console.error('Failed to fetch stats:', statsError);
        // Set default stats if endpoints fail
        setStats({
          total_courses: 0,
          total_subjects: 0,
          total_sections: 0,
          total_users: 0,
          total_teachers: 0,
          total_students: 0
        });
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleProfilePicUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('profile_pic', file);

    try {
      await api.put('/auth/profile', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Profile picture updated!');
      fetchProfile();
    } catch (error) {
      toast.error('Failed to update profile picture');
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="h-32 bg-gradient-to-r from-purple-600 to-purple-800"></div>
        <div className="px-6 pb-6">
          <div className="flex flex-col md:flex-row md:items-end -mt-16">
            <div className="relative">
              <div className="h-32 w-32 rounded-full border-4 border-white bg-white overflow-hidden">
                {profile?.profile_pic ? (
                  <img 
                    src={profile.profile_pic} 
                    alt={profile.name} 
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="h-full w-full bg-purple-100 flex items-center justify-center">
                    <FiUser className="h-16 w-16 text-purple-600" />
                  </div>
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-purple-600 text-white p-2 rounded-full cursor-pointer hover:bg-purple-700">
                <FiUpload className="h-4 w-4" />
                <input 
                  type="file" 
                  className="hidden" 
                  accept="image/*"
                  onChange={handleProfilePicUpload}
                />
              </label>
            </div>
            <div className="mt-4 md:mt-0 md:ml-6 flex-1">
              <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{profile?.name || 'Admin User'}</h1>
                  <p className="text-gray-600 mt-1 flex items-center">
                    <FiMail className="mr-2" /> {profile?.email || 'admin@yourcollege.edu'}
                  </p>
                  <p className="text-gray-600 mt-1 flex items-center">
                    <FiShield className="mr-2" /> System Administrator
                  </p>
                </div>
                <Link
                  to="/profile/edit"
                  className="mt-2 md:mt-0 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center"
                >
                  <FiEdit2 className="mr-2" />
                  Edit Profile
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
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
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Subjects</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_subjects}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <FiActivity className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Sections</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_sections}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <FiSettings className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Users</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_users}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Teachers</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_teachers}</p>
            </div>
            <div className="bg-indigo-100 p-3 rounded-full">
              <FiUser className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Students</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_students}</p>
            </div>
            <div className="bg-pink-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-pink-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Admin Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 md:col-span-2">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Admin Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Full Name</h3>
              <p className="mt-1 text-gray-900">{profile?.name || 'Not set'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Email Address</h3>
              <p className="mt-1 text-gray-900">{profile?.email || 'Not set'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Role</h3>
              <p className="mt-1 text-gray-900 capitalize">{profile?.role || 'admin'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Member Since</h3>
              <p className="mt-1 text-gray-900">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-500">Bio</h3>
            <p className="mt-1 text-gray-700">
              {profile?.bio || 'No bio added yet.'}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/admin/courses"
              className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 text-blue-700"
            >
              <span>Manage Courses</span>
              <FiBook className="text-blue-600" />
            </Link>
            <Link
              to="/admin/subjects"
              className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 text-green-700"
            >
              <span>Manage Subjects</span>
              <FiActivity className="text-green-600" />
            </Link>
            <Link
              to="/admin/sections"
              className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 text-purple-700"
            >
              <span>Manage Sections</span>
              <FiSettings className="text-purple-600" />
            </Link>
            <Link
              to="/admin/users"
              className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg hover:bg-yellow-100 text-yellow-700"
            >
              <span>Manage Users</span>
              <FiUsers className="text-yellow-600" />
            </Link>
            <Link
              to="/profile/edit"
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <span>Edit Profile</span>
              <FiEdit2 className="text-gray-400" />
            </Link>
            <button
              onClick={logout}
              className="w-full flex items-center justify-between p-3 bg-red-50 rounded-lg hover:bg-red-100 text-red-600"
            >
              <span>Sign Out</span>
              <FiLogOut className="text-red-600" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminProfile;