import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  FormControlLabel,
  Switch,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { doctorService, SessionSummary } from '../../services/doctorService';

const DoctorQueue: React.FC = () => {
  const navigate = useNavigate();
  const [assignedToMe, setAssignedToMe] = useState(false);

  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['doctor', 'queue', assignedToMe],
    queryFn: () => doctorService.getQueue(assignedToMe),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const handleRowClick = (sessionId: string) => {
    navigate(`/doctor/sessions/${sessionId}`);
  };

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
        Failed to load sessions. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Doctor Queue</Typography>
        <FormControlLabel
          control={
            <Switch
              checked={assignedToMe}
              onChange={(e) => setAssignedToMe(e.target.checked)}
            />
          }
          label="Show only assigned to me"
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Session ID</TableCell>
              <TableCell>Patient</TableCell>
              <TableCell>Date/Time</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Chief Complaint</TableCell>
              <TableCell>Assigned Doctor</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sessions && sessions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" py={4}>
                    No sessions in queue
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sessions?.map((session: SessionSummary) => (
                <TableRow
                  key={session.session_id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleRowClick(session.session_id)}
                >
                  <TableCell>{session.session_id}</TableCell>
                  <TableCell>{session.patient_name}</TableCell>
                  <TableCell>
                    {new Date(session.session_date).toLocaleString()}
                  </TableCell>
                  <TableCell sx={{ textTransform: 'capitalize' }}>
                    {session.session_type.replace('_', ' ')}
                  </TableCell>
                  <TableCell>{session.chief_complaint}</TableCell>
                  <TableCell>{session.assigned_doctor_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={session.session_status.replace('_', ' ')}
                      size="small"
                      color={
                        session.session_status === 'vlm_failed'
                          ? 'error'
                          : session.session_status === 'doctor_reviewing'
                          ? 'info'
                          : session.session_status === 'awaiting_doctor'
                          ? 'warning'
                          : 'default'
                      }
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default DoctorQueue;

