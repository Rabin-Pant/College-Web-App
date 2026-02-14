import api from './services/api';

const testConnection = async () => {
  try {
    console.log('🔍 Testing backend connection...');
    console.log('📡 API URL:', process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api');
    
    const response = await api.get('/health');
    console.log('✅ Backend connection successful!');
    console.log('📊 Server status:', response.data);
    return true;
  } catch (error) {
    console.error('❌ Backend connection failed!');
    console.error('🔴 Error:', error.message);
    console.error('💡 Make sure Flask backend is running on port 5000');
    return false;
  }
};

export default testConnection;