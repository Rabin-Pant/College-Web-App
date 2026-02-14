import api from './api';

const courseService = {
  // Get all courses
  getAllCourses: async () => {
    try {
      const response = await api.get('/courses/');
      return response.data.courses;
    } catch (error) {
      console.error('Error fetching courses:', error);
      throw error;
    }
  },

  // Get course by ID
  getCourseById: async (courseId) => {
    try {
      const response = await api.get(`/courses/${courseId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching course:', error);
      throw error;
    }
  },

  // Get courses for selection dropdown
  getCourseOptions: async () => {
    try {
      const courses = await courseService.getAllCourses();
      return courses.map(course => ({
        value: course.id,
        label: `${course.code} - ${course.name}`
      }));
    } catch (error) {
      console.error('Error fetching course options:', error);
      return [];
    }
  }
};

export default courseService;