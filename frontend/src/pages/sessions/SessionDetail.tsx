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
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { sessionService } from '../../services/sessionService';
import { patientService } from '../../services/patientService';

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

const SessionDetail: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => sessionService.getSession(sessionId!),
    enabled: !!sessionId,
  });

  const { data: patientPortfolio } = useQuery({
    queryKey: ['patient', 'portfolio', session?.patient_id],
    queryFn: () => patientService.getPatientPortfolio(session!.patient_id),
    enabled: !!session?.patient_id,
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
  const diagnosis = session.diagnosis;
  const isCompleted = ['completed', 'pending_tests'].includes(session.session_status);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Box>
            <Typography variant="h4">Session Detail</Typography>
            <Typography variant="body2" color="text.secondary">
              {session.session_id} • {session.patient_name}
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            label={session.session_status.replace('_', ' ')}
            size="medium"
            color={
              isCompleted
                ? 'success'
                : session.session_status === 'doctor_reviewing'
                ? 'info'
                : session.session_status === 'awaiting_doctor'
                ? 'warning'
                : 'default'
            }
          />
        </Box>
      </Box>

      <Paper>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Session Info" />
          <Tab label="Patient Demographics" />
          <Tab label="Medical History" />
          {vlmOutput && <Tab label="VLM Analysis" />}
          {diagnosis && <Tab label="Diagnosis" />}
        </Tabs>

        {/* Tab 1: Session Info */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ px: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Session Type
                </Typography>
                <Typography variant="body1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                  {session.session_type.replace('_', ' ')}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Session Date
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {new Date(session.session_date).toLocaleString()}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Assigned Doctor
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {session.assigned_doctor_name}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Nurse
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {session.nurse_name}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Chief Complaint
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {session.chief_complaint}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Current State Description
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {session.current_state_description}
                </Typography>
              </Grid>
            </Grid>

            {session.uploaded_files.length > 0 && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="h6" gutterBottom>
                  Uploaded Files
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>File Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Size (MB)</TableCell>
                        <TableCell>Upload Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {session.uploaded_files.map((file: any) => (
                        <TableRow key={file.file_id}>
                          <TableCell>{file.file_name}</TableCell>
                          <TableCell sx={{ textTransform: 'capitalize' }}>
                            {file.file_type.replace('_', ' ')}
                          </TableCell>
                          <TableCell>{file.file_size_mb}</TableCell>
                          <TableCell>
                            {new Date(file.upload_timestamp).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Box>
        </TabPanel>

        {/* Tab 2: Patient Demographics */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ px: 3 }}>
            {patient ? (
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
                    Age
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {patient.age} years old
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Sex
                  </Typography>
                  <Typography variant="body1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                    {patient.sex}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Phone
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {patient.phone_primary}
                  </Typography>
                </Grid>
              </Grid>
            ) : (
              <Typography color="text.secondary">Loading patient information...</Typography>
            )}
          </Box>
        </TabPanel>

        {/* Tab 3: Medical History */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ px: 3 }}>
            {patient ? (
              <>
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
              </>
            ) : (
              <Typography color="text.secondary">Loading medical history...</Typography>
            )}
          </Box>
        </TabPanel>

        {/* Tab 4: VLM Analysis (if available) */}
        {vlmOutput && (
          <TabPanel value={tabValue} index={3}>
            <Box sx={{ px: 3 }}>
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

                <Typography variant="caption" color="text.secondary" display="block" mt={2}>
                  Model: {vlmOutput.model_version}
                </Typography>
              </Paper>
            </Box>
          </TabPanel>
        )}

        {/* Tab 5: Diagnosis (if available) */}
        {diagnosis && (
          <TabPanel value={tabValue} index={vlmOutput ? 4 : 3}>
            <Box sx={{ px: 3 }}>
              <Paper sx={{ p: 3, mb: 3, bgcolor: 'success.50' }}>
                <Typography variant="h6" gutterBottom>
                  Diagnosis
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Primary Diagnosis
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {diagnosis.primary_diagnosis}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Severity
                    </Typography>
                    <Typography variant="body1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                      {diagnosis.severity}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Doctor Notes
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {diagnosis.doctor_notes}
                    </Typography>
                  </Grid>
                  {diagnosis.recommendations && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Recommendations
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        {diagnosis.recommendations}
                      </Typography>
                    </Grid>
                  )}
                </Grid>

                {diagnosis.medications && diagnosis.medications.length > 0 && (
                  <>
                    <Divider sx={{ my: 3 }} />
                    <Typography variant="subtitle2" gutterBottom>
                      Medications
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Dosage</TableCell>
                            <TableCell>Duration</TableCell>
                            <TableCell>Instructions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {diagnosis.medications.map((med: any, index: number) => (
                            <TableRow key={index}>
                              <TableCell>{med.name}</TableCell>
                              <TableCell>{med.dosage}</TableCell>
                              <TableCell>{med.duration}</TableCell>
                              <TableCell>{med.instructions}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </>
                )}

                {diagnosis.follow_up_required && (
                  <>
                    <Divider sx={{ my: 3 }} />
                    <Alert severity="info">
                      <Typography variant="subtitle2" gutterBottom>
                        Follow-up Required
                      </Typography>
                      {diagnosis.follow_up_date && (
                        <Typography variant="body2">
                          Date: {new Date(diagnosis.follow_up_date).toLocaleDateString()}
                        </Typography>
                      )}
                      {diagnosis.follow_up_reason && (
                        <Typography variant="body2">
                          Reason: {diagnosis.follow_up_reason}
                        </Typography>
                      )}
                    </Alert>
                  </>
                )}

                {session.pending_tests?.required && (
                  <>
                    <Divider sx={{ my: 3 }} />
                    <Alert severity="warning">
                      <Typography variant="subtitle2" gutterBottom>
                        Pending Tests
                      </Typography>
                      <Box component="ul" sx={{ mt: 1, mb: 0 }}>
                        {session.pending_tests.tests_requested.map((test: string, index: number) => (
                          <li key={index}>
                            <Typography variant="body2">{test}</Typography>
                          </li>
                        ))}
                      </Box>
                      {session.pending_tests.instructions_to_patient && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Instructions: {session.pending_tests.instructions_to_patient}
                        </Typography>
                      )}
                    </Alert>
                  </>
                )}
              </Paper>
            </Box>
          </TabPanel>
        )}
      </Paper>
    </Box>
  );
};

export default SessionDetail;

