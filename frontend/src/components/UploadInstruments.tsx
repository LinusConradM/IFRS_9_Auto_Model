import React, { useState } from 'react';

interface PreviewRow {
  row_number: number;
  raw_data: Record<string, any>;
  errors: string[];
}

const UploadInstruments: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewRow[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setPreview([]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/upload_instruments', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      alert('Upload failed: ' + (await res.text()));
      return;
    }
    const data = await res.json();
    setPreview(data.preview);
  };

  return (
    <div>
      <h2>Upload Instruments</h2>
      <input type="file" accept=".csv,.xlsx" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file} style={{ marginLeft: '8px' }}>
        Upload
      </button>
      {preview.length > 0 && (
        <table style={{ marginTop: '16px', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {Object.keys(preview[0].raw_data).map((key) => (
                <th key={key} style={{ border: '1px solid #ccc', padding: '4px' }}>
                  {key}
                </th>
              ))}
              <th style={{ border: '1px solid #ccc', padding: '4px' }}>Errors</th>
            </tr>
          </thead>
          <tbody>
            {preview.map((row) => (
              <tr
                key={row.row_number}
                style={{ backgroundColor: row.errors.length > 0 ? '#fdecea' : undefined }}
              >
                {Object.values(row.raw_data).map((v, i) => (
                  <td key={i} style={{ border: '1px solid #ccc', padding: '4px' }}>
                    {v ?? ''}
                  </td>
                ))}
                <td style={{ border: '1px solid #ccc', padding: '4px' }}>
                  {row.errors.join('; ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default UploadInstruments;