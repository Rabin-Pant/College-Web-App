import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import SendNotificationModal from './SendNotificationModal';
import { 
  FiBell, FiBellOff, FiCheck, FiX, FiMail, 
  FiMessageSquare, FiBook, FiUsers, FiClock,
  FiSend, FiChevronRight
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const NotificationBell = () => {
  const { user, isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const dropdownRef = useRef(null);

  // Debug logging
  console.log('🔔 NotificationBell rendered');
  console.log('👤 User:', user);
  console.log('🔑 isAuthenticated:', isAuthenticated);

  useEffect(() => {
    console.log('📡 NotificationBell mounted');
    if (isAuthenticated) {
      console.log('✅ User is authenticated, fetching notifications...');
      fetchNotifications();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    } else {
      console.log('❌ User not authenticated');
    }
  }, [isAuthenticated]);

  useEffect(() => {
    console.log('📊 Notifications state updated:', notifications);
    console.log('🔢 Unread count:', unreadCount);
  }, [notifications, unreadCount]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setApiError(null);
      console.log('📡 Fetching notifications from API...');
      
      const response = await api.get('/notifications/?limit=5');
      
      console.log('✅ API Response:', response);
      console.log('✅ Response data:', response.data);
      console.log('✅ Notifications array:', response.data.notifications);
      console.log('✅ Unread count:', response.data.unread_count);
      
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
      
      if (response.data.notifications?.length === 0) {
        console.log('ℹ️ No notifications returned from API');
      }
    } catch (error) {
      console.error('❌ Failed to fetch notifications:', error);
      console.error('❌ Error response:', error.response);
      console.error('❌ Error status:', error.response?.status);
      console.error('❌ Error data:', error.response?.data);
      setApiError(error.message);
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      console.log('🔢 Fetching unread count...');
      const response = await api.get('/notifications/unread-count');
      console.log('✅ Unread count response:', response.data);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('❌ Failed to fetch unread count:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      console.log('📝 Marking notification as read:', notificationId);
      await api.put(`/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('❌ Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      console.log('📝 Marking all notifications as read');
      await api.put('/notifications/read-all');
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      console.error('❌ Failed to mark all as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      console.log('🗑️ Deleting notification:', notificationId);
      await api.delete(`/notifications/${notificationId}`);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      if (notifications.find(n => n.id === notificationId)?.is_read === false) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
      toast.success('Notification deleted');
    } catch (error) {
      console.error('❌ Failed to delete notification:', error);
      toast.error(error.response?.data?.error || 'Failed to delete notification');
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'assignment_created':
        return <FiBook className="h-4 w-4 text-blue-500" />;
      case 'deadline_approaching':
        return <FiClock className="h-4 w-4 text-yellow-500" />;
      case 'submission_graded':
        return <FiCheck className="h-4 w-4 text-green-500" />;
      case 'class_announcement':
      case 'teacher_announcement':
        return <FiMessageSquare className="h-4 w-4 text-purple-500" />;
      case 'system_announcement':
        return <FiBell className="h-4 w-4 text-red-500" />;
      case 'class_joined':
        return <FiUsers className="h-4 w-4 text-indigo-500" />;
      default:
        return <FiMail className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTimeAgo = (dateString) => {
    if (!dateString) return 'unknown';
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const seconds = Math.floor((now - date) / 1000);
      
      if (seconds < 60) return 'just now';
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) return `${minutes}m ago`;
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      if (days < 7) return `${days}d ago`;
      return date.toLocaleDateString();
    } catch (e) {
      return 'unknown';
    }
  };

  const handleSendClick = () => {
    setShowDropdown(false);
    setShowSendModal(true);
  };

  if (!isAuthenticated) {
    console.log('🚫 Not authenticated, returning null');
    return null;
  }

  // TEMPORARY: Show mock data if no notifications (for testing)
  const displayNotifications = notifications.length > 0 ? notifications : [
    {
      id: 999,
      title: "Debug Mode",
      message: "No real notifications. Check console for API errors.",
      created_at: new Date().toISOString(),
      is_read: false,
      type: "system_announcement",
      sender_name: "System"
    }
  ];

  return (
    <>
      <div className="relative" ref={dropdownRef}>
        {/* Bell Icon */}
        <button
          onClick={() => {
            console.log('🔔 Bell clicked');
            setShowDropdown(!showDropdown);
          }}
          className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none transition-colors"
          title="Notifications"
        >
          {unreadCount > 0 ? (
            <>
              <FiBell className="h-5 w-5" />
              <span className="absolute top-0 right-0 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            </>
          ) : (
            <FiBellOff className="h-5 w-5" />
          )}
        </button>

        {/* Dropdown */}
        {showDropdown && (
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl overflow-hidden z-50 border border-gray-200">
            {/* Header */}
            <div className="p-3 border-b border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-gray-700">
                  Notifications 
                  {apiError && <span className="ml-2 text-xs text-red-500">(Error)</span>}
                </h3>
                {unreadCount > 0 && user?.role !== 'student' && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              {apiError && (
                <div className="mt-1 text-xs text-red-500">
                  API Error: {apiError}
                  <button 
                    onClick={fetchNotifications}
                    className="ml-2 text-primary-600 underline"
                  >
                    Retry
                  </button>
                </div>
              )}
            </div>

            {/* Send Notification Button for Teachers/Admins */}
            {(user?.role === 'teacher' || user?.role === 'admin') && (
              <div className="p-2 border-b border-gray-200 bg-green-50">
                <button
                  onClick={handleSendClick}
                  className="w-full flex items-center justify-center px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                >
                  <FiSend className="mr-2" />
                  Send Notification
                </button>
              </div>
            )}

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="p-4 text-center text-gray-500">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-sm">Loading...</p>
                </div>
              ) : notifications.length === 0 && !apiError ? (
                <div className="p-8 text-center text-gray-500">
                  <FiBellOff className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm">No notifications</p>
                  <p className="text-xs text-gray-400 mt-1">You're all caught up!</p>
                  <button 
                    onClick={fetchNotifications}
                    className="mt-2 text-xs text-primary-600 hover:text-primary-700"
                  >
                    Refresh
                  </button>
                </div>
              ) : (
                displayNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-3 border-b border-gray-100 hover:bg-gray-50 transition ${
                      !notification.is_read ? 'bg-blue-50/50' : ''
                    }`}
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mt-1">
                        {getIcon(notification.type)}
                      </div>
                      <div className="ml-3 flex-1">
                        <div className="flex justify-between items-start">
                          <p className="text-xs font-medium text-gray-900">
                            {notification.title}
                          </p>
                          {!notification.is_read && (
                            <span className="w-2 h-2 bg-blue-600 rounded-full ml-2 flex-shrink-0"></span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-xs text-gray-400">
                            {getTimeAgo(notification.created_at)}
                            {notification.sender_name && ` • by ${notification.sender_name}`}
                          </span>
                          <div className="flex space-x-2">
                            {!notification.is_read && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                              >
                                Mark read
                              </button>
                            )}
                            {/* Only show delete button for admins */}
                            {user?.role === 'admin' && (
                              <button
                                onClick={() => deleteNotification(notification.id)}
                                className="text-xs text-red-600 hover:text-red-700 font-medium"
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        </div>
                        {notification.link && (
                          <Link
                            to={notification.link}
                            className="mt-2 text-xs text-primary-600 hover:text-primary-700 inline-flex items-center"
                            onClick={() => setShowDropdown(false)}
                          >
                            View details
                            <FiChevronRight className="ml-1 h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-gray-200 bg-gray-50 text-center">
              <Link
                to="/notifications"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium inline-flex items-center"
                onClick={() => setShowDropdown(false)}
              >
                View all notifications
                <FiChevronRight className="ml-1 h-4 w-4" />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Send Notification Modal */}
      <SendNotificationModal
        isOpen={showSendModal}
        onClose={() => setShowSendModal(false)}
      />
    </>
  );
};

export default NotificationBell;