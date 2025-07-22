const { useState, useEffect } = React;

function App() {
    const [file, setFile] = useState(null);
    const [instruments, setInstruments] = useState([]);

    useEffect(() => {
        fetchInstruments();
    }, []);

    const fetchInstruments = async () => {
        const res = await fetch('/instruments');
        const data = await res.json();
        setInstruments(data);
    };

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        if (res.ok) {
            const json = await res.json();
            alert(`Inserted ${json.inserted} records`);
            fetchInstruments();
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail}`);
        }
    };

    return (
        <div style={{ padding: '1rem', fontFamily: 'sans-serif' }}>
            <h1>Instrument Upload</h1>
            <input type="file" onChange={e => setFile(e.target.files[0])} />
            <button onClick={handleUpload} style={{ marginLeft: '0.5rem' }}>
                Upload
            </button>
            <h2>Instruments</h2>
            <table border="1" cellPadding="4">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>PD</th>
                        <th>LGD</th>
                        <th>EAD</th>
                        <th>Raw PD</th>
                        <th>Raw LGD</th>
                        <th>Raw EAD</th>
                    </tr>
                </thead>
                <tbody>
                    {instruments.map(instr => (
                        <tr key={instr.id}>
                            <td>{instr.id}</td>
                            <td>{instr.pd}</td>
                            <td>{instr.lgd}</td>
                            <td>{instr.ead}</td>
                            <td>{instr.raw_pd}</td>
                            <td>{instr.raw_lgd}</td>
                            <td>{instr.raw_ead}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));