import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Avatar,
  CircularProgress,
} from '@mui/material';
import { Send, SmartToy, Person } from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { doctorService } from '../../services/doctorService';

interface VLMChatProps {
  sessionId: string;
  chatHistory: any[];
}

const VLMChat: React.FC<VLMChatProps> = ({ sessionId, chatHistory }) => {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const chatMutation = useMutation({
    mutationFn: (msg: string) => doctorService.chatWithVLM(sessionId, msg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'session', sessionId] });
      setMessage('');
    },
  });

  const handleSendMessage = () => {
    if (message.trim()) {
      chatMutation.mutate(message);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2, maxHeight: 500, overflow: 'auto' }}>
        {chatHistory.length === 0 ? (
          <Box textAlign="center" py={4}>
            <SmartToy sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              VLM Assistant Ready
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask questions or provide additional clinical observations
            </Typography>
          </Box>
        ) : (
          <Box>
            {chatHistory.map((msg, index) => (
              <Box key={index} mb={3}>
                {/* Doctor Message */}
                <Box display="flex" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <Person />
                  </Avatar>
                  <Box flex={1}>
                    <Typography variant="subtitle2" color="text.secondary">
                      You
                    </Typography>
                    <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                      <Typography variant="body1">{msg.content}</Typography>
                    </Paper>
                  </Box>
                </Box>

                {/* VLM Response */}
                {msg.vlm_response && (
                  <Box display="flex" gap={2} pl={7}>
                    <Avatar sx={{ bgcolor: 'secondary.main' }}>
                      <SmartToy />
                    </Avatar>
                    <Box flex={1}>
                      <Typography variant="subtitle2" color="text.secondary">
                        VLM Assistant
                      </Typography>
                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="body1">
                          {msg.vlm_response.findings}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          display="block"
                          mt={1}
                        >
                          Processing time: {msg.vlm_response.processing_time}s
                        </Typography>
                      </Paper>
                    </Box>
                  </Box>
                )}
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </Box>
        )}
      </Paper>

      <Box display="flex" gap={2}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Ask VLM a question or provide additional observations..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={chatMutation.isPending}
        />
        <Button
          variant="contained"
          endIcon={chatMutation.isPending ? <CircularProgress size={20} /> : <Send />}
          onClick={handleSendMessage}
          disabled={!message.trim() || chatMutation.isPending}
          sx={{ minWidth: 120 }}
        >
          {chatMutation.isPending ? 'Sending...' : 'Ask VLM'}
        </Button>
      </Box>
    </Box>
  );
};

export default VLMChat;

