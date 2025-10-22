import os
from datetime import datetime

class LogManager:
    """
    FIXED Log Manager - No Markdown parsing errors
    Removes all problematic formatting that causes Telegram errors
    """
    
    def __init__(self):
        self.log_files = ["enhanced_bot.log", "bot.log", "trading.log"]
    
    def get_log_files(self):
        """Get available log files with safe formatting"""
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
        """Read last N lines from log file"""
        try:
            if not os.path.exists(log_path):
                return f"Error: Log file {log_path} not found"
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                all_lines = file.readlines()
                
                if not all_lines:
                    return "Log file is empty"
                
                # Get last N lines and clean them
                tail_lines = all_lines[-lines:]
                cleaned_lines = [self._clean_log_line(line) for line in tail_lines]
                
                return ''.join(cleaned_lines)
                
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def _clean_log_line(self, line):
        """Clean log line to prevent Telegram parsing errors"""
        # Remove or escape problematic characters
        line = line.replace('*', '').replace('_', '').replace('`', '')
        line = line.replace('[', '').replace(']', '')
        return line
    
    def get_log_stats(self, log_path):
        """Get log file statistics - SAFE formatting"""
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            
            file_size = os.path.getsize(log_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                error_count = sum(1 for line in lines if 'ERROR' in line.upper())
                warning_count = sum(1 for line in lines if 'WARNING' in line.upper())
                info_count = sum(1 for line in lines if 'INFO' in line.upper())
            
            # SAFE TEXT FORMAT - No markdown that can cause parsing errors
            stats = f"""LOG STATISTICS: {os.path.basename(log_path)}

File Size: {file_size} bytes ({round(file_size/1024, 2)} KB)
Total Lines: {len(lines)}
Errors: {error_count}
Warnings: {warning_count}
Info: {info_count}
Last Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            return stats
            
        except Exception as e:
            return f"Error getting log stats: {str(e)}"
    
    def search_logs(self, log_path, search_term, max_results=20):
        """Search logs for specific term - SAFE formatting"""
        try:
            if not os.path.exists(log_path):
                return f"Log file not found: {log_path}"
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                
            matching_lines = [f"Line {i+1}: {self._clean_log_line(line)}" 
                              for i, line in enumerate(lines) 
                              if search_term.lower() in line.lower()]
            
            if not matching_lines:
                return f"No results found for: {search_term}"
            
            # Return last N matching lines
            result_lines = matching_lines[-max_results:]
            result = f"Found {len(matching_lines)} matches. Showing last {len(result_lines)}:\n\n"
            result += ''.join(result_lines)
            
            return result
            
        except Exception as e:
            return f"Error searching logs: {str(e)}"

    def clear_logs(self, log_path):
        """Clear log file - SAFE operation"""
        try:
            if not os.path.exists(log_path):
                return f"Log file not found: {log_path}"
            
            with open(log_path, 'w') as file:
                file.write("")
            
            return f"SUCCESS: Log file cleared - {log_path}"
            
        except Exception as e:
            return f"Error clearing logs: {str(e)}"

    def get_module_health_report(self):
        """Bot health report - SAFE formatting"""
        try:
            health_info = "BOT HEALTH REPORT\n"
            health_info += "=" * 20 + "\n"
            
            health_info += "LOG FILES:\n"
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    size_kb = round(os.path.getsize(log_file) / 1024, 2)
                    health_info += f"  - OK: {log_file} ({size_kb} KB)\n"
                else:
                    health_info += f"  - MISSING: {log_file}\n"
            
            health_info += f"\nSYSTEM INFO:\n"
            health_info += f"  - Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            health_info += f"  - Status: RUNNING\n"
            
            return health_info
            
        except Exception as e:
            return f"Health report error: {str(e)}"

# Global log manager instance
log_manager = LogManager()
