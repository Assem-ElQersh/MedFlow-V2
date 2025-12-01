import React, { useState } from 'react';
import {
  Box,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
  Chip,
} from '@mui/material';
import { CloudUpload, Delete, InsertDriveFile } from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionService } from '../services/sessionService';
import { FileType, UploadedFile } from '../types/session';

interface FileUploadProps {
  sessionId: string;
  files: UploadedFile[];
  canDelete: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ sessionId, files, canDelete }) => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<FileType>('other');

  const uploadMutation = useMutation({
    mutationFn: ({ file, type }: { file: File; type: FileType }) =>
      sessionService.uploadFile(sessionId, file, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] });
      setSelectedFile(null);
      setFileType('other');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => sessionService.deleteFile(sessionId, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] });
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate({ file: selectedFile, type: fileType });
    }
  };

  const handleDownload = async (file: UploadedFile) => {
    try {
      const url = await sessionService.getFileUrl(sessionId, file.file_id);
      window.open(url, '_blank');
    } catch (error) {
      console.error('Failed to get file URL:', error);
    }
  };

  const formatFileSize = (sizeMb: number): string => {
    if (sizeMb < 1) {
      return `${Math.round(sizeMb * 1024)} KB`;
    }
    return `${sizeMb.toFixed(2)} MB`;
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Upload Medical Files
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Upload X-rays, CT scans, lab results, ECG, or other medical reports
        </Typography>

        <Box display="flex" gap={2} mt={2} alignItems="flex-end">
          <Button
            variant="outlined"
            component="label"
            startIcon={<CloudUpload />}
            disabled={!canDelete}
          >
            Choose File
            <input type="file" hidden onChange={handleFileSelect} />
          </Button>

          {selectedFile && (
            <>
              <Box flex={1}>
                <Typography variant="body2" gutterBottom>
                  {selectedFile.name} ({formatFileSize(selectedFile.size / (1024 * 1024))})
                </Typography>
                <FormControl fullWidth size="small">
                  <InputLabel>File Type</InputLabel>
                  <Select
                    value={fileType}
                    label="File Type"
                    onChange={(e) => setFileType(e.target.value as FileType)}
                  >
                    <MenuItem value="xray">X-Ray</MenuItem>
                    <MenuItem value="ct">CT Scan</MenuItem>
                    <MenuItem value="lab_result">Lab Result</MenuItem>
                    <MenuItem value="ecg">ECG</MenuItem>
                    <MenuItem value="report">Report</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
              </Button>
            </>
          )}
        </Box>

        {uploadMutation.isPending && <LinearProgress sx={{ mt: 2 }} />}
      </Paper>

      {files.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Uploaded Files ({files.length})
          </Typography>
          <List>
            {files.map((file) => (
              <ListItem
                key={file.file_id}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                }}
                onClick={() => handleDownload(file)}
              >
                <InsertDriveFile sx={{ mr: 2, color: 'primary.main' }} />
                <ListItemText
                  primary={file.file_name}
                  secondary={
                    <Box display="flex" gap={1} alignItems="center" mt={0.5}>
                      <Chip
                        label={file.file_type.toUpperCase()}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(file.file_size_mb)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        • {new Date(file.upload_timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                />
                {canDelete && file.can_delete && (
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm('Delete this file?')) {
                          deleteMutation.mutate(file.file_id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                )}
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default FileUpload;

