"use client";
import { useState } from "react";
import { parseExcel, normalizeKeys } from "@/utils/excel";
import { UploadCloud, Play, Download, Loader2, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import * as XLSX from 'xlsx';

interface Shipment {
  id: number;
  trackingNumber: string;
  carrier: string;
  systemEta: string; // From Excel
  liveEta?: string;  // From API
  status?: string;
  summary?: string;
  loading?: boolean;
  type: "air" | "sea";
  raw?: any; // Keep original excel row data
}

export default function Dashboard() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  // 1. Handle File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const data = await parseExcel(e.target.files[0]);

    // Map Excel rows to our App Structure
    const mapped = data.map((row: any, index: number) => {
      const norm = normalizeKeys(row);

      // Normalize carrier names for API compatibility
      let carrier = norm.carrier || "Unknown";
      const carrierLower = carrier.toLowerCase().trim();

      // Map common abbreviations to full names
      if (carrierLower.includes('hapag') || carrierLower === 'hapag') carrier = 'HAPAG-LLOYD';
      else if (carrierLower.includes('cma') || carrierLower === 'cma') carrier = 'CMA CGM';
      else if (carrierLower.includes('one') || carrierLower === 'one') carrier = 'Ocean Network Express';
      else if (carrierLower.includes('msc') || carrierLower === 'msc') carrier = 'MSC';

      // Guess type based on number format (Air = XXX-XXXXXXXXX, Sea = XXXUXXXXXXXX)
      const trackingNum = norm.trackingNumber || "";
      const isAir = trackingNum.includes("-") && trackingNum.split("-")[1]?.length === 8;

      return {
        id: index,
        trackingNumber: trackingNum,
        carrier: carrier,
        systemEta: norm.systemEta || "N/A",
        type: isAir ? "air" : "sea",
        loading: false,
        raw: row
      } as Shipment;
    }).filter(s => s.trackingNumber && s.trackingNumber !== "UNKNOWN" && s.trackingNumber.length > 0); // Filter empty rows

    setShipments(mapped);
  };

  // 2. The Tracking Loop
  const startTracking = async () => {
    setIsProcessing(true);
    setProgress(0);

    let completed = 0;
    const newShipments = [...shipments];

    // Process one by one (Sequential to avoid rate limits/browser crashes)
    for (let i = 0; i < newShipments.length; i++) {
      newShipments[i].loading = true;
      setShipments([...newShipments]); // Update UI to show spinner

      try {
        const res = await fetch("http://localhost:8000/track/single", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tracking_number: newShipments[i].trackingNumber,
            carrier: newShipments[i].carrier,
            type: newShipments[i].type
          })
        });

        const data = await res.json();

        // Update the row with results
        newShipments[i].liveEta = data.live_eta;
        newShipments[i].status = data.status;
        newShipments[i].summary = data.smart_summary;
        newShipments[i].loading = false;

      } catch (error) {
        console.error("Tracking failed", error);
        newShipments[i].status = "Error";
        newShipments[i].summary = "Failed to connect to backend";
        newShipments[i].loading = false;
      }

      completed++;
      setProgress((completed / shipments.length) * 100);
      setShipments([...newShipments]); // Update UI live
    }

    setIsProcessing(false);
  };

  // 3. Export to Excel
  const exportData = () => {
    const exportRows = shipments.map(s => ({
      ...s.raw, // Original columns
      "LIVE STATUS": s.status,
      "LIVE ETA": s.liveEta,
      "SMART SUMMARY": s.summary,
      "ETA CHANGED?": s.systemEta !== s.liveEta ? "YES" : "NO"
    }));

    const ws = XLSX.utils.json_to_sheet(exportRows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Updated Tracking");
    XLSX.writeFile(wb, "MP_Cargo_Updated.xlsx");
  };

  // Helper: Status Color Logic
  const getStatusColor = (status: string | undefined) => {
    if (!status) return "bg-gray-100 text-gray-600";
    const s = status.toLowerCase();
    if (s.includes("delivered") || s.includes("arrived")) return "bg-green-100 text-green-700 border-green-200";
    if (s.includes("transit") || s.includes("departed")) return "bg-blue-100 text-blue-700 border-blue-200";
    if (s.includes("exception") || s.includes("error") || s.includes("hold")) return "bg-red-100 text-red-700 border-red-200";
    return "bg-gray-100 text-gray-700";
  };

  // Helper: ETA Comparison Color
  const getEtaColor = (system: string, live: string | undefined) => {
    if (!live || live === "N/A") return "text-gray-900";
    // Simple string comparison for demo (Ideally use date-fns)
    if (system.includes(live) || live.includes(system)) return "text-green-600 font-medium";
    return "text-red-600 font-bold"; // Dates don't match -> Alert
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">MP Cargo Smart Tracker</h1>
            <p className="text-gray-500 mt-1">Upload your daily Excel sheet to sync live ETAs.</p>
          </div>
          <div className="flex gap-3">
            {shipments.length > 0 && !isProcessing && (
              <button onClick={exportData} className="flex items-center gap-2 bg-white border border-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition">
                <Download size={16} /> Export Excel
              </button>
            )}
            {shipments.length > 0 && (
              <button
                onClick={startTracking}
                disabled={isProcessing}
                className="flex items-center gap-2 bg-black text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50 transition shadow-lg"
              >
                {isProcessing ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
                {isProcessing ? `Tracking ${Math.round(progress)}%` : "Start Tracking"}
              </button>
            )}
          </div>
        </div>

        {/* Upload Area */}
        {shipments.length === 0 && (
          <div className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center bg-white hover:bg-gray-50 transition cursor-pointer relative">
            <input type="file" accept=".xlsx,.csv" onChange={handleFileUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
            <div className="flex flex-col items-center">
              <div className="bg-blue-50 p-4 rounded-full mb-4">
                <UploadCloud className="text-blue-600" size={32} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Click to upload tracking file</h3>
              <p className="text-sm text-gray-500 mt-2">Supports .xlsx and .csv files</p>
            </div>
          </div>
        )}

        {/* Data Table */}
        {shipments.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Tracking #</th>
                    <th className="px-6 py-4">Carrier</th>
                    <th className="px-6 py-4">System ETA</th>
                    <th className="px-6 py-4">Live ETA</th>
                    <th className="px-6 py-4 w-1/3">Smart Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {shipments.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 transition">

                      {/* Status Badge */}
                      <td className="px-6 py-4">
                        {item.loading ? (
                          <Loader2 className="animate-spin text-blue-500" size={18} />
                        ) : (
                          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(item.status)}`}>
                            {item.status || "Pending"}
                          </span>
                        )}
                      </td>

                      <td className="px-6 py-4 font-medium text-gray-900">{item.trackingNumber}</td>
                      <td className="px-6 py-4 text-gray-500">{item.carrier}</td>

                      {/* System ETA */}
                      <td className="px-6 py-4 text-gray-500">{item.systemEta}</td>

                      {/* Live ETA (Color Logic) */}
                      <td className={`px-6 py-4 ${getEtaColor(item.systemEta, item.liveEta)}`}>
                        {item.liveEta || "-"}
                      </td>

                      {/* Smart Summary */}
                      <td className="px-6 py-4 text-gray-600 max-w-xs truncate" title={item.summary}>
                        {item.summary || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
