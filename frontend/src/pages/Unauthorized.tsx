import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Block } from '@mui/icons-material';

const Unauthorized: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="background.default"
    >
      <Paper elevation={3} sx={{ p: 4, textAlign: 'center', maxWidth: 500 }}>
        <Block sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          You don't have permission to access this page.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/')}>
          Go to Dashboard
        </Button>
      </Paper>
    </Box>
  );
};

export default Unauthorized;

