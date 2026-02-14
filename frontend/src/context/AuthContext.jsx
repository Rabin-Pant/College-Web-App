import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/profile');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      
      const { access_token, refresh_token, user } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setToken(access_token);
      setUser(user);
      
      toast.success('Login successful!');
      return { success: true, role: user.role };
    } catch (error) {
      console.error('Login error:', error.response?.data || error);
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        if (error.response?.data?.needs_verification) {
          toast.error('Please verify your email before logging in.');
          return { 
            success: false, 
            error: 'Email not verified',
            needsVerification: true 
          };
        }
        toast.error('Invalid email or password');
        return { success: false, error: 'Invalid credentials' };
      }
      
      const message = error.response?.data?.error || 'Login failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const register = async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      
      toast.success(response.data.message || 'Registration successful! You can now login.');
      
      // If email is auto-verified (development), show success message
      if (response.data.email_verified) {
        toast.success('Email auto-verified! You can login now.');
      }
      
      return { 
        success: true, 
        message: response.data.message,
        emailVerified: response.data.email_verified 
      };
    } catch (error) {
      console.error('Registration error:', error.response?.data || error);
      
      // Handle validation errors
      if (error.response?.status === 400) {
        const errorMsg = error.response?.data?.error || 'Invalid registration data';
        toast.error(errorMsg);
        return { success: false, error: errorMsg };
      }
      
      const message = error.response?.data?.error || 'Registration failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete api.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    toast.success('Logged out successfully');
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user,
    isTeacher: user?.role === 'teacher',
    isStudent: user?.role === 'student',
    isAdmin: user?.role === 'admin',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};