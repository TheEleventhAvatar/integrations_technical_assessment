import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Paper,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    // loadedData will hold parsed JSON (array/object) or null
    const [loadedData, setLoadedData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            setIsLoading(true);
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            // keep parsed data for nicer UI rendering
            setLoadedData(data);
            setIsLoading(false);
        } catch (e) {
            setIsLoading(false);
            const detail = e?.response?.data ?? e?.message ?? JSON.stringify(e);
            alert('Load error: ' + (typeof detail === 'string' ? detail : JSON.stringify(detail)));
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                {Array.isArray(loadedData) ? (
                    <Paper sx={{ mt: 2, width: '100%', overflowX: 'auto' }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Email</TableCell>
                                    <TableCell>Phone</TableCell>
                                    <TableCell>Company</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {loadedData.map((row, idx) => (
                                    <TableRow key={row.id || idx}>
                                        <TableCell>{row.name}</TableCell>
                                        <TableCell>{row.email || ''}</TableCell>
                                        <TableCell>{row.phone || ''}</TableCell>
                                        <TableCell>{row.company || ''}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Paper>
                ) : (
                    <TextField
                        label="Loaded Data"
                        value={loadedData ? JSON.stringify(loadedData, null, 2) : ''}
                        sx={{mt: 2}}
                        InputLabelProps={{ shrink: true }}
                        disabled
                        multiline
                        minRows={6}
                    />
                )}
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    {isLoading ? 'Loading...' : 'Load Data'}
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
