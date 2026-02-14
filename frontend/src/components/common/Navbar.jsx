import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import NotificationBell from '../notifications/NotificationBell';
import { 
  FiLogOut, FiUser, FiBook, FiHome, FiUsers, 
  FiClipboard, FiSettings, FiMenu, FiX,
  FiChevronDown, FiCalendar, FiBell
} from 'react-icons/fi';

const Navbar = () => {
  const { user, isAuthenticated, logout, isTeacher, isStudent, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
    setProfileDropdownOpen(false);
  };

  const getDashboardLink = () => {
    if (!user) return '/';
    switch (user.role) {
      case 'teacher': return '/teacher/dashboard';
      case 'student': return '/student/dashboard';
      case 'admin': return '/admin/dashboard';
      default: return '/dashboard';
    }
  };

  const closeMenus = () => {
    setMobileMenuOpen(false);
    setProfileDropdownOpen(false);
  };

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to={getDashboardLink()} className="flex items-center space-x-2" onClick={closeMenus}>
            <FiBook className="h-6 w-6 text-primary-600" />
            <span className="font-bold text-xl text-gray-800">CollegeApp</span>
          </Link>

          {/* Desktop Navigation - ONLY ONCE */}
          <div className="hidden md:flex items-center space-x-6">
            {isAuthenticated && (
              <>
                <Link to={getDashboardLink()} className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                  <FiHome className="h-4 w-4" />
                  <span>Dashboard</span>
                </Link>
                
                <Link to="/profile" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                  <FiUser className="h-4 w-4" />
                  <span>Profile</span>
                </Link>
                
                {isStudent && (
                  <>
                    <Link to="/student/sections" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                      <FiBook className="h-4 w-4" />
                      <span>My Sections</span>
                    </Link>
                    <Link to="/student/available-sections" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                      <FiClipboard className="h-4 w-4" />
                      <span>Browse Sections</span>
                    </Link>
                  </>
                )}

                {isTeacher && (
                  <>
                    <Link to="/teacher/sections" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                      <FiBook className="h-4 w-4" />
                      <span>My Sections</span>
                    </Link>
                    <Link to="/teacher/schedule" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                      <FiCalendar className="h-4 w-4" />
                      <span>Schedule</span>
                    </Link>
                  </>
                )}

                {isAdmin && (
                  <Link to="/admin/users" className="flex items-center space-x-1 text-gray-600 hover:text-gray-900">
                    <FiUsers className="h-4 w-4" />
                    <span>Users</span>
                  </Link>
                )}
              </>
            )}
          </div>

          {/* Right side - Notification Bell & User Menu */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && (
              <>
                <NotificationBell />

                {/* User Profile Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                    className="flex items-center space-x-2 focus:outline-none"
                  >
                    <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center hover:bg-primary-200 transition">
                      {user?.profile_pic ? (
                        <img src={user.profile_pic} alt={user.name} className="h-8 w-8 rounded-full object-cover" />
                      ) : (
                        <FiUser className="h-4 w-4 text-primary-600" />
                      )}
                    </div>
                    <div className="hidden md:block text-left">
                      <p className="text-sm font-medium text-gray-900">{user?.name?.split(' ')[0] || 'User'}</p>
                      <p className="text-xs text-gray-500 capitalize">{user?.role || ''}</p>
                    </div>
                    <FiChevronDown className="hidden md:block h-4 w-4 text-gray-500" />
                  </button>

                  {profileDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 border border-gray-200 z-50">
                      <Link
                        to="/profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setProfileDropdownOpen(false)}
                      >
                        <FiUser className="inline mr-2 h-4 w-4" />
                        My Profile
                      </Link>
                      <Link
                        to="/profile/edit"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setProfileDropdownOpen(false)}
                      >
                        <FiSettings className="inline mr-2 h-4 w-4" />
                        Edit Profile
                      </Link>
                      <Link
                        to="/profile/change-password"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setProfileDropdownOpen(false)}
                      >
                        <FiClipboard className="inline mr-2 h-4 w-4" />
                        Change Password
                      </Link>
                      <hr className="my-1 border-gray-200" />
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                      >
                        <FiLogOut className="inline mr-2 h-4 w-4" />
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}

            {!isAuthenticated && (
              <div className="flex items-center space-x-4">
                <Link to="/login" className="text-gray-600 hover:text-gray-900">
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  Sign Up
                </Link>
              </div>
            )}

            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden text-gray-600 hover:text-gray-900"
            >
              {mobileMenuOpen ? <FiX className="h-6 w-6" /> : <FiMenu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu - ONLY ONCE */}
        {mobileMenuOpen && isAuthenticated && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-3">
              <Link 
                to={getDashboardLink()} 
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                onClick={closeMenus}
              >
                <FiHome className="h-4 w-4" />
                <span>Dashboard</span>
              </Link>
              
              <Link 
                to="/profile" 
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                onClick={closeMenus}
              >
                <FiUser className="h-4 w-4" />
                <span>Profile</span>
              </Link>
              
              {isStudent && (
                <>
                  <Link 
                    to="/student/sections" 
                    className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={closeMenus}
                  >
                    <FiBook className="h-4 w-4" />
                    <span>My Sections</span>
                  </Link>
                  <Link 
                    to="/student/available-sections" 
                    className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={closeMenus}
                  >
                    <FiClipboard className="h-4 w-4" />
                    <span>Browse Sections</span>
                  </Link>
                </>
              )}

              {isTeacher && (
                <>
                  <Link 
                    to="/teacher/sections" 
                    className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={closeMenus}
                  >
                    <FiBook className="h-4 w-4" />
                    <span>My Sections</span>
                  </Link>
                  <Link 
                    to="/teacher/schedule" 
                    className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={closeMenus}
                  >
                    <FiCalendar className="h-4 w-4" />
                    <span>Schedule</span>
                  </Link>
                </>
              )}

              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-red-600 hover:text-red-700 px-2 py-1"
              >
                <FiLogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;