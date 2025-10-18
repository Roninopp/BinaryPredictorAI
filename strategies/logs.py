import os
import logging
import asyncio
from datetime import datetime
# REMOVE these lines - they cause circular imports:
# from telegram import Update
# from telegram.ext import ContextTypes, CommandHandler

class LogManager:
    def __init__(self, log_file_paths=None):
        self.log_file_paths = log_file_paths or [
            "enhanced_bot.log",
            "bot.log", 
            "bot_logs.txt"
        ]
        
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
    
    def read_log_range(self, log_path, start_line=1, end_line=100):
        """Read specific line range from log file"""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
                all_lines = file.readlines()
                if not all_lines:
                    return "Log file is empty"
                
                start = max(0, start_line - 1)
                end = min(len(all_lines), end_line)
                
                selected_lines = all_lines[start:end]
                return f"Lines {start_line}-{end_line}:\n" + ''.join(selected_lines)
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
📊 **LOG STATISTICS: {os.path.basename(log_path)}**

📁 **File Info:**
• Size: {file_size} bytes ({round(file_size / (1024 * 1024), 2)} MB)
• Lines: {len(lines)}
• Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
• Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}

🚨 **Error Analysis:**
• Errors: {error_count}
• Warnings: {warning_count}
• Error Rate: {round((error_count / len(lines)) * 100, 2) if lines else 0}%

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
                matching_lines = [line for line in lines if search_term.lower() in line.lower()]
                
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
                file.write("")
            return f"✅ Log file cleared: {log_path}"
        except Exception as e:
            return f"Error clearing logs: {e}"

# Global log manager instance
log_manager = LogManager()

# Telegram command handlers - MOVE THESE TO MAIN BOT FILE
# Remove all the async functions and setup_log_handlers from here
