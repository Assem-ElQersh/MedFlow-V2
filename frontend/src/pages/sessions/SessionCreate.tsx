import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Alert,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { sessionService } from '../../services/sessionService';
import { patientService } from '../../services/patientService';
import { SessionCreate as SessionCreateType, SessionType } from '../../types/session';
import FileUpload from '../../components/FileUpload';

const SessionCreate: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const patientIdFromUrl = searchParams.get('patientId');

  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState('');
  const [createdSessionId, setCreatedSessionId] = useState<string | null>(null);

  const [formData, setFormData] = useState<SessionCreateType>({
    patient_id: patientIdFromUrl || '',
    session_type: 'new_problem',
    assigned_doctor_id: '',
    chief_complaint: '',
    current_state_description: '',
  });

  // Fetch patient data
  const { data: patientPortfolio, isLoading: loadingPatient } = useQuery({
    queryKey: ['patient', 'portfolio', formData.patient_id],
    queryFn: () => patientService.getPatientPortfolio(formData.patient_id),
    enabled: !!formData.patient_id,
  });

  // Mock doctors list (in production, this would come from an API)
  const mockDoctors = [
    { user_id: 'D-00001', full_name: 'Dr. Sarah Johnson' },
    { user_id: 'D-00002', full_name: 'Dr. Ahmed Hassan' },
    { user_id: 'D-00003', full_name: 'Dr. Maria Garcia' },
  ];

  const createMutation = useMutation({
    mutationFn: (data: SessionCreateType) => sessionService.createSession(data),
    onSuccess: (session) => {
      setCreatedSessionId(session.session_id);
      setActiveStep(1); // Move to file upload step
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create session');
    },
  });

  const submitMutation = useMutation({
    mutationFn: (sessionId: string) => sessionService.submitSession(sessionId),
    onSuccess: () => {
      navigate(`/sessions/${createdSessionId}`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to submit session');
    },
  });

  // Fetch current session data for file upload step
  const { data: currentSession } = useQuery({
    queryKey: ['session', createdSessionId],
    queryFn: () => sessionService.getSession(createdSessionId!),
    enabled: !!createdSessionId && activeStep === 1,
    refetchInterval: 2000, // Auto-refresh for file uploads
  });

  const handleInputChange = (field: keyof SessionCreateType, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleCreateSession = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    createMutation.mutate(formData);
  };

  const handleSubmitSession = () => {
    if (createdSessionId) {
      submitMutation.mutate(createdSessionId);
    }
  };

  const handleSkipFiles = () => {
    setActiveStep(2);
  };

  const steps = ['Session Details', 'Upload Files (Optional)', 'Review & Submit'];

  if (loadingPatient) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Box>
          <Typography variant="h4">Create New Session</Typography>
          {patientPortfolio && (
            <Typography variant="body2" color="text.secondary">
              Patient: {patientPortfolio.patient.name} ({patientPortfolio.patient.patient_id})
            </Typography>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Step 1: Session Details */}
      {activeStep === 0 && (
        <form onSubmit={handleCreateSession}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Session Information
            </Typography>

            <Box mt={2}>
              <FormControl fullWidth sx={{ mb: 2 }} required>
                <InputLabel>Session Type</InputLabel>
                <Select
                  value={formData.session_type}
                  label="Session Type"
                  onChange={(e) => handleInputChange('session_type', e.target.value as SessionType)}
                >
                  <MenuItem value="new_problem">New Problem</MenuItem>
                  <MenuItem value="follow_up">Follow-up</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }} required>
                <InputLabel>Assign to Doctor</InputLabel>
                <Select
                  value={formData.assigned_doctor_id}
                  label="Assign to Doctor"
                  onChange={(e) => handleInputChange('assigned_doctor_id', e.target.value)}
                >
                  {mockDoctors.map((doctor) => (
                    <MenuItem key={doctor.user_id} value={doctor.user_id}>
                      {doctor.full_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                required
                fullWidth
                label="Chief Complaint"
                placeholder="e.g., Persistent dry cough for 3 weeks"
                value={formData.chief_complaint}
                onChange={(e) => handleInputChange('chief_complaint', e.target.value)}
                sx={{ mb: 2 }}
                helperText="Brief description of the main health concern"
              />

              <TextField
                required
                fullWidth
                multiline
                rows={6}
                label="Current State Description"
                placeholder="Describe the patient's current symptoms, duration, severity, and any relevant observations..."
                value={formData.current_state_description}
                onChange={(e) => handleInputChange('current_state_description', e.target.value)}
                helperText="Detailed description of the patient's current condition"
              />
            </Box>
          </Paper>

          {/* Patient Context Summary */}
          {patientPortfolio && (
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Patient Context
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Age:</strong> {patientPortfolio.patient.age} years •{' '}
                <strong>Sex:</strong> {patientPortfolio.patient.sex}
              </Typography>
              {patientPortfolio.patient.chronic_diseases.length > 0 && (
                <Typography variant="body2" gutterBottom>
                  <strong>Chronic Diseases:</strong>{' '}
                  {patientPortfolio.patient.chronic_diseases.join(', ')}
                </Typography>
              )}
              {patientPortfolio.patient.allergies.length > 0 && (
                <Typography variant="body2" gutterBottom color="error">
                  <strong>Allergies:</strong> {patientPortfolio.patient.allergies.join(', ')}
                </Typography>
              )}
              {patientPortfolio.patient.current_medications.length > 0 && (
                <Typography variant="body2">
                  <strong>Current Medications:</strong>{' '}
                  {patientPortfolio.patient.current_medications
                    .map((m: any) => m.name)
                    .join(', ')}
                </Typography>
              )}
            </Paper>
          )}

          <Box display="flex" gap={2}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={createMutation.isPending || !formData.patient_id || !formData.assigned_doctor_id}
            >
              {createMutation.isPending ? 'Creating...' : 'Next: Upload Files'}
            </Button>
            <Button variant="outlined" size="large" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </Box>
        </form>
      )}

      {/* Step 2: File Upload */}
      {activeStep === 1 && currentSession && (
        <Box>
          <FileUpload
            sessionId={currentSession.session_id}
            files={currentSession.uploaded_files}
            canDelete={currentSession.session_status === 'draft'}
          />

          <Box display="flex" gap={2} mt={3}>
            <Button variant="contained" size="large" onClick={() => setActiveStep(2)}>
              Next: Review
            </Button>
            <Button variant="outlined" size="large" onClick={handleSkipFiles}>
              Skip Files
            </Button>
          </Box>
        </Box>
      )}

      {/* Step 3: Review & Submit */}
      {activeStep === 2 && currentSession && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Review Session
            </Typography>
            <Box mt={2}>
              <Typography variant="body2" gutterBottom>
                <strong>Session Type:</strong> {currentSession.session_type.replace('_', ' ')}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Assigned Doctor:</strong> {currentSession.assigned_doctor_name}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Chief Complaint:</strong> {currentSession.chief_complaint}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Current State:</strong> {currentSession.current_state_description}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Files Uploaded:</strong> {currentSession.uploaded_files.length}
              </Typography>
            </Box>
          </Paper>

          <Alert severity="info" sx={{ mb: 3 }}>
            Once submitted, the session will be processed by the VLM system and assigned to{' '}
            {currentSession.assigned_doctor_name} for review. You will not be able to edit the
            session after submission.
          </Alert>

          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              size="large"
              color="primary"
              onClick={handleSubmitSession}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Submitting...' : 'Submit Session'}
            </Button>
            <Button variant="outlined" size="large" onClick={() => setActiveStep(1)}>
              Back to Files
            </Button>
            <Button variant="outlined" size="large" color="error" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default SessionCreate;

