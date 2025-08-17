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
def setup_colored_logging():
    """Setup logging with colored formatter"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) #logging.DEBUG Change the desired log level here
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create and set custom formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

logger = setup_colored_logging()