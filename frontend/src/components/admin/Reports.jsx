import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  FiBarChart2, FiDownload, FiCalendar, 
  FiUsers, FiBook, FiClipboard 
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const AdminReports = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [classReport, setClassReport] = useState([]);
  const [dateRange, setDateRange] = useState('30');

  useEffect(() => {
    fetchReports();
  }, [dateRange]);

  const fetchReports = async () => {
    try {
      const [statsRes, classRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/reports/classes')
      ]);
      
      setStats(statsRes.data);
      setClassReport(classRes.data.classes || []);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = (type) => {
    let data = [];
    let filename = '';

    if (type === 'users') {
      data = Object.entries(stats?.users || {}).map(([role, count]) => ({ role, count }));
      filename = 'user_report.csv';
    } else if (type === 'classes') {
      data = classReport;
      filename = 'class_report.csv';
    }

    // Convert to CSV
    const csv = data.map(row => Object.values(row).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  if (loading) return <Loader />;
  if (!stats) return <div>No data available</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <FiBarChart2 className="mr-2" />
            Analytics & Reports
          </h1>
          
          <div className="mt-4 md:mt-0 flex space-x-2">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="input-field w-40"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="365">Last year</option>
            </select>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Users</p>
                <p className="text-3xl font-bold mt-1">
                  {stats.users?.student + stats.users?.teacher + stats.users?.admin || 0}
                </p>
              </div>
              <FiUsers className="h-8 w-8 text-blue-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Total Classes</p>
                <p className="text-3xl font-bold mt-1">{stats.total_classes || 0}</p>
              </div>
              <FiBook className="h-8 w-8 text-green-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Assignments</p>
                <p className="text-3xl font-bold mt-1">{stats.total_assignments || 0}</p>
              </div>
              <FiClipboard className="h-8 w-8 text-purple-200" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-100 text-sm">Active Users</p>
                <p className="text-3xl font-bold mt-1">{stats.active_users_7d || 0}</p>
              </div>
              <FiCalendar className="h-8 w-8 text-yellow-200" />
            </div>
          </div>
        </div>

        {/* User Distribution */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">User Distribution</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Students</span>
                  <span className="font-medium text-gray-900">{stats.users?.student || 0}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full"
                    style={{ 
                      width: `${((stats.users?.student || 0) / 
                        (stats.users?.student + stats.users?.teacher + stats.users?.admin || 1)) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Teachers</span>
                  <span className="font-medium text-gray-900">{stats.users?.teacher || 0}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ 
                      width: `${((stats.users?.teacher || 0) / 
                        (stats.users?.student + stats.users?.teacher + stats.users?.admin || 1)) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Admins</span>
                  <span className="font-medium text-gray-900">{stats.users?.admin || 0}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ 
                      width: `${((stats.users?.admin || 0) / 
                        (stats.users?.student + stats.users?.teacher + stats.users?.admin || 1)) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Submission Status</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Total Submissions</span>
                  <span className="font-medium text-gray-900">{stats.submissions?.total || 0}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-yellow-600">Pending</span>
                  <span className="font-medium text-gray-900">{stats.submissions?.pending || 0}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-green-600">Graded</span>
                  <span className="font-medium text-gray-900">{stats.submissions?.graded || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Class Report Table */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Class Performance</h2>
            <button
              onClick={() => exportReport('classes')}
              className="flex items-center text-sm text-primary-600 hover:text-primary-700"
            >
              <FiDownload className="mr-1" />
              Export CSV
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Class
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Teacher
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Students
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Assignments
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Materials
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {classReport.map((cls) => (
                  <tr key={cls.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{cls.name}</div>
                      <div className="text-sm text-gray-500">{cls.course_code}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cls.teacher_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {cls.student_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {cls.assignment_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {cls.material_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(cls.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminReports;