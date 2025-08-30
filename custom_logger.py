# Totally AI generated (claude sonnet 4.0)
import logging
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels while keeping colon uncolored"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        # Get the color for the current log level
        color = self.COLORS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format level name with color, then add uncolored colon, then pad to 8 chars total
        level_with_colon = f"{record.levelname}:"
        colored_level = f"{color}{record.levelname}{self.RESET}:{level_with_colon[len(record.levelname)+1:]:>{8-len(level_with_colon)}}"
        
        # Actually, let's make this simpler and clearer:
        colored_level = f"{color}{record.levelname}{self.RESET}:"
        # Pad the entire thing to 8 characters
        padded_level = f"{colored_level:<8}"  # This won't work correctly with ANSI codes
        
        # Better approach: calculate padding manually
        padding_needed = 8 - len(record.levelname) - 1  # -1 for the colon
        padding = " " * max(0, padding_needed)
        colored_level = f"{color}{record.levelname}{self.RESET}:{padding}"
        
        # Build the complete log message
        log_message = f"{colored_level} [{timestamp}] {record.getMessage()}"
        
        # Handle exception information if present
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_message += '\n' + record.exc_text
        
        return log_message

# Example usage and setup
def setup_custom_logger():
    """Setup logging with colored formatter"""
    log_level = logging.INFO #logging.INFO #logging.WARNING #logging.DEBUG Change the desired log level here

    # Create logger
    logger = logging.getLogger()
    # Set the log level the logger emits to all handlers
    logger.setLevel(log_level) 

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    #logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    console_handler = logging.StreamHandler(sys.stderr)
    # Control the log level for the console handler (the most restrictive level between the logger and the handler wins).
    console_handler.setLevel(log_level)

    # Create and set custom formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Configure AutoGen-specific loggers to use WARNING level
    autogen_modules = [
        'autogen',
        'autogen_core',
        'autogen_agentchat', 
        'autogen_ext',
        'autogen_agentchat.agents',
        'autogen_agentchat.teams',
        'autogen_agentchat.conditions',
        'autogen_ext.models',
        'autogen_ext.models.ollama',
        'autogen_ext.tools',
        'autogen_ext.tools.mcp'
    ]
    
    for module_name in autogen_modules:
        autogen_logger = logging.getLogger(module_name)
        autogen_logger.setLevel(logging.WARNING)
        # Don't add handlers here since they inherit from root logger
    
    return logger

logger = setup_custom_logger()