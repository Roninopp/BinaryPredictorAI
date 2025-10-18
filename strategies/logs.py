import os
import logging
from datetime import datetime

class LogManager:
    def __init__(self):
        self.log_files = ["enhanced_bot.log", "bot.log"]
    
    def get_log_files(self):
        available_logs = []
        for log_path in self.log_files:
            if os.path.exists(log_path):
                file_size = os.path.getsize(log_path)
                modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                available_logs.append({
                    'path': log_path,
                    'size': file_size,
                    'modified': modified_time,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                })
        return available_logs
    
    def read_log_tail(self, log_path, lines=50):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                all_lines = file.readlines()
                return ''.join(all_lines[-lines:]) if all_lines else "Log file is empty"
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def get_log_stats(self, log_path):
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            
            file_size = os.path.getsize(log_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                error_count = sum(1 for line in lines if 'ERROR' in line.upper())
            
            stats = f"""
📊 **LOG STATISTICS: {os.path.basename(log_path)}**
• Size: {file_size} bytes
• Lines: {len(lines)}
• Errors: {error_count}
• Modified: {modified_time.strftime('%H:%M:%S')}
"""
            return stats
        except Exception as e:
            return f"Error getting log stats: {e}"
    
    def search_logs(self, log_path, search_term):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                matching_lines = [line for line in lines if search_term.lower() in line.lower()]
                
                if not matching_lines:
                    return f"No results found for: '{search_term}'"
                
                return ''.join(matching_lines[-20:])
        except Exception as e:
            return f"Error searching logs: {e}"
    
    def clear_logs(self, log_path):
        try:
            with open(log_path, 'w') as file:
                file.write("")
            return f"✅ Log file cleared: {log_path}"
        except Exception as e:
            return f"Error clearing logs: {e}"

    def get_module_health_report(self):
        """Enhanced health report for the bot"""
        try:
            health_info = "🤖 BOT HEALTH REPORT\n\n"
            
            # Check log files
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    health_info += f"✅ {log_file}: {size} bytes\n"
                else:
                    health_info += f"❌ {log_file}: NOT FOUND\n"
            
            # Add system status
            health_info += f"\n🕒 System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            health_info += f"\n📁 Working Dir: {os.getcwd()}"
            
            return health_info
        except Exception as e:
            return f"Health report error: {e}"

    def get_recent_errors(self, hours=24):
        """Get recent errors from logs"""
        try:
            error_lines = []
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
                        for line in file:
                            if 'ERROR' in line.upper():
                                # Simple time filter (basic implementation)
                                error_lines.append(f"{log_file}: {line.strip()}")
            
            if not error_lines:
                return f"No errors found in last {hours} hours"
            
            return '\n'.join(error_lines[-20:])  # Last 20 errors
        except Exception as e:
            return f"Error fetching recent errors: {e}"

log_manager = LogManager()
