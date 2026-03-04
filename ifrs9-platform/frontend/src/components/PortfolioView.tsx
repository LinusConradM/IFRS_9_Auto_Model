import React, { useEffect, useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Chip,
  CircularProgress,
  Typography,
} from '@mui/material';
import { getInstruments, Instrument } from '../services/api';

const PortfolioView: React.FC = () => {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [filteredInstruments, setFilteredInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    loadInstruments();
  }, []);

  useEffect(() => {
    filterInstruments();
  }, [instruments, searchTerm, stageFilter, statusFilter]);

  const loadInstruments = async () => {
    try {
      setLoading(true);
      const data = await getInstruments();
      setInstruments(data);
    } catch (err) {
      console.error('Failed to load instruments:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterInstruments = () => {
    let filtered = [...instruments];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (i) =>
          i.instrument_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          i.customer_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Stage filter
    if (stageFilter !== 'ALL') {
      filtered = filtered.filter((i) => i.current_stage === stageFilter);
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      filtered = filtered.filter((i) => i.status === statusFilter);
    }

    setFilteredInstruments(filtered);
    setPage(0);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'STAGE_1':
        return 'success';
      case 'STAGE_2':
        return 'warning';
      case 'STAGE_3':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'success';
      case 'DERECOGNIZED':
        return 'default';
      case 'WRITTEN_OFF':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatCurrency = (value: number) => {
    return `UGX ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Filters */}
      <Box sx={{ p: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Instrument ID or Customer ID"
          sx={{ minWidth: 250 }}
        />

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Stage</InputLabel>
          <Select value={stageFilter} label="Stage" onChange={(e) => setStageFilter(e.target.value)}>
            <MenuItem value="ALL">All Stages</MenuItem>
            <MenuItem value="STAGE_1">Stage 1</MenuItem>
            <MenuItem value="STAGE_2">Stage 2</MenuItem>
            <MenuItem value="STAGE_3">Stage 3</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="ALL">All Status</MenuItem>
            <MenuItem value="ACTIVE">Active</MenuItem>
            <MenuItem value="DERECOGNIZED">Derecognized</MenuItem>
            <MenuItem value="WRITTEN_OFF">Written Off</MenuItem>
          </Select>
        </FormControl>

        <Box sx={{ flexGrow: 1 }} />

        <Typography variant="body2" sx={{ alignSelf: 'center' }}>
          Showing {filteredInstruments.length} of {instruments.length} instruments
        </Typography>
      </Box>

      {/* Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Instrument ID</TableCell>
              <TableCell>Customer ID</TableCell>
              <TableCell>Type</TableCell>
              <TableCell align="right">Principal</TableCell>
              <TableCell align="right">Interest Rate</TableCell>
              <TableCell align="right">DPD</TableCell>
              <TableCell>Stage</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Origination</TableCell>
              <TableCell>Maturity</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredInstruments
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((instrument) => (
                <TableRow key={instrument.instrument_id} hover>
                  <TableCell>{instrument.instrument_id}</TableCell>
                  <TableCell>{instrument.customer_id}</TableCell>
                  <TableCell>{instrument.instrument_type}</TableCell>
                  <TableCell align="right">{formatCurrency(instrument.principal_amount)}</TableCell>
                  <TableCell align="right">{instrument.interest_rate}%</TableCell>
                  <TableCell align="right">{instrument.days_past_due}</TableCell>
                  <TableCell>
                    <Chip
                      label={instrument.current_stage}
                      color={getStageColor(instrument.current_stage) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={instrument.status}
                      color={getStatusColor(instrument.status) as any}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{new Date(instrument.origination_date).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(instrument.maturity_date).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={filteredInstruments.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
};

export default PortfolioView;
