# Totally AI generated (Claude Sonnet 4)
import re
#import asyncio
from typing import AsyncGenerator, List
#import json

class MarkdownStreamer:
    def __init__(self):
        self.buffer = ""
        self.in_code_block = False
        self.code_block_lang = ""
        self.in_list = False
        self.list_indent = 0
        
        # Markdown patterns
        self.code_block_pattern = re.compile(r'^```(\w*)')
        self.code_end_pattern = re.compile(r'^```\s*$')
        self.header_pattern = re.compile(r'^#{1,6}\s+')
        self.list_pattern = re.compile(r'^(\s*)([-*+]|\d+\.)\s+')
        self.bold_pattern = re.compile(r'\*\*.*?\*\*|\__.*?\__')
        self.italic_pattern = re.compile(r'\*.*?\*|\_.*?\_')
        self.inline_code_pattern = re.compile(r'`[^`]+`')
    
    def detect_markdown_boundaries(self, text: str) -> List[str]:
        """Split text at natural Markdown boundaries"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code blocks
            if self.code_block_pattern.match(line.strip()):
                # Start of code block - find the end
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                
                code_chunk = [line]
                i += 1
                while i < len(lines):
                    code_chunk.append(lines[i])
                    if self.code_end_pattern.match(lines[i].strip()):
                        break
                    i += 1
                
                chunks.append('\n'.join(code_chunk))
                i += 1
                continue
            
            # Check for headers
            elif self.header_pattern.match(line):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                current_chunk.append(line)
            
            # Check for lists
            elif self.list_pattern.match(line):
                if not self.in_list and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                current_chunk.append(line)
                self.in_list = True
            
            # Empty line - potential boundary
            elif line.strip() == '':
                current_chunk.append(line)
                if self.in_list:
                    # End of list
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    self.in_list = False
            
            else:
                current_chunk.append(line)
                if self.in_list and not self.list_pattern.match(line):
                    self.in_list = False
            
            i += 1
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def is_complete_markdown_element(self, text: str) -> bool:
        """Check if text contains complete Markdown elements"""
        lines = text.strip().split('\n')
        
        # Check for complete code blocks
        code_starts = len(re.findall(r'^```', text, re.MULTILINE))
        if code_starts % 2 != 0:  # Incomplete code block
            return False
        
        # Check for complete bold/italic
        bold_count = len(re.findall(r'\*\*', text))
        if bold_count % 2 != 0:  # Incomplete bold
            return False
        
        # Check for complete inline code
        inline_code_count = len(re.findall(r'`', text))
        if inline_code_count % 2 != 0:  # Incomplete inline code
            return False
        
        return True
    
    async def stream_with_markdown_awareness(self, content_generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Stream content while preserving Markdown structure"""
        buffer = ""
        
        async for chunk in content_generator:
            buffer += chunk
            
            # Try to extract complete markdown elements
            while buffer:
                # Look for natural break points
                sentences = re.split(r'([.!?]\s+)', buffer)
                
                if len(sentences) < 2:
                    break
                
                # Build complete sentence
                complete_part = ""
                remaining = buffer
                
                for i in range(0, len(sentences) - 1, 2):
                    if i + 1 < len(sentences):
                        sentence = sentences[i] + sentences[i + 1]
                        test_content = complete_part + sentence
                        
                        if self.is_complete_markdown_element(test_content):
                            complete_part = test_content
                            remaining = ''.join(sentences[i + 2:])
                        else:
                            break
                
                if complete_part and complete_part != buffer:
                    yield complete_part
                    buffer = remaining
                else:
                    # No complete elements found, wait for more content
                    break
        
        # Send any remaining content
        if buffer.strip():
            yield buffer