from utils.database import mysql

class Settings:
    """Settings Model - Handles system configuration"""
    
    @staticmethod
    def get_all():
        """Get all settings"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM settings ORDER BY `key`")
        settings = cursor.fetchall()
        cursor.close()
        
        # Convert to dictionary
        settings_dict = {}
        for setting in settings:
            settings_dict[setting['key']] = setting['value']
        return settings_dict
    
    @staticmethod
    def get(key, default=None):
        """Get a specific setting by key"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
        result = cursor.fetchone()
        cursor.close()
        return result['value'] if result else default
    
    @staticmethod
    def set(key, value):
        """Set a specific setting"""
        cursor = mysql.connection.cursor()
        try:
            # Check if setting exists
            cursor.execute("SELECT id FROM settings WHERE `key` = %s", (key,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute("UPDATE settings SET value = %s, updated_at = NOW() WHERE `key` = %s", (value, key))
            else:
                cursor.execute("INSERT INTO settings (`key`, value) VALUES (%s, %s)", (key, value))
            
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def set_many(settings_dict):
        """Set multiple settings at once"""
        cursor = mysql.connection.cursor()
        try:
            for key, value in settings_dict.items():
                cursor.execute("SELECT id FROM settings WHERE `key` = %s", (key,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("UPDATE settings SET value = %s, updated_at = NOW() WHERE `key` = %s", (value, key))
                else:
                    cursor.execute("INSERT INTO settings (`key`, value) VALUES (%s, %s)", (key, value))
            
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e