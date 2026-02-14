import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

// ============ COMMON COMPONENTS ============
import Navbar from './components/common/Navbar';
import PrivateRoute from './components/auth/PrivateRoute';
import RoleRoute from './components/auth/RoleRoute';

// ============ AUTH PAGES ============
import Login from './pages/Login';
import Register from './pages/Register';

// ============ STUDENT COMPONENTS ============
import StudentDashboard from './components/student/Dashboard';
import AvailableSections from './components/student/AvailableSections';
import StudentSectionView from './components/student/SectionView';
import AssignmentView from './components/student/AssignmentView';
import StudentProfile from './components/student/Profile';
import StudentSections from './components/student/Sections';

// ============ TEACHER COMPONENTS ============
import TeacherDashboard from './components/teacher/Dashboard';
import TeacherSectionView from './components/teacher/SectionView';
import TeacherSections from './components/teacher/Sections';
import TeacherSchedule from './components/teacher/Schedule';
import TeacherAttendance from './components/teacher/TeacherAttendance';
import CreateAssignment from './components/teacher/CreateAssignment';
import GradeSubmissions from './components/teacher/GradeSubmissions';
import UploadMaterial from './components/teacher/UploadMaterial';
import TeacherProfile from './components/teacher/Profile';
import CreateZoomModal from './components/teacher/CreateZoomModal';
import TakeAttendanceModal from './components/teacher/TakeAttendanceModal';

// ============ ADMIN COMPONENTS ============
import AdminDashboard from './components/admin/Dashboard';
import AdminUsers from './components/admin/Users';
import AdminReports from './components/admin/Reports';
import AdminSettings from './components/admin/Settings';
import AdminCourses from './components/admin/Courses';
import AdminSubjects from './components/admin/Subjects';
import AdminSections from './components/admin/Sections';
import AdminEnrollments from './components/admin/Enrollments';
import AdminTeacherAssignments from './components/admin/TeacherAssignments';
import AdminProfile from './components/admin/Profile';

// ============ PROFILE COMPONENTS ============
import EditProfile from './components/common/EditProfile';
import ChangePassword from './components/common/ChangePassword';
import Notifications from './pages/Notifications';

// ============ TEST CONNECTION (REMOVE IN PRODUCTION) ============
import testConnection from './testConnection';

