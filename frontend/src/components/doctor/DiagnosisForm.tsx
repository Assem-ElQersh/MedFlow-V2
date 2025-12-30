import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Paper,
  Grid,
  Checkbox,
  FormControlLabel,
  Divider,
  Alert,
} from '@mui/material';
import { Add, Delete, Save } from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { doctorService, Diagnosis, Medication, PendingTests } from '../../services/doctorService';

interface DiagnosisFormProps {
  sessionId: string;
  initialDiagnosis?: Diagnosis;
  initialPendingTests?: PendingTests;
  onComplete?: () => void;
}

const DiagnosisForm: React.FC<DiagnosisFormProps> = ({
  sessionId,
  initialDiagnosis,
  initialPendingTests,
  onComplete,
}) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');

  const [diagnosis, setDiagnosis] = useState<Diagnosis>({
    primary_diagnosis: initialDiagnosis?.primary_diagnosis || '',
    severity: initialDiagnosis?.severity || 'mild',
    medications: initialDiagnosis?.medications || [],
    recommendations: initialDiagnosis?.recommendations || '',
    follow_up_required: initialDiagnosis?.follow_up_required || false,
    follow_up_reason: initialDiagnosis?.follow_up_reason || '',
    follow_up_date: initialDiagnosis?.follow_up_date || '',
    doctor_notes: initialDiagnosis?.doctor_notes || '',
  });

  const [pendingTests, setPendingTests] = useState<PendingTests>({
    required: initialPendingTests?.required || false,
    tests_requested: initialPendingTests?.tests_requested || [],
    instructions_to_patient: initialPendingTests?.instructions_to_patient || '',
  });

  const [newTest, setNewTest] = useState('');

  const saveMutation = useMutation({
    mutationFn: async () => {
      // Filter out empty medications before submitting
      const filteredDiagnosis = {
        ...diagnosis,
        medications: diagnosis.medications.filter(
          med => med.name.trim() && med.dosage.trim() && med.duration.trim()
        ),
      };
      await doctorService.submitDiagnosis(sessionId, filteredDiagnosis);
      await doctorService.setPendingTests(sessionId, pendingTests);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'session', sessionId] });
      if (onComplete) onComplete();
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        // FastAPI validation errors
        const messages = detail
          .map((d: any) => `${d.loc?.join(' → ') || 'Field'}: ${d.msg}`)
          .join('; ');
        setError(messages);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Failed to save diagnosis');
      }
    },
  });

  const handleAddMedication = () => {
    setDiagnosis({
      ...diagnosis,
      medications: [
        ...diagnosis.medications,
        { name: '', dosage: '', duration: '', instructions: '' },
      ],
    });
  };

  const handleUpdateMedication = (index: number, field: keyof Medication, value: string) => {
    const updated = [...diagnosis.medications];
    updated[index] = { ...updated[index], [field]: value };
    setDiagnosis({ ...diagnosis, medications: updated });
  };

  const handleRemoveMedication = (index: number) => {
    const updated = diagnosis.medications.filter((_, i) => i !== index);
    setDiagnosis({ ...diagnosis, medications: updated });
  };

  const handleAddTest = () => {
    if (newTest.trim()) {
      setPendingTests({
        ...pendingTests,
        tests_requested: [...pendingTests.tests_requested, newTest.trim()],
      });
      setNewTest('');
    }
  };

  const handleRemoveTest = (index: number) => {
    const updated = pendingTests.tests_requested.filter((_, i) => i !== index);
    setPendingTests({ ...pendingTests, tests_requested: updated });
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Diagnosis
        </Typography>

        <TextField
          fullWidth
          required
          label="Primary Diagnosis"
          value={diagnosis.primary_diagnosis}
          onChange={(e) => setDiagnosis({ ...diagnosis, primary_diagnosis: e.target.value })}
          sx={{ mb: 2 }}
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Severity</InputLabel>
          <Select
            value={diagnosis.severity}
            label="Severity"
            onChange={(e) => setDiagnosis({ ...diagnosis, severity: e.target.value as any })}
          >
            <MenuItem value="mild">Mild</MenuItem>
            <MenuItem value="moderate">Moderate</MenuItem>
            <MenuItem value="severe">Severe</MenuItem>
          </Select>
        </FormControl>

        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="subtitle1">Medications</Typography>
            <Button startIcon={<Add />} onClick={handleAddMedication}>
              Add Medication
            </Button>
          </Box>

          {diagnosis.medications.map((med, index) => (
            <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Name"
                    value={med.name}
                    onChange={(e) => handleUpdateMedication(index, 'name', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Dosage"
                    value={med.dosage}
                    onChange={(e) => handleUpdateMedication(index, 'dosage', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Duration"
                    value={med.duration}
                    onChange={(e) => handleUpdateMedication(index, 'duration', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Instructions"
                    value={med.instructions}
                    onChange={(e) => handleUpdateMedication(index, 'instructions', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={1} display="flex" alignItems="center">
                  <IconButton color="error" onClick={() => handleRemoveMedication(index)}>
                    <Delete />
                  </IconButton>
                </Grid>
              </Grid>
            </Paper>
          ))}
        </Box>

        <TextField
          fullWidth
          multiline
          rows={3}
          label="Recommendations"
          value={diagnosis.recommendations}
          onChange={(e) => setDiagnosis({ ...diagnosis, recommendations: e.target.value })}
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          multiline
          rows={4}
          required
          label="Doctor Notes"
          placeholder="Additional observations, clinical reasoning, patient education..."
          value={diagnosis.doctor_notes}
          onChange={(e) => setDiagnosis({ ...diagnosis, doctor_notes: e.target.value })}
          sx={{ mb: 2 }}
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={diagnosis.follow_up_required}
              onChange={(e) =>
                setDiagnosis({ ...diagnosis, follow_up_required: e.target.checked })
              }
            />
          }
          label="Follow-up Required"
        />

        {diagnosis.follow_up_required && (
          <Box mt={2}>
            <TextField
              fullWidth
              type="date"
              label="Follow-up Date"
              InputLabelProps={{ shrink: true }}
              value={diagnosis.follow_up_date}
              onChange={(e) => setDiagnosis({ ...diagnosis, follow_up_date: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Follow-up Reason"
              value={diagnosis.follow_up_reason}
              onChange={(e) => setDiagnosis({ ...diagnosis, follow_up_reason: e.target.value })}
            />
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Pending Tests
        </Typography>

        <FormControlLabel
          control={
            <Checkbox
              checked={pendingTests.required}
              onChange={(e) =>
                setPendingTests({ ...pendingTests, required: e.target.checked })
              }
            />
          }
          label="Tests Required (Will create follow-up session)"
        />

        {pendingTests.required && (
          <Box mt={2}>
            <Box display="flex" gap={2} mb={2}>
              <TextField
                fullWidth
                size="small"
                label="Add Test"
                value={newTest}
                onChange={(e) => setNewTest(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTest()}
              />
              <Button onClick={handleAddTest} startIcon={<Add />}>
                Add
              </Button>
            </Box>

            {pendingTests.tests_requested.map((test, index) => (
              <Paper key={index} sx={{ p: 1.5, mb: 1, bgcolor: 'grey.50' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography>{test}</Typography>
                  <IconButton size="small" color="error" onClick={() => handleRemoveTest(index)}>
                    <Delete />
                  </IconButton>
                </Box>
              </Paper>
            ))}

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Instructions to Patient"
              placeholder="Instructions for obtaining and returning with test results..."
              value={pendingTests.instructions_to_patient}
              onChange={(e) =>
                setPendingTests({ ...pendingTests, instructions_to_patient: e.target.value })
              }
              sx={{ mt: 2 }}
            />
          </Box>
        )}
      </Paper>

      <Divider sx={{ my: 3 }} />

      <Box display="flex" gap={2}>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending || !diagnosis.primary_diagnosis || !diagnosis.doctor_notes}
        >
          {saveMutation.isPending ? 'Saving...' : 'Save Diagnosis'}
        </Button>
      </Box>
    </Box>
  );
};

export default DiagnosisForm;

