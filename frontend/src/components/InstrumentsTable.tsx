import React, { useState, useEffect } from 'react';

interface PreviewRow {
  id: number;
  row_number: number;
  raw_data: Record<string, any>;
  errors: string[] | null;
}

const InstrumentsTable: React.FC = () => {
  const [data, setData] = useState<PreviewRow[]>([]);
  const [errorFilter, setErrorFilter] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const params = errorFilter ? '?error=true' : '';
      const res = await fetch(`/instruments${params}`);
      if (res.ok) {
        const list = await res.json();
        setData(list);
      }
    };
    fetchData();
  }, [errorFilter]);

  if (data.length === 0) return null;

  return (
    <div style={{ marginTop: '32px' }}>
      <h2>Instruments Preview</h2>
      <label>
        <input
          type="checkbox"
          checked={errorFilter}
          onChange={(e) => setErrorFilter(e.target.checked)}
        />
        {' '}Show only rows with errors
      </label>
      <table style={{ marginTop: '16px', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {Object.keys(data[0].raw_data).map((key) => (
              <th key={key} style={{ border: '1px solid #ccc', padding: '4px' }}>
                {key}
              </th>
            ))}
            <th style={{ border: '1px solid #ccc', padding: '4px' }}>Errors</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.id}
              style={{ backgroundColor: row.errors?.length ? '#fdecea' : undefined }}
            >
              {Object.values(row.raw_data).map((v, i) => (
                <td key={i} style={{ border: '1px solid #ccc', padding: '4px' }}>
                  {v ?? ''}
                </td>
              ))}
              <td style={{ border: '1px solid #ccc', padding: '4px' }}>
                {row.errors?.join('; ') || ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default InstrumentsTable;