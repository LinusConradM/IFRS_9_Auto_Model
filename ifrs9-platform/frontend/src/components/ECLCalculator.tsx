import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import { calculateECL } from '../services/api';

interface ECLResult {
  calculation_id: string;
  instrument_id: string;
  ecl_amount: number;
  pd: number;
  lgd: number;
  ead: number;
  stage: string;
  reporting_date: string;
}

const ECLCalculator: React.FC = () => {
  const [instrumentId, setInstrumentId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ECLResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    if (!instrumentId.trim()) {
      setError('Please enter an instrument ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await calculateECL(instrumentId);
      setResult(data);
    } catch (err: any) {
      console.error('ECL calculation error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to calculate ECL';
      setError(errorMessage);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return `UGX ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(4)}%`;
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Calculate Expected Credit Loss (ECL)
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Enter an instrument ID to calculate its ECL based on current parameters and stage.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
          <TextField
            label="Instrument ID"
            variant="outlined"
            value={instrumentId}
            onChange={(e) => setInstrumentId(e.target.value)}
            placeholder="e.g., 1003020638002"
            sx={{ flexGrow: 1 }}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleCalculate();
              }
            }}
          />
          <Button
            variant="contained"
            onClick={handleCalculate}
            disabled={loading}
            sx={{ height: 56 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Calculate ECL'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {result && (
        <Box>
          <Alert severity="success" sx={{ mb: 3 }}>
            ECL calculation completed successfully!
          </Alert>

          <Box sx={{ display: 'flex', gap: 3, mb: 3, flexWrap: 'wrap' }}>
            <Card sx={{ flex: '1 1 300px' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  ECL Amount
                </Typography>
                <Typography variant="h4" color="primary">
                  {formatCurrency(result.ecl_amount)}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Calculation ID: {result.calculation_id}
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ flex: '1 1 300px' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Stage
                </Typography>
                <Typography variant="h4">
                  {result.stage}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Reporting Date: {new Date(result.reporting_date).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ECL Components
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, mt: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="textSecondary">
                  Probability of Default (PD)
                </Typography>
                <Typography variant="h6">
                  {formatPercentage(result.pd)}
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="textSecondary">
                  Loss Given Default (LGD)
                </Typography>
                <Typography variant="h6">
                  {formatPercentage(result.lgd)}
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="textSecondary">
                  Exposure at Default (EAD)
                </Typography>
                <Typography variant="h6">
                  {formatCurrency(result.ead)}
                </Typography>
              </Box>
            </Box>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Calculation Formula
            </Typography>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body1" component="pre" sx={{ fontFamily: 'monospace' }}>
                ECL = PD × LGD × EAD
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                = {formatPercentage(result.pd)} × {formatPercentage(result.lgd)} × {formatCurrency(result.ead)}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                = {formatCurrency(result.ecl_amount)}
              </Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
              Note: This is a simplified calculation. In production, ECL would include:
              <ul>
                <li>Time-series PD, LGD, and EAD values</li>
                <li>Discount factors for present value</li>
                <li>Multiple macroeconomic scenarios with probability weighting</li>
                <li>Forward-looking adjustments</li>
              </ul>
            </Typography>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default ECLCalculator;
