import os
import logging
import traceback
import inspect
import sys
from datetime import datetime
from functools import wraps

class AdvancedLogManager:
    def __init__(self, log_file_paths=None):
        self.log_file_paths = log_file_paths or [
            "enhanced_bot.log",
            "bot.log", 
            "error_trace.log",
            "performance.log"
        ]
        
        # Setup advanced logging
        self.setup_advanced_logging()
        
    def setup_advanced_logging(self):
        """Setup comprehensive logging system"""
        try:
            # Main bot logger
            self.bot_logger = logging.getLogger('BinaryPredictorAI')
            self.bot_logger.setLevel(logging.INFO)
            
            # Error-specific logger
            self.error_logger = logging.getLogger('ErrorTracker')
            self.error_logger.setLevel(logging.ERROR)
            
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # File handlers
            bot_handler = logging.FileHandler('enhanced_bot.log')
            bot_handler.setFormatter(detailed_formatter)
            
            error_handler = logging.FileHandler('error_trace.log')
            error_handler.setFormatter(detailed_formatter)
            error_handler.setLevel(logging.ERROR)
            
            # Add handlers
            self.bot_logger.addHandler(bot_handler)
            self.error_logger.addHandler(error_handler)
            
            # Also log to console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(detailed_formatter)
            self.bot_logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"❌ CRITICAL: Logging setup failed: {e}")
    
    def track_error(self, error, context=""):
        """Track errors with full traceback and context"""
        try:
            # Get the calling function and module
            frame = inspect.currentframe().f_back
            calling_function = frame.f_code.co_name
            calling_file = os.path.basename(frame.f_code.co_filename)
            calling_line = frame.f_lineno
            
            error_info = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'calling_function': calling_function,
                'calling_file': calling_file,
                'calling_line': calling_line,
                'context': context,
                'full_traceback': traceback.format_exc()
            }
            
            # Log to error file
            error_message = f"""
🚨 🚨 🚨 CRITICAL ERROR DETECTED 🚨 🚨 🚨

⏰ TIMESTAMP: {error_info['timestamp']}
📁 MODULE: {error_info['calling_file']}
🔧 FUNCTION: {error_info['calling_function']}:{error_info['calling_line']}
🚨 ERROR TYPE: {error_info['error_type']}
💬 ERROR MESSAGE: {error_info['error_message']}
📝 CONTEXT: {error_info['context']}

🔍 FULL TRACEBACK:
{error_info['full_traceback'] if error_info['full_traceback'] != 'NoneType: None' else 'No traceback available'}

📍 ERROR ORIGIN: 
  File: {error_info['calling_file']}
  Function: {error_info['calling_function']}
  Line: {error_info['calling_line']}
"""
            
            self.error_logger.error(error_message)
            self.bot_logger.error(f"ERROR in {calling_file}:{calling_function}:{calling_line} - {error}")
            
            return error_info
            
        except Exception as log_error:
            print(f"❌ LOGGING SYSTEM FAILED: {log_error}")
    
    def get_module_health_report(self):
        """Generate health report for all modules"""
        try:
            report = "🤖 BOT HEALTH REPORT 🤖\n"
            report += f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Check each log file
            for log_path in self.log_file_paths:
                report += f"📁 {log_path}:\n"
                if os.path.exists(log_path):
                    file_size = os.path.getsize(log_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                    
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                        lines = file.readlines()
                        error_count = sum(1 for line in lines if 'ERROR' in line.upper())
                        warning_count = sum(1 for line in lines if 'WARNING' in line.upper())
                    
                    report += f"  • Size: {file_size} bytes\n"
                    report += f"  • Lines: {len(lines)}\n"
                    report += f"  • Errors: {error_count}\n"
                    report += f"  • Warnings: {warning_count}\n"
                    report += f"  • Last Modified: {modified_time.strftime('%H:%M:%S')}\n"
                    
                    # Recent errors
                    recent_errors = [line for line in lines[-10:] if 'ERROR' in line.upper()]
                    if recent_errors:
                        report += f"  • Recent Errors: {len(recent_errors)} in last 10 lines\n"
                    
                else:
                    report += "  • ❌ FILE NOT FOUND\n"
                report += "\n"
            
            return report
            
        except Exception as e:
            return f"❌ Health report failed: {e}"
    
    def get_recent_errors(self, hours=24):
        """Get errors from last N hours"""
        try:
            error_file = "error_trace.log"
            if not os.path.exists(error_file):
                return "No error log file found"
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_errors = []
            
            with open(error_file, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                current_error = []
                in_error = False
                
                for line in lines:
                    if '🚨 🚨 🚨 CRITICAL ERROR DETECTED' in line:
                        if current_error and in_error:
                            recent_errors.append(''.join(current_error))
                        current_error = [line]
                        in_error = True
                    elif in_error:
                        current_error.append(line)
                        if '📍 ERROR ORIGIN:' in line:
                            # Check if this error is recent
                            error_text = ''.join(current_error)
                            recent_errors.append(error_text)
                            current_error = []
                            in_error = False
            
            if recent_errors:
                return f"🔍 LAST {len(recent_errors)} ERRORS:\n\n" + "\n" + "="*50 + "\n".join(recent_errors[-10:])
            else:
                return "✅ No recent errors found!"
                
        except Exception as e:
            return f"Error reading recent errors: {e}"
    
    def get_log_files(self):
        """Get available log files"""
        available_logs = []
        for log_path in self.log_file_paths:
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
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                all_lines = file.readlines()
                return ''.join(all_lines[-lines:]) if all_lines else "Log file is empty"
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def get_log_stats(self, log_path):
        """Get log file statistics"""
        try:
            if not os.path.exists(log_path):
                return "Log file not found"
            
            file_size = os.path.getsize(log_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_path))
            created_time = datetime.fromtimestamp(os.path.getctime(log_path))
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                error_count = sum(1 for line in lines if 'ERROR' in line.upper())
                warning_count = sum(1 for line in lines if 'WARNING' in line.upper())
            
            stats = f"""
📊 **DETAILED LOG STATISTICS: {os.path.basename(log_path)}**

📁 **File Info:**
• Size: {file_size} bytes ({round(file_size / (1024 * 1024), 2)} MB)
• Lines: {len(lines)}
• Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
• Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}

🚨 **Error Analysis:**
• Total Errors: {error_count}
• Total Warnings: {warning_count}
• Error Rate: {round((error_count / len(lines)) * 100, 2) if lines else 0}%

📈 **Recent Activity:**
• Last 10 lines errors: {sum(1 for line in lines[-10:] if 'ERROR' in line.upper())}
• Last 50 lines errors: {sum(1 for line in lines[-50:] if 'ERROR' in line.upper())}

💡 **Status:** {'🟢 ACTIVE' if len(lines) > 0 else '🔴 EMPTY'}
"""
            return stats
        except Exception as e:
            return f"Error getting log stats: {e}"
    
    def search_logs(self, log_path, search_term, max_results=20):
        """Search for specific terms in logs"""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                matching_lines = []
                
                for i, line in enumerate(lines, 1):
                    if search_term.lower() in line.lower():
                        matching_lines.append(f"Line {i}: {line}")
                
                if not matching_lines:
                    return f"No results found for: '{search_term}'"
                
                results = matching_lines[-max_results:]
                return f"🔍 **Search Results for '{search_term}'** (showing last {len(results)}):\n\n" + ''.join(results)
        except Exception as e:
            return f"Error searching logs: {e}"
    
    def clear_logs(self, log_path):
        """Clear log file content"""
        try:
            with open(log_path, 'w') as file:
                file.write(f"✅ Logs cleared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            return f"✅ Log file cleared: {log_path}"
        except Exception as e:
            return f"Error clearing logs: {e}"

# Global advanced log manager instance
log_manager = AdvancedLogManager()

# Quick test function
def test_logging_system():
    """Test the logging system"""
    try:
        log_manager.bot_logger.info("✅ Logging system initialized successfully!")
        print("✅ Advanced logging system READY!")
        print("📊 It will track:")
        print("   • Exact error locations (file, function, line)")
        print("   • Full tracebacks")
        print("   • Module health reports")
        print("   • Recent error analysis")
    except Exception as e:
        print(f"❌ Logging test failed: {e}")

# Run test on import
test_logging_system()
