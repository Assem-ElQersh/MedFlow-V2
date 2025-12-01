import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Divider,
  Alert,
} from '@mui/material';
import { Add, Delete, ArrowBack } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { patientService } from '../../services/patientService';
import { PatientCreateRequest, Medication, SurgicalProcedure } from '../../types/patient';

const PatientForm: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<PatientCreateRequest>({
    name: '',
    national_id: '',
    date_of_birth: '',
    phone_primary: '',
    phone_secondary: '',
    email: '',
    address: '',
    sex: 'male',
    chronic_diseases: [],
    allergies: [],
    current_medications: [],
    surgical_history: [],
    smoking_status: 'unknown',
  });

  const [newDisease, setNewDisease] = useState('');
  const [newAllergy, setNewAllergy] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: PatientCreateRequest) => patientService.createPatient(data),
    onSuccess: (data) => {
      navigate(`/patients/${data.patient_id}`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create patient');
    },
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleAddChronicDisease = () => {
    if (newDisease.trim()) {
      handleInputChange('chronic_diseases', [...formData.chronic_diseases, newDisease.trim()]);
      setNewDisease('');
    }
  };

  const handleRemoveChronicDisease = (index: number) => {
    const updated = formData.chronic_diseases.filter((_, i) => i !== index);
    handleInputChange('chronic_diseases', updated);
  };

  const handleAddAllergy = () => {
    if (newAllergy.trim()) {
      handleInputChange('allergies', [...formData.allergies, newAllergy.trim()]);
      setNewAllergy('');
    }
  };

  const handleRemoveAllergy = (index: number) => {
    const updated = formData.allergies.filter((_, i) => i !== index);
    handleInputChange('allergies', updated);
  };

  const handleAddMedication = () => {
    const newMed: Medication = {
      name: '',
      dosage: '',
      frequency: '',
      instructions: '',
    };
    handleInputChange('current_medications', [...formData.current_medications, newMed]);
  };

  const handleUpdateMedication = (index: number, field: keyof Medication, value: string) => {
    const updated = [...formData.current_medications];
    updated[index] = { ...updated[index], [field]: value };
    handleInputChange('current_medications', updated);
  };

  const handleRemoveMedication = (index: number) => {
    const updated = formData.current_medications.filter((_, i) => i !== index);
    handleInputChange('current_medications', updated);
  };

  const handleAddSurgery = () => {
    const newSurgery: SurgicalProcedure = {
      procedure: '',
      date: '',
      notes: '',
    };
    handleInputChange('surgical_history', [...formData.surgical_history, newSurgery]);
  };

  const handleUpdateSurgery = (index: number, field: keyof SurgicalProcedure, value: string) => {
    const updated = [...formData.surgical_history];
    updated[index] = { ...updated[index], [field]: value };
    handleInputChange('surgical_history', updated);
  };

  const handleRemoveSurgery = (index: number) => {
    const updated = formData.surgical_history.filter((_, i) => i !== index);
    handleInputChange('surgical_history', updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    createMutation.mutate(formData);
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/patients')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4">New Patient Registration</Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Personal Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                required
                fullWidth
                label="Full Name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                required
                fullWidth
                label="National ID"
                value={formData.national_id}
                onChange={(e) => handleInputChange('national_id', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                required
                fullWidth
                type="date"
                label="Date of Birth"
                InputLabelProps={{ shrink: true }}
                value={formData.date_of_birth}
                onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth required>
                <InputLabel>Sex</InputLabel>
                <Select
                  value={formData.sex}
                  label="Sex"
                  onChange={(e) => handleInputChange('sex', e.target.value)}
                >
                  <MenuItem value="male">Male</MenuItem>
                  <MenuItem value="female">Female</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Smoking Status</InputLabel>
                <Select
                  value={formData.smoking_status}
                  label="Smoking Status"
                  onChange={(e) => handleInputChange('smoking_status', e.target.value)}
                >
                  <MenuItem value="never">Never</MenuItem>
                  <MenuItem value="former">Former</MenuItem>
                  <MenuItem value="current">Current</MenuItem>
                  <MenuItem value="unknown">Unknown</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                required
                fullWidth
                label="Primary Phone"
                value={formData.phone_primary}
                onChange={(e) => handleInputChange('phone_primary', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Secondary Phone (Optional)"
                value={formData.phone_secondary}
                onChange={(e) => handleInputChange('phone_secondary', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="email"
                label="Email (Optional)"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Address (Optional)"
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
              />
            </Grid>
          </Grid>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Medical History
          </Typography>

          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              Chronic Diseases
            </Typography>
            <Box display="flex" gap={1} mb={1}>
              <TextField
                size="small"
                fullWidth
                label="Add Chronic Disease"
                value={newDisease}
                onChange={(e) => setNewDisease(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddChronicDisease())}
              />
              <Button onClick={handleAddChronicDisease} startIcon={<Add />}>
                Add
              </Button>
            </Box>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {formData.chronic_diseases.map((disease, index) => (
                <Chip
                  key={index}
                  label={disease}
                  onDelete={() => handleRemoveChronicDisease(index)}
                />
              ))}
            </Box>
          </Box>

          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom color="error">
              Allergies (Important!)
            </Typography>
            <Box display="flex" gap={1} mb={1}>
              <TextField
                size="small"
                fullWidth
                label="Add Allergy"
                value={newAllergy}
                onChange={(e) => setNewAllergy(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAllergy())}
              />
              <Button onClick={handleAddAllergy} startIcon={<Add />}>
                Add
              </Button>
            </Box>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {formData.allergies.map((allergy, index) => (
                <Chip
                  key={index}
                  label={allergy}
                  color="error"
                  onDelete={() => handleRemoveAllergy(index)}
                />
              ))}
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">Current Medications</Typography>
              <Button startIcon={<Add />} onClick={handleAddMedication}>
                Add Medication
              </Button>
            </Box>
            {formData.current_medications.map((med, index) => (
              <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <TextField
                      size="small"
                      fullWidth
                      label="Medication Name"
                      value={med.name}
                      onChange={(e) => handleUpdateMedication(index, 'name', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      size="small"
                      fullWidth
                      label="Dosage"
                      value={med.dosage}
                      onChange={(e) => handleUpdateMedication(index, 'dosage', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      size="small"
                      fullWidth
                      label="Frequency"
                      value={med.frequency}
                      onChange={(e) => handleUpdateMedication(index, 'frequency', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      size="small"
                      fullWidth
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

          <Divider sx={{ my: 3 }} />

          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">Surgical History</Typography>
              <Button startIcon={<Add />} onClick={handleAddSurgery}>
                Add Surgery
              </Button>
            </Box>
            {formData.surgical_history.map((surgery, index) => (
              <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      size="small"
                      fullWidth
                      label="Procedure"
                      value={surgery.procedure}
                      onChange={(e) => handleUpdateSurgery(index, 'procedure', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      size="small"
                      fullWidth
                      type="date"
                      label="Date"
                      InputLabelProps={{ shrink: true }}
                      value={surgery.date}
                      onChange={(e) => handleUpdateSurgery(index, 'date', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={5}>
                    <TextField
                      size="small"
                      fullWidth
                      label="Notes"
                      value={surgery.notes}
                      onChange={(e) => handleUpdateSurgery(index, 'notes', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={1} display="flex" alignItems="center">
                    <IconButton color="error" onClick={() => handleRemoveSurgery(index)}>
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              </Paper>
            ))}
          </Box>
        </Paper>

        <Box display="flex" gap={2}>
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating Patient...' : 'Create Patient'}
          </Button>
          <Button variant="outlined" size="large" onClick={() => navigate('/patients')}>
            Cancel
          </Button>
        </Box>
      </form>
    </Box>
  );
};

export default PatientForm;

