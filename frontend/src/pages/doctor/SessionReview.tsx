import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Chip,
  Grid,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import { ArrowBack, CheckCircle } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { doctorService } from '../../services/doctorService';
import { patientService } from '../../services/patientService';
import FileUpload from '../../components/FileUpload';
import VLMChat from '../../components/doctor/VLMChat';
import DiagnosisForm from '../../components/doctor/DiagnosisForm';

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

const SessionReview: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);

  const { data: session, isLoading } = useQuery({
    queryKey: ['doctor', 'session', sessionId],
    queryFn: () => doctorService.getSessionForReview(sessionId!),
    enabled: !!sessionId,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: patientPortfolio } = useQuery({
    queryKey: ['patient', 'portfolio', session?.patient_id],
    queryFn: () => patientService.getPatientPortfolio(session!.patient_id),
    enabled: !!session?.patient_id,
  });

  const closeMutation = useMutation({
    mutationFn: () => doctorService.closeSession(sessionId!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'queue'] });
      navigate('/doctor/queue');
    },
  });

  if (isLoading || !session) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const patient = patientPortfolio?.patient;
  const vlmOutput = session.vlm_initial_output;
  const vlmFailed = session.vlm_initial_status === 'failed' || session.session_status === 'vlm_failed';

  const canClose = !!session.diagnosis;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate('/doctor/queue')} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Box>
            <Typography variant="h4">Session Review</Typography>
            <Typography variant="body2" color="text.secondary">
              {session.session_id} • {session.patient_name}
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            label={session.session_status.replace('_', ' ')}
            color={session.session_status === 'completed' ? 'success' : 'warning'}
          />
          <Button
            variant="contained"
            color="success"
            startIcon={<CheckCircle />}
            onClick={() => setCloseDialogOpen(true)}
            disabled={!canClose || closeMutation.isPending}
          >
            Complete Session
          </Button>
        </Box>
      </Box>

      {!canClose && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please fill out the diagnosis form before completing the session.
        </Alert>
      )}

      {/* Tabs */}
      <Paper>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Patient History" />
          <Tab label="Current Session" />
          <Tab label="Files" />
          <Tab label="VLM Analysis" />
          <Tab label="Diagnosis" />
        </Tabs>

        {/* Tab 1: Patient History */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ px: 3 }}>
            {patient && (
              <>
                <Typography variant="h6" gutterBottom>
                  Demographics
                </Typography>
                <Grid container spacing={2} mb={3}>
                  <Grid item xs={6} md={3}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Age
                    </Typography>
                    <Typography>{patient.age} years</Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Sex
                    </Typography>
                    <Typography sx={{ textTransform: 'capitalize' }}>{patient.sex}</Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Smoking Status
                    </Typography>
                    <Typography sx={{ textTransform: 'capitalize' }}>
                      {patient.smoking_status}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Total Sessions
                    </Typography>
                    <Typography>{patient.total_sessions}</Typography>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />

                <Typography variant="h6" gutterBottom>
                  Medical History
                </Typography>
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Chronic Diseases
                  </Typography>
                  {patient.chronic_diseases.length > 0 ? (
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {patient.chronic_diseases.map((disease: string, i: number) => (
                        <Chip key={i} label={disease} />
                      ))}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">None</Typography>
                  )}
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom color="error">
                    Allergies
                  </Typography>
                  {patient.allergies.length > 0 ? (
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {patient.allergies.map((allergy: string, i: number) => (
                        <Chip key={i} label={allergy} color="error" />
                      ))}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">None</Typography>
                  )}
                </Box>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Current Medications
                  </Typography>
                  {patient.current_medications.length > 0 ? (
                    patient.current_medications.map((med: any, i: number) => (
                      <Typography key={i} variant="body2">
                        • {med.name} - {med.dosage} - {med.frequency}
                      </Typography>
                    ))
                  ) : (
                    <Typography color="text.secondary">None</Typography>
                  )}
                </Box>
              </>
            )}
          </Box>
        </TabPanel>

        {/* Tab 2: Current Session */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ px: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Session Type
                </Typography>
                <Typography sx={{ textTransform: 'capitalize' }}>
                  {session.session_type.replace('_', ' ')}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Session Date
                </Typography>
                <Typography>{new Date(session.session_date).toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Chief Complaint
                </Typography>
                <Typography>{session.chief_complaint}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Current State Description
                </Typography>
                <Typography>{session.current_state_description}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Nurse
                </Typography>
                <Typography>{session.nurse_name}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Assigned Doctor
                </Typography>
                <Typography>{session.assigned_doctor_name}</Typography>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Tab 3: Files */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ px: 3 }}>
            {session.uploaded_files.length > 0 ? (
              <FileUpload
                sessionId={session.session_id}
                files={session.uploaded_files}
                canDelete={false}
              />
            ) : (
              <Box textAlign="center" py={4}>
                <Typography variant="h6" color="text.secondary">
                  No files uploaded
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This session was created as text-only
                </Typography>
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Tab 4: VLM Analysis */}
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ px: 3 }}>
            {vlmFailed ? (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  VLM Processing Failed
                </Typography>
                <Typography variant="body2">
                  The VLM system encountered an error while processing this session. 
                  However, all session data (chief complaint, patient state, uploaded files) 
                  is still available for your review. You can proceed with diagnosis based on 
                  the available information.
                </Typography>
              </Alert>
            ) : vlmOutput ? (
              <>
                <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.50' }}>
                  <Typography variant="h6" gutterBottom>
                    VLM Initial Analysis
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {vlmOutput.findings}
                  </Typography>

                  <Typography variant="subtitle2" gutterBottom>
                    Key Observations
                  </Typography>
                  <Box component="ul" sx={{ pl: 2 }}>
                    {vlmOutput.key_observations.map((obs: string, i: number) => (
                      <li key={i}>
                        <Typography variant="body2">{obs}</Typography>
                      </li>
                    ))}
                  </Box>

                  <Typography variant="subtitle2" gutterBottom mt={2}>
                    Suggested Considerations
                  </Typography>
                  <Box component="ul" sx={{ pl: 2 }}>
                    {vlmOutput.suggested_considerations.map((cons: string, i: number) => (
                      <li key={i}>
                        <Typography variant="body2">{cons}</Typography>
                      </li>
                    ))}
                  </Box>

                  <Typography variant="subtitle2" gutterBottom mt={2}>
                    Differential Patterns
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {vlmOutput.differential_patterns.map((pattern: string, i: number) => (
                      <Chip key={i} label={pattern} variant="outlined" />
                    ))}
                  </Box>

                  <Typography variant="caption" color="text.secondary" display="block" mt={2}>
                    Model: {vlmOutput.model_version} • Processing time:{' '}
                    {vlmOutput.processing_time_seconds}s
                  </Typography>
                </Paper>

                <Divider sx={{ my: 3 }} />

                <Typography variant="h6" gutterBottom>
                  Chat with VLM
                </Typography>
                <VLMChat sessionId={session.session_id} chatHistory={session.vlm_chat_history} />
              </>
            ) : (
              <Box textAlign="center" py={4}>
                <CircularProgress sx={{ mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  VLM Processing in progress...
                </Typography>
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Tab 5: Diagnosis */}
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ px: 3 }}>
            <DiagnosisForm
              sessionId={session.session_id}
              initialDiagnosis={session.diagnosis}
              initialPendingTests={session.pending_tests}
            />
          </Box>
        </TabPanel>
      </Paper>

      {/* Close Session Dialog */}
      <Dialog open={closeDialogOpen} onClose={() => setCloseDialogOpen(false)}>
        <DialogTitle>Complete Session</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to complete this session? The session will be closed and cannot
            be edited further.
          </Typography>
          {session.pending_tests?.required && (
            <Alert severity="info" sx={{ mt: 2 }}>
              A follow-up session will be automatically created for pending tests.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloseDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => closeMutation.mutate()}
            disabled={closeMutation.isPending}
          >
            {closeMutation.isPending ? 'Closing...' : 'Complete Session'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SessionReview;

