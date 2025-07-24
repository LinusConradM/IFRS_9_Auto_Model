// frontend/src/App.tsx
import React from 'react';

import React from 'react';
import UploadInstruments from './components/UploadInstruments';
import InstrumentsTable from './components/InstrumentsTable';

function App() {
  return (
    <div style={{ padding: '16px' }}>
      <h1>IFRS 9 Automation Platform</h1>
      <UploadInstruments />
      <InstrumentsTable />
    </div>
  );
}

export default App;

