import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * Format VLM response text with proper styling for numbered sections
 */
export const formatVLMResponse = (text: string) => {
  // Split by numbered points (1. 2. 3. etc.)
  const numberedPattern = /(\d+\.\s\*\*[^*]+\*\*[^]*?)(?=\d+\.\s\*\*|\s*$)/g;
  const matches = text.match(numberedPattern);
  
  if (matches && matches.length > 0) {
    return (
      <Box>
        {matches.map((section, index) => {
          // Extract number, title, and content
          const titleMatch = section.match(/(\d+)\.\s\*\*([^*]+)\*\*/);
          const number = titleMatch ? titleMatch[1] : index + 1;
          const title = titleMatch ? titleMatch[2] : 'Point';
          const content = section.replace(/^\d+\.\s\*\*[^*]+\*\*\s*/, '').trim();
          
          return (
            <Box key={index} mb={2.5}>
              <Box display="flex" alignItems="flex-start" gap={1.5} mb={1}>
                <Box
                  sx={{
                    minWidth: 28,
                    height: 28,
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: '0.875rem',
                  }}
                >
                  {number}
                </Box>
                <Typography variant="subtitle1" fontWeight="600" color="primary.main" sx={{ mt: 0.3 }}>
                  {title}
                </Typography>
              </Box>
              <Box pl={5}>
                <Typography variant="body2" sx={{ lineHeight: 1.7, color: 'text.primary' }}>
                  {content}
                </Typography>
              </Box>
            </Box>
          );
        })}
      </Box>
    );
  }
  
  // Fallback: Format paragraphs with proper spacing
  const paragraphs = text.split('\n').filter(p => p.trim());
  return (
    <Box>
      {paragraphs.map((para, index) => (
        <Typography key={index} variant="body2" paragraph sx={{ lineHeight: 1.7, mb: 1.5 }}>
          {para}
        </Typography>
      ))}
    </Box>
  );
};