function AppContent() {
  const { user, isAuthenticated } = useAuth();

  // Test backend connection on app start (remove in production)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      testConnection();
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Routes>
          {/* ============ PUBLIC ROUTES ============ */}
          <Route path="/login" element={
            !isAuthenticated ? <Login /> : <Navigate to="/dashboard" />
          } />
          <Route path="/register" element={
            !isAuthenticated ? <Register /> : <Navigate to="/dashboard" />
          } />
          
          {/* ============ ROOT REDIRECT ============ */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          
          {/* ============ DASHBOARD ROUTER ============ */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <DashboardRouter />
            </PrivateRoute>
          } />
          
          {/* ============ NOTIFICATIONS ============ */}
          <Route path="/notifications" element={
            <PrivateRoute>
              <Notifications />
            </PrivateRoute>
          } />
          
          {/* ============ PROFILE ROUTES ============ */}
          <Route path="/profile" element={
            <PrivateRoute>
              <ProfileRouter />
            </PrivateRoute>
          } />
          <Route path="/profile/edit" element={
            <PrivateRoute>
              <EditProfile />
            </PrivateRoute>
          } />
          <Route path="/profile/change-password" element={
            <PrivateRoute>
              <ChangePassword />
            </PrivateRoute>
          } />
          
          {/* ============ TEACHER ROUTES ============ */}
          {/* SPECIFIC ROUTES FIRST - ORDER MATTERS! */}
          <Route path="/teacher/sections" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherSections />
            </RoleRoute>
          } />
          
          <Route path="/teacher/schedule" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherSchedule />
            </RoleRoute>
          } />
          
          <Route path="/teacher/profile" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherProfile />
            </RoleRoute>
          } />
          
          {/* ✅ ATTENDANCE PAGE ROUTE - FIXES 404 ERROR */}
          <Route path="/teacher/section/:sectionId/attendance" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherAttendance />
            </RoleRoute>
          } />
          
          {/* PARAMETERIZED ROUTES - AFTER SPECIFIC ONES */}
          <Route path="/teacher/section/:sectionId/create-assignment" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <CreateAssignment />
            </RoleRoute>
          } />
          
          <Route path="/teacher/section/:sectionId/upload-material" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <UploadMaterial />
            </RoleRoute>
          } />
          
          <Route path="/teacher/section/:sectionId/schedule-zoom" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <CreateZoomModal />
            </RoleRoute>
          } />
          
          <Route path="/teacher/section/:sectionId/take-attendance" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TakeAttendanceModal />
            </RoleRoute>
          } />
          
          <Route path="/teacher/section/:sectionId" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherSectionView />
            </RoleRoute>
          } />
          
          <Route path="/teacher/assignment/:assignmentId/grade" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <GradeSubmissions />
            </RoleRoute>
          } />
          
          {/* GENERIC DASHBOARD LAST */}
          <Route path="/teacher/dashboard" element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherDashboard />
            </RoleRoute>
          } />
          
          {/* ============ STUDENT ROUTES ============ */}
          <Route path="/student/sections" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <StudentSections />
            </RoleRoute>
          } />
          
          <Route path="/student/available-sections" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <AvailableSections />
            </RoleRoute>
          } />
          
          <Route path="/student/profile" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <StudentProfile />
            </RoleRoute>
          } />
          
          <Route path="/student/section/:sectionId" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <StudentSectionView />
            </RoleRoute>
          } />
          
          <Route path="/student/assignment/:assignmentId" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <AssignmentView />
            </RoleRoute>
          } />
          
          <Route path="/student/dashboard" element={
            <RoleRoute allowedRoles={['student', 'admin']}>
              <StudentDashboard />
            </RoleRoute>
          } />
          
          {/* ============ ADMIN ROUTES ============ */}
          <Route path="/admin/profile" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminProfile />
            </RoleRoute>
          } />
          
          <Route path="/admin/courses" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminCourses />
            </RoleRoute>
          } />
          
          <Route path="/admin/subjects" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminSubjects />
            </RoleRoute>
          } />
          
          <Route path="/admin/sections" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminSections />
            </RoleRoute>
          } />
          
          <Route path="/admin/enrollments" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminEnrollments />
            </RoleRoute>
          } />
          
          <Route path="/admin/teacher-assignments" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminTeacherAssignments />
            </RoleRoute>
          } />
          
          <Route path="/admin/users" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminUsers />
            </RoleRoute>
          } />
          
          <Route path="/admin/reports" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminReports />
            </RoleRoute>
          } />
          
          <Route path="/admin/settings" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminSettings />
            </RoleRoute>
          } />
          
          <Route path="/admin/dashboard" element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </RoleRoute>
          } />
          
          {/* ============ 404 NOT FOUND ============ */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
      
      {/* ============ TOAST NOTIFICATIONS ============ */}
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  );
}

// ============ DASHBOARD ROUTER ============
const DashboardRouter = () => {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" />;
  
  switch (user.role) {
    case 'admin':
      return <Navigate to="/admin/dashboard" />;
    case 'teacher':
      return <Navigate to="/teacher/dashboard" />;
    case 'student':
      return <Navigate to="/student/dashboard" />;
    default:
      return <Navigate to="/login" />;
  }
};

// ============ PROFILE ROUTER ============
const ProfileRouter = () => {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" />;
  
  switch (user.role) {
    case 'admin':
      return <Navigate to="/admin/profile" />;
    case 'teacher':
      return <Navigate to="/teacher/profile" />;
    case 'student':
      return <Navigate to="/student/profile" />;
    default:
      return <Navigate to="/login" />;
  }
};

// ============ 404 NOT FOUND COMPONENT ============
const NotFound = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <p className="mt-2 text-gray-500">The page you're looking for doesn't exist.</p>
        <button 
          onClick={() => window.history.back()}
          className="mt-6 btn-primary"
        >
          Go Back
        </button>
      </div>
    </div>
  );
};

// ============ MAIN APP ============
function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;