import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { PersonAdd } from '@mui/icons-material';

const UserManagement: React.FC = () => {
  const [openDialog, setOpenDialog] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    role: 'nurse',
  });

  const mockUsers = [
    { user_id: 'A-00001', username: 'admin', full_name: 'System Administrator', role: 'admin', is_active: true },
    { user_id: 'D-00001', username: 'doctor1', full_name: 'Dr. Sarah Johnson', role: 'doctor', is_active: true },
    { user_id: 'N-00001', username: 'nurse1', full_name: 'Fatma Hassan', role: 'nurse', is_active: true },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<PersonAdd />}
          onClick={() => setOpenDialog(true)}
        >
          Add User
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        This is a placeholder for admin features. In production, implement full user CRUD operations.
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User ID</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Full Name</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockUsers.map((user) => (
              <TableRow key={user.user_id}>
                <TableCell>{user.user_id}</TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.full_name}</TableCell>
                <TableCell>
                  <Chip
                    label={user.role}
                    size="small"
                    color={
                      user.role === 'admin'
                        ? 'error'
                        : user.role === 'doctor'
                        ? 'primary'
                        : 'default'
                    }
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    size="small"
                    color={user.is_active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <Button size="small">Edit</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add User Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New User</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Username"
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              type="password"
              label="Password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Full Name"
              value={newUser.full_name}
              onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              type="email"
              label="Email"
              value={newUser.email}
              onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                value={newUser.role}
                label="Role"
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              >
                <MenuItem value="nurse">Nurse</MenuItem>
                <MenuItem value="doctor">Doctor</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" disabled>
            Add User (Not Implemented)
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;

