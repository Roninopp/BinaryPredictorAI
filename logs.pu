import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

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
                # Read all lines and get last N
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
                
                # Adjust line numbers (1-indexed to 0-indexed)
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
            
            # Count lines and errors
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
                
                results = matching_lines[-max_results:]  # Get latest matches
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

# Telegram command handlers
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available log files and their status"""
    try:
        available_logs = log_manager.get_log_files()
        
        if not available_logs:
            await update.message.reply_text("📭 No log files found!")
            return
        
        message = "📁 **AVAILABLE LOG FILES:**\n\n"
        for log in available_logs:
            message += f"• **{log['path']}**\n"
            message += f"  Size: {log['size_mb']}MB | Modified: {log['modified'].strftime('%H:%M:%S')}\n\n"
        
        message += "💡 **Usage:**\n"
        message += "`/logs tail FILE` - Show last 50 lines\n"
        message += "`/logs stats FILE` - Show file statistics\n"
        message += "`/logs search FILE TERM` - Search in logs\n"
        message += "`/logs clear FILE` - Clear log file\n\n"
        message += "**Example:** `/logs tail enhanced_bot.log`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error showing logs: {e}")

async def handle_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all logs subcommands"""
    try:
        if not context.args:
            await show_logs(update, context)
            return
        
        command = context.args[0].lower()
        
        if command == "tail":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs tail FILENAME`\nExample: `/logs tail enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            lines = int(context.args[2]) if len(context.args) > 2 else 50
            
            if not os.path.exists(log_file):
                await update.message.reply_text(f"❌ Log file not found: {log_file}")
                return
            
            log_content = log_manager.read_log_tail(log_file, lines)
            
            # Split if too long for Telegram
            if len(log_content) > 4000:
                log_content = log_content[-4000:] + "\n\n... (truncated, use fewer lines)"
            
            await update.message.reply_text(f"📄 **Last {lines} lines of {log_file}:**\n\n```\n{log_content}\n```", parse_mode='Markdown')
        
        elif command == "stats":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs stats FILENAME`\nExample: `/logs stats enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            stats = log_manager.get_log_stats(log_file)
            await update.message.reply_text(stats, parse_mode='Markdown')
        
        elif command == "search":
            if len(context.args) < 3:
                await update.message.reply_text("❌ Usage: `/logs search FILENAME TERM`\nExample: `/logs search enhanced_bot.log ERROR`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            search_term = " ".join(context.args[2:])
            
            if not os.path.exists(log_file):
                await update.message.reply_text(f"❌ Log file not found: {log_file}")
                return
            
            results = log_manager.search_logs(log_file, search_term)
            
            # Split if too long
            if len(results) > 4000:
                results = results[-4000:] + "\n\n... (truncated)"
            
            await update.message.reply_text(f"```\n{results}\n```", parse_mode='Markdown')
        
        elif command == "clear":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs clear FILENAME`\nExample: `/logs clear enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            result = log_manager.clear_logs(log_file)
            await update.message.reply_text(result)
        
        else:
            await update.message.reply_text("❌ Unknown logs command. Use: tail, stats, search, or clear")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Logs command error: {e}")

# Function to add log handlers to main bot
def setup_log_handlers(application):
    """Add log command handlers to the bot"""
    application.add_handler(CommandHandler("logs", handle_logs_command))
    application.add_handler(CommandHandler("log", handle_logs_command))
    application.add_handler(CommandHandler("tail", handle_logs_command))
