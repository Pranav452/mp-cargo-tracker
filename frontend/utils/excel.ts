import * as XLSX from 'xlsx';

export const parseExcel = (file: File): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        const workbook = XLSX.read(data, { type: 'binary' });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];

        // Check if it's a CSV without headers (common cargo format)
        const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
        const firstRow = XLSX.utils.sheet_to_json(sheet, { header: 1, range: { s: { r: 0, c: 0 }, e: { r: 0, c: range.e.c } } })[0];

        let jsonData;
        if (firstRow && firstRow.length >= 3 && typeof firstRow[0] === 'string' && firstRow[0].length >= 10) {
          // Looks like headerless CSV (container numbers are long)
          // Create default headers for cargo data: Container,Vessel,Carrier,ETD,ETA,Destination,ATA
          const headers = ['Container', 'Vessel', 'Carrier', 'ETD', 'ETA', 'Destination', 'ATA'];
          jsonData = XLSX.utils.sheet_to_json(sheet, { header: headers });
        } else {
          // Normal Excel with headers
          jsonData = XLSX.utils.sheet_to_json(sheet);
        }

        resolve(jsonData);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = reject;
    reader.readAsBinaryString(file);
  });
};

// Helper to normalize keys (e.g., "E.T.A" -> "eta")
export const normalizeKeys = (row: any) => {
  const newRow: any = {};

  // First try to map known column names
  Object.keys(row).forEach((key) => {
    const lower = key.toLowerCase().trim();
    if (lower.includes('container') || lower.includes('awb') || lower.includes('tracking') || key === 'Container') {
      newRow.trackingNumber = row[key];
    }
    else if (lower.includes('carrier') || lower.includes('shipping line') || lower.includes('airline') || key === 'Carrier') {
      newRow.carrier = row[key];
    }
    else if (lower.includes('eta') || lower.includes('arrival') || key === 'ETA') {
      newRow.systemEta = row[key];
    }
    else {
      newRow[key] = row[key]; // Keep other columns
    }
  });

  // If we don't have trackingNumber but row has data, try to infer from position
  if (!newRow.trackingNumber && Object.keys(row).length >= 1) {
    const values = Object.values(row);
    if (values[0] && typeof values[0] === 'string' && values[0].length >= 10) {
      newRow.trackingNumber = values[0]; // First column is likely container
    }
    if (values[2] && typeof values[2] === 'string') {
      newRow.carrier = values[2]; // Third column is likely carrier
    }
    if (values[4] && typeof values[4] === 'string') {
      newRow.systemEta = values[4]; // Fifth column is likely ETA
    }
  }

  return newRow;
};
