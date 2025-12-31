import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  CircularProgress,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Snackbar,
} from '@mui/material';
import { ArrowBack, Edit, Add, Delete } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patientService } from '../../services/patientService';
import { sessionService } from '../../services/sessionService';
import { useAuth } from '../../contexts/AuthContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const PatientProfile: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  // Check if user has permission to edit patients (nurse, doctor, admin)
  const canEditPatient = user && ['nurse', 'doctor', 'admin'].includes(user.role);
  const canDeleteSession = user && ['nurse', 'admin'].includes(user.role);
  
  // Delete session state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['patient', 'portfolio', patientId],
    queryFn: () => patientService.getPatientPortfolio(patientId!),
    enabled: !!patientId,
  });

  // Delete session mutation
  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => sessionService.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient', 'portfolio', patientId] });
      setSnackbar({ open: true, message: 'Session deleted successfully', severity: 'success' });
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete session';
      setSnackbar({ open: true, message, severity: 'error' });
      setDeleteDialogOpen(false);
    },
  });

  const handleDeleteClick = (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (sessionToDelete) {
      deleteMutation.mutate(sessionToDelete);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setSessionToDelete(null);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!portfolio) {
    return <Typography>Patient not found</Typography>;
  }

  const { patient, sessions } = portfolio;

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate('/patients')} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Box>
            <Typography variant="h4">{patient.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {patient.patient_id} • {patient.age} years old
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => navigate(`/sessions/new?patientId=${patient.patient_id}`)}
          >
            New Session
          </Button>
          {canEditPatient && (
            <Button 
              variant="outlined" 
              startIcon={<Edit />}
              onClick={() => navigate(`/patients/${patient.patient_id}/edit`)}
            >
              Edit Patient
            </Button>
          )}
        </Box>
      </Box>

      <Paper>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Demographics" />
          <Tab label="Medical History" />
          <Tab label={`Sessions (${patient.total_sessions})`} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ px: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Full Name
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.name}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  National ID
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.national_id}
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  Date of Birth
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {new Date(patient.date_of_birth).toLocaleDateString()} ({patient.age} years old)
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  Sex
                </Typography>
                <Typography variant="body1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                  {patient.sex}
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  Smoking Status
                </Typography>
                <Typography variant="body1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                  {patient.smoking_status}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Primary Phone
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.phone_primary}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Secondary Phone
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.phone_secondary || 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Email
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.email || 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Address
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {patient.address || 'N/A'}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ px: 3 }}>
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Chronic Diseases
              </Typography>
              {patient.chronic_diseases.length > 0 ? (
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {patient.chronic_diseases.map((disease: string, index: number) => (
                    <Chip key={index} label={disease} color="primary" />
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">None recorded</Typography>
              )}
            </Box>

            <Box mb={3}>
              <Typography variant="h6" gutterBottom color="error">
                Allergies
              </Typography>
              {patient.allergies.length > 0 ? (
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {patient.allergies.map((allergy: string, index: number) => (
                    <Chip key={index} label={allergy} color="error" />
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">None recorded</Typography>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Current Medications
              </Typography>
              {patient.current_medications.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Medication</TableCell>
                        <TableCell>Dosage</TableCell>
                        <TableCell>Frequency</TableCell>
                        <TableCell>Instructions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {patient.current_medications.map((med: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{med.name}</TableCell>
                          <TableCell>{med.dosage}</TableCell>
                          <TableCell>{med.frequency}</TableCell>
                          <TableCell>{med.instructions || 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="text.secondary">None recorded</Typography>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            <Box>
              <Typography variant="h6" gutterBottom>
                Surgical History
              </Typography>
              {patient.surgical_history.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Procedure</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Notes</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {patient.surgical_history.map((surgery: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{surgery.procedure}</TableCell>
                          <TableCell>{new Date(surgery.date).toLocaleDateString()}</TableCell>
                          <TableCell>{surgery.notes || 'N/A'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="text.secondary">None recorded</Typography>
              )}
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ px: 3 }}>
            {sessions.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Session ID</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Chief Complaint</TableCell>
                      <TableCell>Doctor</TableCell>
                      <TableCell>Status</TableCell>
                      {canDeleteSession && <TableCell align="center">Actions</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sessions.map((session: any) => (
                      <TableRow
                        key={session.session_id}
                        hover
                        sx={{ cursor: 'pointer' }}
                        onClick={() => navigate(`/sessions/${session.session_id}`)}
                      >
                        <TableCell>{session.session_id}</TableCell>
                        <TableCell>{new Date(session.session_date).toLocaleString()}</TableCell>
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
                              session.session_status === 'completed'
                                ? 'success'
                                : session.session_status === 'awaiting_doctor'
                                ? 'warning'
                                : 'info'
                            }
                          />
                        </TableCell>
                        {canDeleteSession && (
                          <TableCell align="center">
                            {session.session_status !== 'completed' && (
                              <IconButton
                                size="small"
                                color="error"
                                onClick={(e) => handleDeleteClick(session.session_id, e)}
                                title="Delete session"
                              >
                                <Delete />
                              </IconButton>
                            )}
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box textAlign="center" py={4}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No sessions yet
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Create a new session to begin patient care
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => navigate(`/sessions/new?patientId=${patient.patient_id}`)}
                  sx={{ mt: 2 }}
                >
                  Create First Session
                </Button>
              </Box>
            )}
          </Box>
        </TabPanel>
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel}>
        <DialogTitle>Delete Session</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete session <strong>{sessionToDelete}</strong>?
            This action cannot be undone. All session data including uploaded files will be permanently deleted.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="inherit">
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PatientProfile;

