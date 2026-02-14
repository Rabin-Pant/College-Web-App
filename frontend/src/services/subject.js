import api from './api';

const subjectService = {
  // Get all subjects
  getAllSubjects: async () => {
    try {
      const response = await api.get('/subjects/');
      return response.data.subjects;
    } catch (error) {
      console.error('Error fetching subjects:', error);
      throw error;
    }
  },

  // Get subjects for dropdown
  getSubjectsForSelection: async () => {
    try {
      const response = await api.get('/subjects/for-selection');
      return response.data.subjects;
    } catch (error) {
      console.error('Error fetching subjects:', error);
      return [];
    }
  },

  // Get subjects by course
  getSubjectsByCourse: async (courseId) => {
    try {
      const response = await api.get(`/subjects/course/${courseId}`);
      return response.data.subjects;
    } catch (error) {
      console.error('Error fetching subjects:', error);
      throw error;
    }
  },

  // Get subject by ID
  getSubjectById: async (subjectId) => {
    try {
      const response = await api.get(`/subjects/${subjectId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching subject:', error);
      throw error;
    }
  }
};

export default subjectService;