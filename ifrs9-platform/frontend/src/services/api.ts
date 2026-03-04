import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PortfolioStats {
  total_instruments: number;
  total_customers: number;
  total_exposure: number;
  total_ecl: number;
  stage_distribution: {
    stage: string;
    count: number;
    exposure: number;
  }[];
  customer_type_distribution: {
    type: string;
    count: number;
    exposure: number;
  }[];
}

export interface Instrument {
  instrument_id: string;
  customer_id: string;
  instrument_type: string;
  principal_amount: number;
  interest_rate: number;
  days_past_due: number;
  current_stage: string;
  status: string;
  origination_date: string;
  maturity_date: string;
}

export interface ECLCalculation {
  calculation_id: string;
  instrument_id: string;
  ecl_amount: number;
  pd: number;
  lgd: number;
  ead: number;
  stage: string;
  reporting_date: string;
}

// Portfolio Statistics
export const getPortfolioStats = async (): Promise<PortfolioStats> => {
  // Since we don't have a stats endpoint yet, we'll aggregate from instruments
  const response = await api.get('/instruments');
  const instruments = response.data;
  
  // Calculate stats
  const totalInstruments = instruments.length;
  const totalExposure = instruments.reduce((sum: number, i: any) => sum + parseFloat(i.principal_amount || 0), 0);
  
  // Stage distribution
  const stageMap = new Map();
  instruments.forEach((i: any) => {
    const stage = i.current_stage || 'UNKNOWN';
    if (!stageMap.has(stage)) {
      stageMap.set(stage, { count: 0, exposure: 0 });
    }
    const stats = stageMap.get(stage);
    stats.count++;
    stats.exposure += parseFloat(i.principal_amount || 0);
  });
  
  const stageDistribution = Array.from(stageMap.entries()).map(([stage, stats]) => ({
    stage,
    count: stats.count,
    exposure: stats.exposure,
  }));
  
  return {
    total_instruments: totalInstruments,
    total_customers: 0, // Would need separate endpoint
    total_exposure: totalExposure,
    total_ecl: 0, // Would need ECL calculations
    stage_distribution: stageDistribution,
    customer_type_distribution: [],
  };
};

// Get all instruments
export const getInstruments = async (params?: {
  stage?: string;
  status?: string;
  limit?: number;
}): Promise<Instrument[]> => {
  const response = await api.get('/instruments', { params });
  return response.data;
};

// Get single instrument
export const getInstrument = async (instrumentId: string): Promise<Instrument> => {
  const response = await api.get(`/instruments/${instrumentId}`);
  return response.data;
};

// Calculate ECL
export const calculateECL = async (instrumentId: string): Promise<ECLCalculation> => {
  const response = await api.post('/ecl/calculate', {
    instrument_id: instrumentId,
    reporting_date: new Date().toISOString().split('T')[0], // Today's date in YYYY-MM-DD format
  });
  return response.data;
};

// Get ECL calculations
export const getECLCalculations = async (params?: {
  instrument_id?: string;
  start_date?: string;
  end_date?: string;
}): Promise<ECLCalculation[]> => {
  const response = await api.get('/ecl/calculations', { params });
  return response.data;
};

export default api;
