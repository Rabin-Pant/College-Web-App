import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  FiUser, FiMail, FiShield, FiEdit2, 
  FiUpload, FiCalendar, FiActivity, FiBook,
  FiUsers, FiSettings, FiLogOut, FiRefreshCw
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminProfile = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageError, setImageError] = useState(false);
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
      setLoading(true);
      const profileRes = await api.get('/auth/profile');
      console.log('📡 Profile data:', profileRes.data);
      console.log('📸 Profile pic path:', profileRes.data.profile_pic);
      
      setProfile(profileRes.data);
      
      // Construct image URL if profile pic exists
      if (profileRes.data.profile_pic) {
        const url = `http://127.0.0.1:5000/uploads/${profileRes.data.profile_pic}`;
        console.log('🖼️ Image URL:', url);
        setImageUrl(url);
        setImageError(false);
      } else {
        setImageUrl(null);
      }
      
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

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload a valid image file (JPEG, PNG, GIF, WEBP)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    const formData = new FormData();
    formData.append('profile_pic', file);

    try {
      setUploading(true);
      console.log('📡 Uploading profile picture...');
      
      const response = await api.post('/auth/profile/picture', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      console.log('✅ Upload response:', response.data);
      toast.success('Profile picture updated!');
      
      // Update image URL with new path
      if (response.data.profile_pic) {
        const newUrl = `http://127.0.0.1:5000/uploads/${response.data.profile_pic}`;
        console.log('🖼️ New image URL:', newUrl);
        setImageUrl(newUrl);
        setImageError(false);
        
        // Also update profile state
        setProfile(prev => ({
          ...prev,
          profile_pic: response.data.profile_pic
        }));
      }
      
      // Refresh profile data to be safe
      setTimeout(() => {
        fetchProfile();
      }, 500);
      
    } catch (error) {
      console.error('❌ Upload failed:', error);
      console.error('❌ Error response:', error.response?.data);
      toast.error(error.response?.data?.error || 'Failed to update profile picture');
    } finally {
      setUploading(false);
    }
  };

  const handleImageError = () => {
    console.error('❌ Image failed to load:', imageUrl);
    setImageError(true);
  };

  const refreshProfile = () => {
    fetchProfile();
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="h-32 bg-gradient-to-r from-purple-600 to-purple-800 relative">
          <button
            onClick={refreshProfile}
            className="absolute top-4 right-4 bg-white bg-opacity-20 text-white p-2 rounded-full hover:bg-opacity-30 transition"
            title="Refresh"
          >
            <FiRefreshCw className="h-5 w-5" />
          </button>
        </div>
        
        <div className="px-6 pb-6">
          <div className="flex flex-col md:flex-row md:items-end -mt-16">
            {/* Profile Picture */}
            <div className="relative">
              <div className="h-32 w-32 rounded-full border-4 border-white bg-white overflow-hidden shadow-xl">
                {imageUrl && !imageError ? (
                  <img 
                    src={imageUrl} 
                    alt={profile?.name || 'Admin'} 
                    className="h-full w-full object-cover"
                    onError={handleImageError}
                  />
                ) : (
                  <div className="h-full w-full bg-purple-100 flex items-center justify-center">
                    <FiUser className="h-16 w-16 text-purple-600" />
                  </div>
                )}
              </div>
              
              {/* Upload Button */}
              <label className="absolute bottom-0 right-0 bg-purple-600 text-white p-2 rounded-full cursor-pointer hover:bg-purple-700 transition-colors shadow-lg">
                <input 
                  type="file" 
                  className="hidden" 
                  accept="image/*"
                  onChange={handleProfilePicUpload}
                  disabled={uploading}
                />
                {uploading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                ) : (
                  <FiUpload className="h-4 w-4" />
                )}
              </label>
            </div>

            {/* User Info */}
            <div className="mt-4 md:mt-0 md:ml-6 flex-1">
              <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{profile?.name || 'Admin User'}</h1>
                  <div className="flex flex-wrap items-center gap-4 mt-2">
                    <p className="text-gray-600 flex items-center">
                      <FiMail className="mr-2" /> {profile?.email || 'admin@yourcollege.edu'}
                    </p>
                    <p className="text-gray-600 flex items-center">
                      <FiShield className="mr-2" /> System Administrator
                    </p>
                  </div>
                </div>
                
                {/* Edit Button */}
                <Link
                  to="/profile/edit"
                  className="mt-2 md:mt-0 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center"
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
        {/* Total Courses */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Courses</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_courses}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <FiBook className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <Link to="/admin/courses" className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-700">
            Manage Courses →
          </Link>
        </div>

        {/* Total Subjects */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Subjects</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_subjects}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <FiActivity className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <Link to="/admin/subjects" className="mt-4 inline-block text-sm text-green-600 hover:text-green-700">
            Manage Subjects →
          </Link>
        </div>

        {/* Total Sections */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Sections</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_sections}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <FiSettings className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <Link to="/admin/sections" className="mt-4 inline-block text-sm text-purple-600 hover:text-purple-700">
            Manage Sections →
          </Link>
        </div>

        {/* Total Users */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Total Users</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_users}</p>
              <div className="mt-2 text-xs">
                <span className="text-green-600">{stats.total_students} Students</span>
                <span className="mx-2 text-gray-300">•</span>
                <span className="text-blue-600">{stats.total_teachers} Teachers</span>
              </div>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
          <Link to="/admin/users" className="mt-4 inline-block text-sm text-yellow-600 hover:text-yellow-700">
            Manage Users →
          </Link>
        </div>

        {/* Teacher Assignments */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Teachers</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_teachers}</p>
            </div>
            <div className="bg-indigo-100 p-3 rounded-full">
              <FiUser className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
          <Link to="/admin/teacher-assignments" className="mt-4 inline-block text-sm text-indigo-600 hover:text-indigo-700">
            Assign Teachers →
          </Link>
        </div>

        {/* Enrollments */}
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Enrollments</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_students}</p>
            </div>
            <div className="bg-pink-100 p-3 rounded-full">
              <FiUsers className="h-6 w-6 text-pink-600" />
            </div>
          </div>
          <Link to="/admin/enrollments" className="mt-4 inline-block text-sm text-pink-600 hover:text-pink-700">
            View Enrollments →
          </Link>
        </div>
      </div>

      {/* Admin Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* About Section */}
        <div className="bg-white rounded-lg shadow-md p-6 md:col-span-2">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Admin Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500">Full Name</h3>
              <p className="mt-1 text-lg font-semibold text-gray-900">{profile?.name || 'Not set'}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500">Email Address</h3>
              <p className="mt-1 text-lg font-semibold text-gray-900">{profile?.email || 'Not set'}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500">Role</h3>
              <p className="mt-1 text-lg font-semibold text-purple-600 capitalize">{profile?.role || 'admin'}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500">Member Since</h3>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          <div className="mt-6 bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Bio</h3>
            <p className="text-gray-700">
              {profile?.bio || 'No bio added yet. Click Edit Profile to add information.'}
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link
              to="/admin/courses"
              className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors text-blue-700"
            >
              <span>📚 Manage Courses</span>
              <FiBook className="text-blue-600" />
            </Link>
            
            <Link
              to="/admin/subjects"
              className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors text-green-700"
            >
              <span>📖 Manage Subjects</span>
              <FiActivity className="text-green-600" />
            </Link>
            
            <Link
              to="/admin/sections"
              className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors text-purple-700"
            >
              <span>🏫 Manage Sections</span>
              <FiSettings className="text-purple-600" />
            </Link>
            
            <Link
              to="/admin/users"
              className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors text-yellow-700"
            >
              <span>👥 Manage Users</span>
              <FiUsers className="text-yellow-600" />
            </Link>
            
            <Link
              to="/admin/reports"
              className="flex items-center justify-between p-3 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors text-orange-700"
            >
              <span>📊 View Reports</span>
              <FiActivity className="text-orange-600" />
            </Link>
            
            <Link
              to="/admin/settings"
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-gray-700"
            >
              <span>⚙️ System Settings</span>
              <FiSettings className="text-gray-600" />
            </Link>
            
            <Link
              to="/profile/edit"
              className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors text-indigo-700 mt-4"
            >
              <span>✏️ Edit Profile</span>
              <FiEdit2 className="text-indigo-600" />
            </Link>
            
            <button
              onClick={logout}
              className="w-full flex items-center justify-between p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors text-red-600 mt-2"
            >
              <span>🚪 Sign Out</span>
              <FiLogOut className="text-red-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Profile updated</p>
              <p className="text-xs text-gray-500">Just now</p>
            </div>
          </div>
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Settings changed</p>
              <p className="text-xs text-gray-500">2 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminProfile;