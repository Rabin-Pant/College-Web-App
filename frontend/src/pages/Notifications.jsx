import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  FiBell, FiMail, FiCheck, FiX, FiClock, 
  FiMessageSquare, FiBook, FiUsers, FiTrash2 
} from 'react-icons/fi';
import Loader from '../components/common/Loader';
import toast from 'react-hot-toast';

const Notifications = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications/?limit=100');
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
    } catch (error) {
      console.error('Failed to mark as read:', error);
      toast.error('Failed to mark notification');
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      toast.success('All notifications marked as read');
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      toast.error('Failed to mark notifications');
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await api.delete(`/notifications/${notificationId}`);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      toast.success('Notification deleted');
    } catch (error) {
      console.error('Failed to delete notification:', error);
      toast.error(error.response?.data?.error || 'Failed to delete notification');
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'assignment_created':
        return <FiBook className="h-5 w-5 text-blue-500" />;
      case 'deadline_approaching':
        return <FiClock className="h-5 w-5 text-yellow-500" />;
      case 'submission_graded':
        return <FiCheck className="h-5 w-5 text-green-500" />;
      case 'class_announcement':
        return <FiMessageSquare className="h-5 w-5 text-purple-500" />;
      case 'class_joined':
        return <FiUsers className="h-5 w-5 text-indigo-500" />;
      case 'system_announcement':
        return <FiBell className="h-5 w-5 text-red-500" />;
      default:
        return <FiMail className="h-5 w-5 text-gray-500" />;
    }
  };

  const getTimeAgo = (dateString) => {
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
  };

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return !n.is_read;
    if (filter === 'read') return n.is_read;
    return true;
  });

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) return <Loader />;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div className="flex items-center">
            <FiBell className="h-6 w-6 text-primary-600 mr-2" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
              <p className="text-gray-600 mt-1">
                You have {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          
          {/* Only show Mark All Read button for non-students when there are unread notifications */}
          {user?.role !== 'student' && unreadCount > 0 && (
            <div className="mt-4 md:mt-0">
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center"
              >
                <FiCheck className="mr-2" />
                Mark All Read
              </button>
            </div>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="mt-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setFilter('all')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'all'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All ({notifications.length})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'unread'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Unread ({unreadCount})
            </button>
            <button
              onClick={() => setFilter('read')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'read'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Read ({notifications.length - unreadCount})
            </button>
          </nav>
        </div>
      </div>

      {/* Notifications List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {filteredNotifications.length === 0 ? (
          <div className="p-12 text-center">
            <FiBell className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No notifications</h3>
            <p className="mt-2 text-gray-500">
              {filter === 'unread' 
                ? 'You have no unread notifications' 
                : 'You haven\'t received any notifications yet'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-6 hover:bg-gray-50 transition ${
                  !notification.is_read ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0 mt-1">
                    {getIcon(notification.type)}
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-gray-900">
                        {notification.title}
                      </h3>
                      <span className="text-xs text-gray-500">
                        {getTimeAgo(notification.created_at)}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-600">
                      {notification.message}
                    </p>
                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        {notification.sender_name && (
                          <span className="text-xs text-gray-500">
                            From: {notification.sender_name}
                          </span>
                        )}
                        {notification.class_name && (
                          <span className="text-xs text-gray-500">
                            Class: {notification.class_name}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {!notification.is_read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="text-xs text-primary-600 hover:text-primary-700 flex items-center"
                          >
                            <FiCheck className="mr-1" />
                            Mark read
                          </button>
                        )}
                        {/* Only show delete button for admins */}
                        {user?.role === 'admin' && (
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="text-xs text-red-600 hover:text-red-700 flex items-center"
                          >
                            <FiX className="mr-1" />
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                    {notification.link && (
                      <Link
                        to={notification.link}
                        className="mt-2 inline-block text-xs text-primary-600 hover:text-primary-700"
                      >
                        View details →
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;