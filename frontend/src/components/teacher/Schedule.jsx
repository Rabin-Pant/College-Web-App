import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  FiCalendar, FiClock, FiMapPin, FiBook,
  FiUser, FiChevronLeft, FiChevronRight
} from 'react-icons/fi';
import Loader from '../common/Loader';
import toast from 'react-hot-toast';

const TeacherSchedule = () => {
  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState({});
  const [currentWeek, setCurrentWeek] = useState(new Date());

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const timeSlots = [
    '08:00', '09:00', '10:00', '11:00', '12:00', 
    '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'
  ];

  useEffect(() => {
    fetchSchedule();
  }, []);

  const fetchSchedule = async () => {
    try {
      const response = await api.get('/teacher/schedule');
      
      // Group schedule by day
      const grouped = {};
      daysOfWeek.forEach(day => {
        grouped[day] = response.data.schedule[day] || [];
      });
      
      setSchedule(grouped);
    } catch (error) {
      console.error('Failed to fetch schedule:', error);
      toast.error('Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  const getWeekDates = () => {
    const start = new Date(currentWeek);
    const day = start.getDay();
    const diff = start.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(start.setDate(diff));
    
    const dates = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  const changeWeek = (direction) => {
    const newDate = new Date(currentWeek);
    newDate.setDate(currentWeek.getDate() + (direction * 7));
    setCurrentWeek(newDate);
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const weekDates = getWeekDates();

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">My Schedule</h1>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => changeWeek(-1)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <FiChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm font-medium">
              {formatDate(weekDates[0])} - {formatDate(weekDates[6])}
            </span>
            <button
              onClick={() => changeWeek(1)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <FiChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Schedule Grid */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <div className="min-w-[800px]">
            {/* Days Header */}
            <div className="grid grid-cols-8 border-b border-gray-200">
              <div className="p-4 bg-gray-50 font-medium text-gray-700">Time</div>
              {daysOfWeek.map((day, index) => (
                <div key={day} className="p-4 bg-gray-50 font-medium text-gray-700 text-center">
                  <div>{day}</div>
                  <div className="text-xs text-gray-500 mt-1">{formatDate(weekDates[index])}</div>
                </div>
              ))}
            </div>

            {/* Time Slots */}
            {timeSlots.map((time, slotIndex) => (
              <div key={time} className="grid grid-cols-8 border-b border-gray-100">
                <div className="p-4 text-sm text-gray-600 bg-gray-50">{time}</div>
                {daysOfWeek.map((day) => {
                  const classAtThisTime = schedule[day]?.find(c => 
                    c.start_time <= time && c.end_time > time
                  );
                  
                  return (
                    <div key={`${day}-${time}`} className="p-2 border-l border-gray-100 min-h-[80px]">
                      {classAtThisTime && (
                        <div className="bg-blue-50 p-2 rounded-lg h-full">
                          <p className="text-xs font-medium text-blue-900">
                            {classAtThisTime.subject_code}
                          </p>
                          <p className="text-xs text-blue-700 mt-1">
                            {classAtThisTime.course_code} - {classAtThisTime.section_name}
                          </p>
                          <p className="text-xs text-blue-600 mt-1 flex items-center">
                            <FiMapPin className="mr-1 h-3 w-3" />
                            {classAtThisTime.room || 'TBA'}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}

            {/* No Schedule Message */}
            {Object.values(schedule).every(day => day.length === 0) && (
              <div className="p-12 text-center">
                <FiCalendar className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-4 text-lg font-medium text-gray-900">No schedule found</h3>
                <p className="mt-2 text-gray-500">Your class schedule will appear here once assigned.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Upcoming Classes Summary */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Upcoming Classes</h2>
        <div className="space-y-3">
          {Object.entries(schedule).map(([day, classes]) => 
            classes.map((cls, idx) => (
              <div key={`${day}-${idx}`} className="flex items-center p-3 bg-gray-50 rounded-lg">
                <div className="w-24 font-medium text-gray-700">{day}</div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{cls.subject_name}</p>
                  <p className="text-sm text-gray-600">
                    {cls.course_name} • Section {cls.section_name}
                  </p>
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <FiClock className="mr-1" />
                  {cls.start_time} - {cls.end_time}
                </div>
              </div>
            ))
          )}
          {Object.values(schedule).every(day => day.length === 0) && (
            <p className="text-gray-500 text-center py-4">No upcoming classes</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherSchedule;