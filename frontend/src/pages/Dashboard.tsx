import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  People,
  Assignment,
  CheckCircle,
  Pending,
  PersonAdd,
  LocalHospital,
  Group,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: statsData, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardService.getStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load dashboard statistics. Please try again.
      </Alert>
    );
  }

  // Build stats array based on user role
  const getStatsForRole = () => {
    if (user?.role === 'nurse') {
      return [
        {
          title: 'Total Patients',
          value: statsData?.total_patients || 0,
          icon: <People fontSize="large" />,
          color: '#1976d2',
        },
        {
          title: 'Active Sessions',
          value: statsData?.active_sessions || 0,
          icon: <Assignment fontSize="large" />,
          color: '#ed6c02',
        },
        {
          title: 'Created Today',
          value: statsData?.created_today || 0,
          icon: <PersonAdd fontSize="large" />,
          color: '#2e7d32',
        },
        {
          title: 'Pending Review',
          value: statsData?.pending_review || 0,
          icon: <Pending fontSize="large" />,
          color: '#9c27b0',
        },
      ];
    } else if (user?.role === 'doctor') {
      return [
        {
          title: 'Assigned to Me',
          value: statsData?.assigned_to_me || 0,
          icon: <Assignment fontSize="large" />,
          color: '#ed6c02',
        },
        {
          title: 'Currently Reviewing',
          value: statsData?.currently_reviewing || 0,
          icon: <LocalHospital fontSize="large" />,
          color: '#1976d2',
        },
        {
          title: 'Completed Today',
          value: statsData?.completed_today || 0,
          icon: <CheckCircle fontSize="large" />,
          color: '#2e7d32',
        },
        {
          title: 'Total Assigned',
          value: statsData?.total_assigned || 0,
          icon: <People fontSize="large" />,
          color: '#9c27b0',
        },
      ];
    } else {
      // Admin
      return [
        {
          title: 'Total Patients',
          value: statsData?.total_patients || 0,
          icon: <People fontSize="large" />,
          color: '#1976d2',
        },
        {
          title: 'Total Users',
          value: statsData?.total_users || 0,
          icon: <Group fontSize="large" />,
          color: '#9c27b0',
        },
        {
          title: 'Active Sessions',
          value: statsData?.active_sessions || 0,
          icon: <Assignment fontSize="large" />,
          color: '#ed6c02',
        },
        {
          title: 'Completed Today',
          value: statsData?.completed_today || 0,
          icon: <CheckCircle fontSize="large" />,
          color: '#2e7d32',
        },
      ];
    }
  };

  const stats = getStatsForRole();

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

