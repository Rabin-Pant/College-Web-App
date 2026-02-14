import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  FiSend, FiX, FiUsers, FiBook, FiGlobe, 
  FiMail, FiBell, FiUser, FiSearch
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const SendNotificationModal = ({ isOpen, onClose, sectionId, sectionName }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [priority, setPriority] = useState('normal');
  const [recipientType, setRecipientType] = useState('class');
  const [selectedClass, setSelectedClass] = useState(sectionId || '');
  const [classes, setClasses] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredUsers, setFilteredUsers] = useState([]);

  useEffect(() => {
    if (isOpen) {
      if (sectionId) {
        setSelectedClass(sectionId);
      }
      
      if (user?.role === 'teacher') {
        fetchTeacherSections();
      } else if (user?.role === 'admin') {
        fetchAllSections();
        fetchAllUsers();
      }
    }
  }, [isOpen, user, sectionId]);

  useEffect(() => {
    if (searchTerm) {
      const filtered = users.filter(u => 
        u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredUsers(filtered);
    } else {
      setFilteredUsers(users);
    }
  }, [searchTerm, users]);

  // For teachers - fetch their assigned sections
  const fetchTeacherSections = async () => {
    try {
      const response = await api.get('/teacher/sections/');
      setClasses(response.data.sections || []);
    } catch (error) {
      console.error('Failed to fetch sections:', error);
      toast.error('Failed to load sections');
    }
  };

  // For admins - fetch all sections
  const fetchAllSections = async () => {
    try {
      const response = await api.get('/admin/sections/');
      setClasses(response.data.sections || []);
    } catch (error) {
      console.error('Failed to fetch sections:', error);
      toast.error('Failed to load sections');
    }
  };

  const fetchAllUsers = async () => {
    try {
      const response = await api.get('/admin/users?limit=100');
      setUsers(response.data.users || []);
      setFilteredUsers(response.data.users || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast.error('Failed to load users');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim() || !message.trim()) {
      toast.error('Title and message are required');
      return;
    }

    setLoading(true);

    try {
      let endpoint = '';
      let payload = { 
        title: title.trim(), 
        message: message.trim(), 
        priority 
      };
      let recipients = 0;

      switch (recipientType) {
        case 'class':
          if (!selectedClass) {
            toast.error('Please select a class/section');
            setLoading(false);
            return;
          }
          endpoint = `/notifications/send-to-class/${selectedClass}`;
          console.log('📨 Sending to class/section:', selectedClass);
          break;
          
        case 'all-classes':
          endpoint = '/notifications/send-to-all-classes';
          break;
          
        case 'all-students':
          if (user?.role !== 'admin') {
            toast.error('Only admins can send to all students');
            setLoading(false);
            return;
          }
          endpoint = '/notifications/send-to-all-students';
          break;
          
        case 'all-teachers':
          if (user?.role !== 'admin') {
            toast.error('Only admins can send to all teachers');
            setLoading(false);
            return;
          }
          endpoint = '/notifications/send-to-all-teachers';
          break;
          
        case 'all-users':
          if (user?.role !== 'admin') {
            toast.error('Only admins can send to all users');
            setLoading(false);
            return;
          }
          endpoint = '/notifications/send-to-all-users';
          break;
          
        case 'specific-user':
          if (!selectedUser) {
            toast.error('Please select a user');
            setLoading(false);
            return;
          }
          endpoint = `/notifications/send-to-user/${selectedUser}`;
          break;
          
        default:
          toast.error('Invalid recipient type');
          setLoading(false);
          return;
      }

      console.log('📨 Sending notification:', { endpoint, payload });
      const response = await api.post(endpoint, payload);
      
      recipients = response.data.recipients || 1;
      console.log('✅ Notification sent to', recipients, 'recipients');
      
      toast.success(`✅ Notification sent to ${recipients} recipient(s)`);
      resetForm();
      onClose();
    } catch (error) {
      console.error('❌ Failed to send notification:', error);
      console.error('❌ Error response:', error.response?.data);
      toast.error(error.response?.data?.error || 'Failed to send notification');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setMessage('');
    setPriority('normal');
    setRecipientType('class');
    setSelectedClass(sectionId || '');
    setSelectedUser('');
    setSearchTerm('');
  };

  const getRecipientDescription = () => {
    switch (recipientType) {
      case 'class':
        const cls = classes.find(c => c.section_id === parseInt(selectedClass) || c.id === parseInt(selectedClass));
        return cls ? `Section: ${cls.subject_name || cls.subject_code} - ${cls.section_name || 'Section'}` : '';
      case 'all-classes':
        return 'All your classes/sections';
      case 'all-students':
        return 'All students in system';
      case 'all-teachers':
        return 'All teachers in system';
      case 'all-users':
        return 'All users (students, teachers, admins)';
      case 'specific-user':
        const usr = users.find(u => u.id === parseInt(selectedUser));
        return usr ? `User: ${usr.name} (${usr.role})` : '';
      default:
        return '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white z-10">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <FiSend className="mr-2 text-primary-600" />
            Send Notification
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="Close"
          >
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Recipient Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Send to:
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setRecipientType('class')}
                className={`p-3 rounded-lg border-2 text-left transition ${
                  recipientType === 'class'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <FiBook className={`h-5 w-5 mb-2 ${
                  recipientType === 'class' ? 'text-primary-600' : 'text-gray-400'
                }`} />
                <p className={`text-sm font-medium ${
                  recipientType === 'class' ? 'text-primary-600' : 'text-gray-700'
                }`}>
                  Specific Section
                </p>
              </button>

              <button
                type="button"
                onClick={() => setRecipientType('all-classes')}
                className={`p-3 rounded-lg border-2 text-left transition ${
                  recipientType === 'all-classes'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <FiUsers className={`h-5 w-5 mb-2 ${
                  recipientType === 'all-classes' ? 'text-primary-600' : 'text-gray-400'
                }`} />
                <p className={`text-sm font-medium ${
                  recipientType === 'all-classes' ? 'text-primary-600' : 'text-gray-700'
                }`}>
                  All My Sections
                </p>
              </button>

              {user?.role === 'admin' && (
                <>
                  <button
                    type="button"
                    onClick={() => setRecipientType('all-students')}
                    className={`p-3 rounded-lg border-2 text-left transition ${
                      recipientType === 'all-students'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FiUsers className={`h-5 w-5 mb-2 ${
                      recipientType === 'all-students' ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <p className={`text-sm font-medium ${
                      recipientType === 'all-students' ? 'text-primary-600' : 'text-gray-700'
                    }`}>
                      All Students
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRecipientType('all-teachers')}
                    className={`p-3 rounded-lg border-2 text-left transition ${
                      recipientType === 'all-teachers'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FiUser className={`h-5 w-5 mb-2 ${
                      recipientType === 'all-teachers' ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <p className={`text-sm font-medium ${
                      recipientType === 'all-teachers' ? 'text-primary-600' : 'text-gray-700'
                    }`}>
                      All Teachers
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRecipientType('all-users')}
                    className={`p-3 rounded-lg border-2 text-left transition ${
                      recipientType === 'all-users'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FiGlobe className={`h-5 w-5 mb-2 ${
                      recipientType === 'all-users' ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <p className={`text-sm font-medium ${
                      recipientType === 'all-users' ? 'text-primary-600' : 'text-gray-700'
                    }`}>
                      All Users
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRecipientType('specific-user')}
                    className={`p-3 rounded-lg border-2 text-left transition ${
                      recipientType === 'specific-user'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <FiUser className={`h-5 w-5 mb-2 ${
                      recipientType === 'specific-user' ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <p className={`text-sm font-medium ${
                      recipientType === 'specific-user' ? 'text-primary-600' : 'text-gray-700'
                    }`}>
                      Specific User
                    </p>
                  </button>
                </>
              )}
            </div>

            {/* Recipient Summary */}
            {getRecipientDescription() && (
              <p className="mt-2 text-sm text-primary-600">
                📨 Sending to: {getRecipientDescription()}
              </p>
            )}
          </div>

          {/* Section/Class Selection */}
          {recipientType === 'class' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Section
              </label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="input-field"
                required
              >
                <option value="">-- Choose a section --</option>
                {classes.map(cls => (
                  <option key={cls.section_id || cls.id} value={cls.section_id || cls.id}>
                    {cls.subject_code || cls.subject_code} - {cls.subject_name} 
                    {cls.section_name ? ` (Section ${cls.section_name})` : ''}
                    {cls.academic_semester ? ` • ${cls.academic_semester}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* User Selection */}
          {recipientType === 'specific-user' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search and Select User
              </label>
              <div className="relative mb-3">
                <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 input-field w-full"
                />
              </div>
              <div className="border border-gray-200 rounded-lg max-h-48 overflow-y-auto">
                {filteredUsers.length === 0 ? (
                  <p className="p-4 text-center text-gray-500">No users found</p>
                ) : (
                  filteredUsers.map(user => (
                    <label
                      key={user.id}
                      className={`flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0 ${
                        selectedUser === user.id.toString() ? 'bg-primary-50' : ''
                      }`}
                    >
                      <input
                        type="radio"
                        name="user"
                        value={user.id}
                        checked={selectedUser === user.id.toString()}
                        onChange={(e) => setSelectedUser(e.target.value)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email} • {user.role}</p>
                      </div>
                    </label>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Notification Details */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input-field"
              placeholder="e.g., System Maintenance, Holiday Announcement, Important Update"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message <span className="text-red-500">*</span>
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={4}
              className="input-field"
              placeholder="Enter your notification message..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="input-field"
            >
              <option value="low">🔵 Low</option>
              <option value="normal">🟢 Normal</option>
              <option value="high">🔴 High</option>
            </select>
          </div>

          {/* Preview */}
          {(title || message) && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Preview:</h3>
              <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center">
                  <FiBell className={`mr-2 ${
                    priority === 'high' ? 'text-red-500' : 
                    priority === 'low' ? 'text-gray-400' : 'text-primary-500'
                  }`} />
                  <span className="font-medium text-gray-900">
                    {title || 'Notification Title'}
                  </span>
                  <span className="ml-auto text-xs text-gray-400">
                    Just now
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-600">
                  {message || 'Your message will appear here...'}
                </p>
                <p className="mt-2 text-xs text-gray-400">
                  From: {user?.name} ({user?.role})
                </p>
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Sending...
                </>
              ) : (
                <>
                  <FiSend className="mr-2" />
                  Send Notification
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SendNotificationModal;