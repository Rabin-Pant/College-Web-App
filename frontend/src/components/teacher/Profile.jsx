import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  FiUser, FiMail, FiBook, FiBriefcase, FiClock,
  FiEdit2, FiAward, FiUsers, FiUpload, FiMapPin,
  FiCalendar, FiCheckCircle, FiLogOut,
  FiSettings
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const TeacherProfile = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState({
    total_sections: 0,
    total_students: 0,
    total_assignments: 0,
    pending_grading: 0,
    total_materials: 0
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const profileRes = await api.get('/auth/profile');
      console.log('📡 Profile data:', profileRes.data);
      console.log('📸 Profile pic path:', profileRes.data.profile_pic);
      setProfile(profileRes.data);
      
      try {
        const [sectionsRes, statsRes, gradingRes] = await Promise.all([
          api.get('/teacher/sections/'),
          api.get('/teacher/sections/stats'),
          api.get('/teacher/grading/pending')
        ]);
        
        setStats({
          total_sections: sectionsRes.data.total || 0,
          total_students: statsRes.data.total_students || 0,
          total_assignments: statsRes.data.total_assignments || 0,
          pending_grading: gradingRes.data.total || 0,
          total_materials: statsRes.data.total_materials || 0
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

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload a valid image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    const formData = new FormData();
    formData.append('profile_pic', file);

    try {
      setUploading(true);
      const response = await api.post('/auth/profile/picture', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      console.log('✅ Upload response:', response.data);
      toast.success('Profile picture updated!');
      fetchProfile();
    } catch (error) {
      console.error('❌ Upload error:', error);
      toast.error(error.response?.data?.error || 'Failed to update profile picture');
    } finally {
      setUploading(false);
    }
  };

  const getImageUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    return `http://127.0.0.1:5000/uploads/${path}`;
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="h-32 bg-gradient-to-r from-blue-600 to-blue-800"></div>
        <div className="px-6 pb-6">
          <div className="flex flex-col md:flex-row md:items-end -mt-16">
            <div className="relative">
              <div className="h-32 w-32 rounded-full border-4 border-white bg-white overflow-hidden">
                {profile?.profile_pic ? (
                  <img 
                    src={getImageUrl(profile.profile_pic)}
                    alt={profile.name}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      console.error('Image failed to load:', e.target.src);
                      e.target.onerror = null;
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = `<div class="h-full w-full bg-blue-100 flex items-center justify-center"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" class="h-16 w-16 text-blue-600" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"></path></svg></div>`;
                    }}
                  />
                ) : (
                  <div className="h-full w-full bg-blue-100 flex items-center justify-center">
                    <FiUser className="h-16 w-16 text-blue-600" />
                  </div>
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700 transition">
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
            <div className="mt-4 md:mt-0 md:ml-6 flex-1">
              <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{profile?.name || 'Teacher'}</h1>
                  <p className="text-gray-600 mt-1 flex items-center">
                    <FiMail className="mr-2" /> {profile?.email || 'teacher@yourcollege.edu'}
                  </p>
                  <p className="text-gray-600 mt-1 flex items-center">
                    <FiBriefcase className="mr-2" /> {profile?.department || 'Department not set'}
                  </p>
                </div>
                <Link
                  to="/profile/edit"
                  className="mt-2 md:mt-0 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-xs">My Sections</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_sections}</p>
            </div>
            <div className="bg-blue-100 p-2 rounded-full">
              <FiBook className="h-5 w-5 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-xs">Total Students</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_students}</p>
            </div>
            <div className="bg-green-100 p-2 rounded-full">
              <FiUsers className="h-5 w-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-xs">Assignments</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_assignments}</p>
            </div>
            <div className="bg-purple-100 p-2 rounded-full">
              <FiAward className="h-5 w-5 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-xs">Materials</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_materials}</p>
            </div>
            <div className="bg-yellow-100 p-2 rounded-full">
              <FiUpload className="h-5 w-5 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-xs">Pending Grading</p>
              <p className="text-2xl font-bold text-orange-600">{stats.pending_grading}</p>
            </div>
            <div className="bg-orange-100 p-2 rounded-full">
              <FiClock className="h-5 w-5 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Profile Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 md:col-span-2">
          <h2 className="text-xl font-bold text-gray-900 mb-4">About Me</h2>
          <p className="text-gray-700">
            {profile?.bio || 'No bio added yet.'}
          </p>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Employee ID</h3>
              <p className="mt-1 text-gray-900">{profile?.employee_id || 'Not assigned'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Department</h3>
              <p className="mt-1 text-gray-900">{profile?.department || 'Not set'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Office Hours</h3>
              <p className="mt-1 text-gray-900">{profile?.office_hours || 'Not set'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Member Since</h3>
              <p className="mt-1 text-gray-900">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          {profile?.qualifications && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-500">Qualifications</h3>
              <p className="mt-1 text-gray-700">{profile.qualifications}</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/teacher/dashboard"
              className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 text-blue-700"
            >
              <span>My Dashboard</span>
              <FiBook className="text-blue-600" />
            </Link>
            <Link
              to="/teacher/sections"
              className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 text-green-700"
            >
              <span>My Sections</span>
              <FiUsers className="text-green-600" />
            </Link>
            <Link
              to="/teacher/schedule"
              className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 text-purple-700"
            >
              <span>My Schedule</span>
              <FiCalendar className="text-purple-600" />
            </Link>
            <Link
              to="/profile/edit"
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <span>Edit Profile</span>
              <FiSettings className="text-gray-400" />
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

export default TeacherProfile;