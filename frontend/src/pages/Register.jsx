import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  FiMail, FiLock, FiUser, FiBook, FiUserPlus, 
  FiAlertCircle, FiCheckCircle, FiCalendar,
  FiBriefcase, FiGlobe
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student'
  });

  // Student specific fields
  const [studentData, setStudentData] = useState({
    course_id: '',
    enrollment_year: new Date().getFullYear(),
    major: ''
  });

  // Teacher specific fields
  const [teacherData, setTeacherData] = useState({
    department: '',
    office_hours: '',
    qualifications: ''
  });

  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [registered, setRegistered] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (formData.role === 'student') {
      fetchCourses();
    }
  }, [formData.role]);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/courses/');
      setCourses(response.data.courses || []);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      toast.error('Failed to load courses');
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!formData.email.endsWith('@yourcollege.edu')) {
      newErrors.email = 'Must use @yourcollege.edu email';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one lowercase letter';
    } else if (!/[0-9]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one number';
    } else if (!/[!@#$%^&*]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one special character';
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Student-specific validation
    if (formData.role === 'student') {
      if (!studentData.course_id) {
        newErrors.course_id = 'Please select a course';
      }
      if (!studentData.major.trim()) {
        newErrors.major = 'Major is required';
      }
    }

    // Teacher-specific validation
    if (formData.role === 'teacher') {
      if (!teacherData.department.trim()) {
        newErrors.department = 'Department is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRoleChange = (role) => {
    setFormData({ ...formData, role });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleStudentChange = (e) => {
    const { name, value } = e.target;
    setStudentData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleTeacherChange = (e) => {
    const { name, value } = e.target;
    setTeacherData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    // Prepare data based on role
    const userData = {
      name: formData.name,
      email: formData.email,
      password: formData.password,
      role: formData.role
    };

    // Add role-specific data
    if (formData.role === 'student') {
      userData.course_id = parseInt(studentData.course_id);
      userData.enrollment_year = parseInt(studentData.enrollment_year);
      userData.major = studentData.major;
    } else if (formData.role === 'teacher') {
      userData.department = teacherData.department;
      userData.office_hours = teacherData.office_hours;
      userData.qualifications = teacherData.qualifications;
    }

    const result = await register(userData);
    
    if (result.success) {
      setRegistered(true);
      toast.success('Registration successful!');
      
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    }
    
    setLoading(false);
  };

  if (registered) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <FiCheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Registration Successful!</h2>
          <p className="text-gray-600 mb-6">
            Your account has been created successfully. You can now login with your credentials.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="w-full btn-primary py-3"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-2xl">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Create Your Account</h2>
          <p className="text-gray-600 mt-2">Join CollegeApp today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiUser className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`pl-10 input-field ${errors.name ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="John Doe"
                />
              </div>
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiMail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`pl-10 input-field ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="you@yourcollege.edu"
                />
              </div>
              {errors.email ? (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              ) : (
                <p className="mt-1 text-xs text-gray-500">Must be @yourcollege.edu email</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`pl-10 input-field ${errors.password ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="••••••••"
                />
              </div>
              {errors.password ? (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              ) : (
                <p className="mt-1 text-xs text-gray-500">Min 8 chars, 1 uppercase, 1 number, 1 special</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FiLock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className={`pl-10 input-field ${errors.confirmPassword ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="••••••••"
                />
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Role Selection */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                I am a <span className="text-red-500">*</span>
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="role"
                    value="student"
                    checked={formData.role === 'student'}
                    onChange={() => handleRoleChange('student')}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Student</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="role"
                    value="teacher"
                    checked={formData.role === 'teacher'}
                    onChange={() => handleRoleChange('teacher')}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Teacher</span>
                </label>
              </div>
            </div>
          </div>

          {/* Student Specific Fields */}
          {formData.role === 'student' && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <FiBook className="mr-2" />
                Academic Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Course <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="course_id"
                    value={studentData.course_id}
                    onChange={handleStudentChange}
                    className={`input-field ${errors.course_id ? 'border-red-500 focus:ring-red-500' : ''}`}
                  >
                    <option value="">-- Select a course --</option>
                    {courses.map(course => (
                      <option key={course.id} value={course.id}>
                        {course.code} - {course.name}
                      </option>
                    ))}
                  </select>
                  {errors.course_id && (
                    <p className="mt-1 text-sm text-red-600">{errors.course_id}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enrollment Year
                  </label>
                  <div className="relative">
                    <FiCalendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <select
                      name="enrollment_year"
                      value={studentData.enrollment_year}
                      onChange={handleStudentChange}
                      className="pl-10 input-field"
                    >
                      <option>2024</option>
                      <option>2025</option>
                      <option>2026</option>
                      <option>2027</option>
                    </select>
                  </div>
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Major/Program <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="major"
                    value={studentData.major}
                    onChange={handleStudentChange}
                    className={`input-field ${errors.major ? 'border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="e.g., Computer Science, Artificial Intelligence"
                  />
                  {errors.major && (
                    <p className="mt-1 text-sm text-red-600">{errors.major}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Teacher Specific Fields */}
          {formData.role === 'teacher' && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <FiBriefcase className="mr-2" />
                Professional Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Department <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="department"
                    value={teacherData.department}
                    onChange={handleTeacherChange}
                    className={`input-field ${errors.department ? 'border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="e.g., Computer Science, Mathematics"
                  />
                  {errors.department && (
                    <p className="mt-1 text-sm text-red-600">{errors.department}</p>
                  )}
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Office Hours
                  </label>
                  <input
                    type="text"
                    name="office_hours"
                    value={teacherData.office_hours}
                    onChange={handleTeacherChange}
                    className="input-field"
                    placeholder="e.g., Mon/Wed 2-4 PM"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Qualifications
                  </label>
                  <textarea
                    name="qualifications"
                    value={teacherData.qualifications}
                    onChange={handleTeacherChange}
                    rows={3}
                    className="input-field"
                    placeholder="e.g., PhD in Computer Science, 10 years teaching experience"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Error Summary */}
          {Object.keys(errors).length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <FiAlertCircle className="h-5 w-5 text-red-400 mr-2" />
                <div>
                  <p className="text-sm text-red-800 font-medium">Please fix the following errors:</p>
                  <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                    {Object.values(errors).map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center py-3"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Creating Account...
              </div>
            ) : (
              <>
                <FiUserPlus className="mr-2" />
                Sign Up
              </>
            )}
          </button>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Register;