import React, { useEffect, useState } from 'react';
import {
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Treemap,
} from 'recharts';
import { getPortfolioStats, PortfolioStats } from '../services/api';

const STAGE_COLORS = {
  STAGE_1: '#4caf50',
  STAGE_2: '#ff9800',
  STAGE_3: '#f44336',
};

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<PortfolioStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState('Base');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getPortfolioStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to load portfolio statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!stats) {
    return null;
  }

  const formatCurrency = (value: number) => {
    return `UGX ${(value / 1000000).toFixed(2)}M`;
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString();
  };

  // Mock data for macroeconomic forecast (would come from API in production)
  const macroForecast = [
    { year: '2021', gdp: 0.15 },
    { year: '2022', gdp: 0.20 },
    { year: '2023', gdp: 0.25 },
    { year: '2024', gdp: 0.23 },
  ];

  // Mock data for ECL by approach (would come from API in production)
  const eclByApproach = [
    { name: 'PD/LGD', value: 60, color: '#1976d2' },
    { name: 'Roll Rate', value: 20, color: '#ff9800' },
    { name: 'WARM', value: 15, color: '#4caf50' },
    { name: 'DiscountCF', value: 5, color: '#9c27b0' },
  ];

  // Prepare treemap data from stage distribution
  const treemapData = stats?.stage_distribution.map((stage) => ({
    name: stage.stage,
    size: stage.exposure,
    count: stage.count,
    color: STAGE_COLORS[stage.stage as keyof typeof STAGE_COLORS] || '#999',
  })) || [];

  return (
    <Box>
      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Card sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Instruments
            </Typography>
            <Typography variant="h4">
              {formatNumber(stats.total_instruments)}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Exposure
            </Typography>
            <Typography variant="h4">
              {formatCurrency(stats.total_exposure)}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total ECL
            </Typography>
            <Typography variant="h4">
              {formatCurrency(stats.total_ecl)}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Coverage Ratio
            </Typography>
            <Typography variant="h4">
              {stats.total_exposure > 0
                ? ((stats.total_ecl / stats.total_exposure) * 100).toFixed(2)
                : '0.00'}
              %
            </Typography>
            <Typography variant="caption" color="textSecondary">
              ECL / Outstanding Principal
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Scenario Selector and Macro Forecast */}
      <Box sx={{ display: 'flex', gap: 3, mb: 3, flexWrap: 'wrap' }}>
        <Paper sx={{ flex: '1 1 400px', p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Macroeconomic Forecast
            </Typography>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Scenario</InputLabel>
              <Select
                value={selectedScenario}
                label="Scenario"
                onChange={(e) => setSelectedScenario(e.target.value)}
              >
                <MenuItem value="Base">Base</MenuItem>
                <MenuItem value="Upside">Upside</MenuItem>
                <MenuItem value="Downside">Downside</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={macroForecast}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis tickFormatter={(value: any) => `${(value * 100).toFixed(0)}%`} />
              <Tooltip formatter={(value: any) => `${(Number(value) * 100).toFixed(2)}%`} />
              <Legend />
              <Line
                type="monotone"
                dataKey="gdp"
                stroke="#4caf50"
                strokeWidth={2}
                name="GDP Growth"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Paper>

        <Paper sx={{ flex: '1 1 400px', p: 2 }}>
          <Typography variant="h6" gutterBottom>
            ECL by Calculation Approach
          </Typography>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={eclByApproach}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={(entry: any) => `${entry.name}: ${entry.value}%`}
              >
                {eclByApproach.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => `${value}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      {/* Portfolio Composition Treemap */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Portfolio Composition (Treemap)
        </Typography>
        <ResponsiveContainer width="100%" height={300}>
          <Treemap
            data={treemapData}
            dataKey="size"
            aspectRatio={4 / 3}
            stroke="#fff"
            fill="#8884d8"
            content={({ x, y, width, height, name, size, count, color }: any) => {
              return (
                <g>
                  <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    style={{
                      fill: color,
                      stroke: '#fff',
                      strokeWidth: 2,
                    }}
                  />
                  {width > 80 && height > 40 && (
                    <>
                      <text
                        x={x + width / 2}
                        y={y + height / 2 - 10}
                        textAnchor="middle"
                        fill="#fff"
                        fontSize={14}
                        fontWeight="bold"
                      >
                        {name}
                      </text>
                      <text
                        x={x + width / 2}
                        y={y + height / 2 + 10}
                        textAnchor="middle"
                        fill="#fff"
                        fontSize={12}
                      >
                        {formatCurrency(size)}
                      </text>
                      <text
                        x={x + width / 2}
                        y={y + height / 2 + 25}
                        textAnchor="middle"
                        fill="#fff"
                        fontSize={10}
                      >
                        {count} instruments
                      </text>
                    </>
                  )}
                </g>
              );
            }}
          />
        </ResponsiveContainer>
      </Paper>

      {/* Charts */}
      <Box sx={{ display: 'flex', gap: 3, mb: 3, flexWrap: 'wrap' }}>
        <Paper sx={{ flex: '1 1 400px', p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Stage Distribution (Count)
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.stage_distribution}
                dataKey="count"
                nameKey="stage"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry: any) => `${entry.stage}: ${entry.count}`}
              >
                {stats.stage_distribution.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={STAGE_COLORS[entry.stage as keyof typeof STAGE_COLORS] || '#999'}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Paper>

        <Paper sx={{ flex: '1 1 400px', p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Stage Distribution (Exposure)
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.stage_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stage" />
              <YAxis tickFormatter={(value: any) => `${(value / 1000000).toFixed(0)}M`} />
              <Tooltip formatter={(value: any) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="exposure" fill="#1976d2" name="Exposure (UGX)" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      {/* Stage Details Table */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Stage Details
        </Typography>
        <Box sx={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>Stage</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Count</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Exposure</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>% of Total</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Avg Exposure</th>
              </tr>
            </thead>
            <tbody>
              {stats.stage_distribution.map((stage) => (
                <tr key={stage.stage} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px' }}>
                    <Box
                      component="span"
                      sx={{
                        display: 'inline-block',
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor:
                          STAGE_COLORS[stage.stage as keyof typeof STAGE_COLORS] || '#999',
                        marginRight: 1,
                      }}
                    />
                    {stage.stage}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatNumber(stage.count)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatCurrency(stage.exposure)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {((stage.exposure / stats.total_exposure) * 100).toFixed(2)}%
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatCurrency(stage.exposure / stage.count)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Box>
      </Paper>
    </Box>
  );
};

export default Dashboard;
