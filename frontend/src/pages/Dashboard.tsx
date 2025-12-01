import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
} from '@mui/material';
import {
  People,
  Assignment,
  CheckCircle,
  Pending,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const stats = [
    {
      title: 'Total Patients',
      value: '0',
      icon: <People fontSize="large" />,
      color: '#1976d2',
    },
    {
      title: 'Active Sessions',
      value: '0',
      icon: <Assignment fontSize="large" />,
      color: '#ed6c02',
    },
    {
      title: 'Completed Today',
      value: '0',
      icon: <CheckCircle fontSize="large" />,
      color: '#2e7d32',
    },
    {
      title: 'Pending Review',
      value: '0',
      icon: <Pending fontSize="large" />,
      color: '#9c27b0',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome, {user?.full_name}
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 4 }}>
        {user?.role === 'nurse' && 'Manage patients and create medical sessions'}
        {user?.role === 'doctor' && 'Review sessions and provide diagnoses'}
        {user?.role === 'admin' && 'System administration and user management'}
      </Typography>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="text.secondary" variant="body2" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4">{stat.value}</Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {user?.role === 'nurse' && 'Search for a patient or create a new patient record to begin.'}
          {user?.role === 'doctor' && 'Visit the Doctor Queue to review pending sessions.'}
          {user?.role === 'admin' && 'Manage users and system settings.'}
        </Typography>
      </Paper>
    </Box>
  );
};

export default Dashboard;

