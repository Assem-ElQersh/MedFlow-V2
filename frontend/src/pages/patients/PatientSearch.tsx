import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  InputAdornment,
  Chip,
} from '@mui/material';
import { Search, Add, PersonAdd } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { patientService } from '../../services/patientService';
import { PatientSearchResult } from '../../types/patient';

const PatientSearch: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['patients', 'search', debouncedQuery],
    queryFn: () => patientService.searchPatients(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
  });

  const handleRowClick = (patientId: string) => {
    navigate(`/patients/${patientId}`);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Patient Management</Typography>
        <Button
          variant="contained"
          startIcon={<PersonAdd />}
          onClick={() => navigate('/patients/new')}
        >
          New Patient
        </Button>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <TextField
          fullWidth
          label="Search Patients"
          placeholder="Enter name, phone number, or national ID"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
            endAdornment: isLoading && (
              <InputAdornment position="end">
                <CircularProgress size={20} />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      {searchQuery && searchResults && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Patient ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Age</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>National ID</TableCell>
                <TableCell>Total Sessions</TableCell>
                <TableCell>Last Visit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {searchResults.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary">No patients found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                searchResults.map((patient: PatientSearchResult) => (
                  <TableRow
                    key={patient.patient_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleRowClick(patient.patient_id)}
                  >
                    <TableCell>{patient.patient_id}</TableCell>
                    <TableCell>{patient.name}</TableCell>
                    <TableCell>{patient.age}</TableCell>
                    <TableCell>{patient.phone_primary}</TableCell>
                    <TableCell>{patient.national_id}</TableCell>
                    <TableCell>
                      <Chip label={patient.total_sessions} size="small" color="primary" />
                    </TableCell>
                    <TableCell>
                      {patient.last_session_date
                        ? new Date(patient.last_session_date).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {!searchQuery && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Search sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Search for a patient to begin
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Enter a name, phone number, or national ID in the search box above
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default PatientSearch;

