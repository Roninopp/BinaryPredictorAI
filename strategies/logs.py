import os
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
            if not os.path.exists(log_path):
                return "Log file not found"
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                all_lines = file.readlines()
                return ''.join(all_lines[-lines:]) if all_lines else "Log file is empty"
        except Exception as e:
            return f"Error reading log: {e}"
    
    def get_log_stats(self, log_path):
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            file_size = os.path.getsize(log_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                error_count = sum(1 for line in lines if 'ERROR' in line.upper())
            return f"Size: {file_size} bytes, Lines: {len(lines)}, Errors: {error_count}"
        except Exception as e:
            return f"Error: {e}"
    
    def search_logs(self, log_path, search_term):
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                matches = [line for line in lines if search_term.lower() in line.lower()]
                return ''.join(matches[-20:]) if matches else "No results found"
        except Exception as e:
            return f"Error: {e}"
    
    def clear_logs(self, log_path):
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            with open(log_path, 'w') as file:
                file.write("")
            return "Log file cleared"
        except Exception as e:
            return f"Error: {e}"
    
    def get_module_health_report(self):
        try:
            report = "Bot Health Report:\n"
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    report += f"{log_file}: {size} bytes\n"
                else:
                    report += f"{log_file}: Not found\n"
            return report
        except Exception as e:
            return f"Error: {e}"
    
    def get_recent_errors(self, hours=24):
        try:
            errors = []
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
                        for line in file:
                            if 'ERROR' in line.upper():
                                errors.append(line.strip())
            return '\n'.join(errors[-20:]) if errors else "No errors found"
        except Exception as e:
            return f"Error: {e}"

log_manager = LogManager()
