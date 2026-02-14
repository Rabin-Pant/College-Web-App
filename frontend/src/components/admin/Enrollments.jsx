import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  FiUsers, FiCheckCircle, FiXCircle, FiClock,
  FiFilter, FiSearch, FiUserCheck, FiUserX,
  FiDownload, FiRefreshCw
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminEnrollments = () => {
  const [loading, setLoading] = useState(true);
  const [enrollments, setEnrollments] = useState([]);
  const [filteredEnrollments, setFilteredEnrollments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  useEffect(() => {
    fetchEnrollments();
  }, []);

  useEffect(() => {
    filterEnrollments();
  }, [enrollments, statusFilter, searchTerm]);

  const fetchEnrollments = async () => {
    try {
      setLoading(true);
      // ✅ FIXED: Added trailing slash
      const response = await api.get('/admin/enrollments/');
      setEnrollments(response.data.enrollments || []);
      setFilteredEnrollments(response.data.enrollments || []);
      
      // Calculate stats
      const stats = {
        total: response.data.enrollments.length,
        pending: response.data.enrollments.filter(e => e.status === 'pending').length,
        approved: response.data.enrollments.filter(e => e.status === 'approved').length,
        rejected: response.data.enrollments.filter(e => e.status === 'rejected').length
      };
      setStats(stats);
    } catch (error) {
      console.error('Failed to fetch enrollments:', error);
      toast.error('Failed to load enrollments');
    } finally {
      setLoading(false);
    }
  };

  const filterEnrollments = () => {
    let filtered = [...enrollments];

    if (statusFilter !== 'all') {
      filtered = filtered.filter(e => e.status === statusFilter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(e => 
        e.student_name?.toLowerCase().includes(term) ||
        e.student_email?.toLowerCase().includes(term) ||
        e.subject_name?.toLowerCase().includes(term) ||
        e.course_name?.toLowerCase().includes(term) ||
        e.section_name?.toLowerCase().includes(term)
      );
    }

    setFilteredEnrollments(filtered);
  };

  const approveEnrollment = async (enrollmentId) => {
    try {
      // ✅ FIXED: Added trailing slash
      await api.post(`/admin/enrollments/${enrollmentId}/approve/`);
      toast.success('Enrollment approved');
      fetchEnrollments();
    } catch (error) {
      console.error('Failed to approve enrollment:', error);
      toast.error(error.response?.data?.error || 'Failed to approve enrollment');
    }
  };

  const rejectEnrollment = async (enrollmentId) => {
    try {
      // ✅ FIXED: Added trailing slash
      await api.post(`/admin/enrollments/${enrollmentId}/reject/`);
      toast.success('Enrollment rejected');
      fetchEnrollments();
    } catch (error) {
      console.error('Failed to reject enrollment:', error);
      toast.error(error.response?.data?.error || 'Failed to reject enrollment');
    }
  };

  const bulkApprove = async () => {
    const pendingIds = filteredEnrollments
      .filter(e => e.status === 'pending')
      .map(e => e.enrollment_id);

    if (pendingIds.length === 0) {
      toast.error('No pending enrollments to approve');
      return;
    }

    if (!window.confirm(`Approve ${pendingIds.length} pending enrollments?`)) return;

    try {
      // ✅ FIXED: Added trailing slash
      await api.post('/admin/enrollments/bulk-approve/', { enrollment_ids: pendingIds });
      toast.success(`${pendingIds.length} enrollments approved`);
      fetchEnrollments();
    } catch (error) {
      console.error('Failed to bulk approve:', error);
      toast.error(error.response?.data?.error || 'Failed to bulk approve');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':
        return <span className="bg-yellow-100 text-yellow-800 px-2 py-1 text-xs rounded-full flex items-center">
          <FiClock className="mr-1" /> Pending
        </span>;
      case 'approved':
        return <span className="bg-green-100 text-green-800 px-2 py-1 text-xs rounded-full flex items-center">
          <FiCheckCircle className="mr-1" /> Approved
        </span>;
      case 'rejected':
        return <span className="bg-red-100 text-red-800 px-2 py-1 text-xs rounded-full flex items-center">
          <FiXCircle className="mr-1" /> Rejected
        </span>;
      default:
        return <span className="bg-gray-100 text-gray-800 px-2 py-1 text-xs rounded-full">{status}</span>;
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <FiUsers className="mr-2 text-primary-600" />
            Enrollment Management
          </h1>
          <button
            onClick={fetchEnrollments}
            className="mt-4 md:mt-0 flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <FiRefreshCw className="mr-2" />
            Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600">Total Enrollments</p>
            <p className="text-2xl font-bold text-blue-700">{stats.total}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <p className="text-sm text-yellow-600">Pending</p>
            <p className="text-2xl font-bold text-yellow-700">{stats.pending}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600">Approved</p>
            <p className="text-2xl font-bold text-green-700">{stats.approved}</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <p className="text-sm text-red-600">Rejected</p>
            <p className="text-2xl font-bold text-red-700">{stats.rejected}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1 relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by student, course, subject..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field w-full"
            />
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FiFilter className="text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-field w-40"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            {stats.pending > 0 && (
              <button
                onClick={bulkApprove}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
              >
                <FiCheckCircle className="mr-2" />
                Approve All Pending
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Enrollments Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Section</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teacher</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEnrollments.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center">
                    <FiUsers className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-gray-500">No enrollments found</p>
                  </td>
                </tr>
              ) : (
                filteredEnrollments.map((enrollment) => (
                  <tr key={enrollment.enrollment_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                          {enrollment.profile_pic ? (
                            <img src={enrollment.profile_pic} alt="" className="h-8 w-8 rounded-full" />
                          ) : (
                            <FiUsers className="h-4 w-4 text-gray-500" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{enrollment.student_name}</p>
                          <p className="text-xs text-gray-500">{enrollment.student_email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {enrollment.course_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {enrollment.subject_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Section {enrollment.section_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {enrollment.teacher_name || 'TBA'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(enrollment.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(enrollment.enrollment_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {enrollment.status === 'pending' && (
                        <>
                          <button
                            onClick={() => approveEnrollment(enrollment.enrollment_id)}
                            className="text-green-600 hover:text-green-900 mr-3"
                            title="Approve"
                          >
                            <FiCheckCircle className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => rejectEnrollment(enrollment.enrollment_id)}
                            className="text-red-600 hover:text-red-900"
                            title="Reject"
                          >
                            <FiXCircle className="h-5 w-5" />
                          </button>
                        </>
                      )}
                      {enrollment.status === 'approved' && (
                        <span className="text-green-600 text-sm">Enrolled</span>
                      )}
                      {enrollment.status === 'rejected' && (
                        <span className="text-red-600 text-sm">Rejected</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminEnrollments;