import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Info,
  Person,
  Assignment,
  LocalHospital,
  Security,
  Settings,
  Refresh,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { adminService, LogEntry } from '../../services/adminService';

const SystemLogs: React.FC = () => {
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [levelFilter, setLevelFilter] = useState<string>('all');

  const { data: logs, isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['admin', 'logs', categoryFilter, levelFilter],
    queryFn: () =>
      adminService.getLogs({
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        level: levelFilter !== 'all' ? levelFilter : undefined,
        limit: 100,
      }),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin', 'logs', 'stats'],
    queryFn: () => adminService.getLogsStats(),
    refetchInterval: 15000,
  });

  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['admin', 'system', 'status'],
    queryFn: () => adminService.getSystemStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle sx={{ fontSize: 18 }} />;
      case 'error':
        return <Error sx={{ fontSize: 18 }} />;
      case 'warning':
        return <Warning sx={{ fontSize: 18 }} />;
      default:
        return <Info sx={{ fontSize: 18 }} />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'auth':
        return <Security fontSize="small" />;
      case 'session':
        return <Assignment fontSize="small" />;
      case 'vlm':
        return <LocalHospital fontSize="small" />;
      case 'admin':
        return <Settings fontSize="small" />;
      default:
        return <Info fontSize="small" />;
    }
  };

  const getStatusColor = (status: string) => {
    if (status === 'connected') return 'success';
    if (status === 'disconnected') return 'error';
    return 'warning';
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box>
          <Typography variant="h4">System Logs & Status</Typography>
          <Typography variant="body2" color="text.secondary">
            Monitor system activity and connection status
          </Typography>
        </Box>
      </Box>

      {/* System Status Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Database Status</Typography>
                {statusLoading ? (
                  <CircularProgress size={20} />
                ) : (
                  <Chip
                    label={systemStatus?.mongodb || 'Unknown'}
                    color={getStatusColor(systemStatus?.mongodb || '')}
                    size="small"
                  />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary">
                MongoDB connection status
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">VLM Service</Typography>
                {statusLoading ? (
                  <CircularProgress size={20} />
                ) : (
                  <Chip
                    label={systemStatus?.vlm_service || 'Unknown'}
                    color={getStatusColor(systemStatus?.vlm_service || '')}
                    size="small"
                  />
                )}
              </Box>
              {systemStatus?.vlm_model && (
                <Typography variant="body2" color="text.secondary">
                  Model: {systemStatus.vlm_model}
                </Typography>
              )}
              {systemStatus?.vlm_device && (
                <Typography variant="body2" color="text.secondary">
                  Device: {systemStatus.vlm_device}
                </Typography>
              )}
              {systemStatus?.vlm_error && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  {systemStatus.vlm_error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics Cards */}
      {statsLoading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="primary">
                  {stats?.total || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Logs
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main">
                  {stats?.by_category?.auth || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Auth Events
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="info.main">
                  {stats?.by_category?.session || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Session Events
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="error.main">
                  {stats?.by_level?.error || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Errors
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="Category"
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="auth">Authentication</MenuItem>
                <MenuItem value="session">Sessions</MenuItem>
                <MenuItem value="vlm">VLM</MenuItem>
                <MenuItem value="system">System</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Level</InputLabel>
              <Select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                label="Level"
              >
                <MenuItem value="all">All Levels</MenuItem>
                <MenuItem value="success">Success</MenuItem>
                <MenuItem value="info">Info</MenuItem>
                <MenuItem value="warning">Warning</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Chip
              icon={<Refresh />}
              label="Auto-refresh: 10s"
              color="primary"
              variant="outlined"
              onClick={() => refetchLogs()}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Logs Table */}
      <Paper>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Session/Patient</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logsLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : logs && logs.length > 0 ? (
                logs.map((log: LogEntry) => (
                  <TableRow key={log.log_id} hover>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(log.timestamp).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getLevelIcon(log.level)}
                        label={log.level}
                        color={getLevelColor(log.level) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getCategoryIcon(log.category)}
                        label={log.category}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{log.message}</Typography>
                    </TableCell>
                    <TableCell>
                      {log.user_name && (
                        <Box>
                          <Typography variant="body2">{log.user_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {log.user_role}
                          </Typography>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      {log.session_id && (
                        <Box>
                          <Typography variant="caption" display="block">
                            {log.session_id}
                          </Typography>
                          {log.patient_name && (
                            <Typography variant="caption" color="text.secondary">
                              {log.patient_name}
                            </Typography>
                          )}
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No logs found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default SystemLogs;
