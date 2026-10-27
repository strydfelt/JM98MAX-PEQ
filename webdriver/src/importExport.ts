import {
  getDevice,
  getEqState,
  getGlobalGainState,
  renderUI,
  setEqState,
  setGlobalGainState,
} from "./fn.ts";
import { log, updateGlobalGain } from "./helpers.ts";
import type { EQ } from "./main.ts";

/**
 * Convert EQ state to text format (like PEQ files)
 */
export function eqStateToText(eqState: EQ, globalGain: number): string {
  let lines = [];
  
  // Preamp line
  lines.push(`Preamp: ${globalGain.toFixed(1)} dB`);
  
  // Filter lines
  eqState.forEach((band, index) => {
    const enabled = band.enabled ? "ON" : "OFF";
    // Map internal type to display type
    let typeStr = band.type;
    if (band.type === "PK") typeStr = "PK";
    else if (band.type === "LSQ") typeStr = "LSQ";
    else if (band.type === "HSQ") typeStr = "HSQ";
    
    lines.push(`Filter ${index + 1}: ${enabled} ${typeStr} Fc ${band.freq} Hz Gain ${band.gain.toFixed(1)} dB Q ${band.q.toFixed(3)}`);
  });
  
  return lines.join('\n');
}

/**
 * Parse text format PEQ file and update state
 */
export function textToEqState(text: string): {eqState: EQ, globalGain: number} | null {
  const lines = text.trim().split('\n');
  const eqState: EQ = [];
  let globalGain = 0;
  let foundPreampOrFilter = false;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    // Parse Preamp line
    if (trimmed.startsWith('Preamp:')) {
      const match = trimmed.match(/Preamp:\s*(-?\d+\.?\d*)\s*dB/);
      if (match) {
        globalGain = parseFloat(match[1]);
        foundPreampOrFilter = true;
      }
      continue;
    }
    
    // Parse Filter lines
    if (trimmed.startsWith('Filter')) {
      const match = trimmed.match(/Filter\s+(\d+):\s+(ON|OFF)\s+(PK|LSQ|HSQ)\s+Fc\s+(\d+)\s+Hz\s+Gain\s*(-?\d+\.?\d*)\s*dB\s+Q\s*(\d+\.?\d*)/);
      if (match) {
        const index = parseInt(match[1]) - 1; // Convert to 0-based index
        const enabled = match[2] === 'ON';
        const type = match[3] as 'PK' | 'LSQ' | 'HSQ';
        const freq = parseInt(match[4]);
        const gain = parseFloat(match[5]);
        const q = parseFloat(match[6]);
        
        // Initialize band if not exists
        if (!eqState[index]) {
          eqState[index] = {
            index: index,
            freq: freq,
            gain: gain,
            q: q,
            type: type,
            enabled: enabled
          };
        } else {
          // Update existing band
          eqState[index].enabled = enabled;
          eqState[index].type = type;
          eqState[index].freq = freq;
          eqState[index].gain = gain;
          eqState[index].q = q;
        }
        foundPreampOrFilter = true;
      }
    }
  }
  
  // If we didn't find any Preamp or Filter lines, return null to indicate invalid PEQ format
  if (!foundPreampOrFilter) {
    return null;
  }
  
  // Fill any missing bands with defaults
  while (eqState.length < 8) {
    const index = eqState.length;
    eqState.push({
      index: index,
      freq: index === 0 ? 26 : index === 1 ? 40 : index === 2 ? 120 : index === 3 ? 460 : index === 4 ? 1700 : index === 5 ? 4600 : index === 6 ? 5900 : 7800,
      gain: 0,
      q: 0.75,
      type: 'PK',
      enabled: true
    });
  }
  
  return {eqState, globalGain};
}

/**
 * Export profile to text file
 */
export async function exportProfile() {
  const device = getDevice();
  const globalGainState = getGlobalGainState();
  const eqState = getEqState();
  if (!device) return;
  
  const textContent = eqStateToText(eqState, globalGainState);
  const blob = new Blob([textContent], {
    type: "text/plain",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "eq_profile.txt";
  a.click();
}

/**
 * Import profile from file (supports both PEQ text format and legacy JSON format)
 * @param e The event object
 */
export async function importProfile(e: Event) {
  const target = e.target as HTMLInputElement;
  if (!target.files) return;
  const file = target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const text = event.target?.result as string;
      
      // Try to parse as PEQ text format first
      let result = textToEqState(text);
      
      // If PEQ parsing fails and it's a JSON file, try legacy JSON format
      if (!result && file.name.endsWith('.json')) {
        try {
          const data = JSON.parse(text);
          if (data.bands) {
            // Convert legacy JSON format to our EQ state format
            const eqState: EQ = data.bands.map((band: any, index: number) => ({
              index: band.index || index,
              freq: band.freq || (index === 0 ? 26 : index === 1 ? 40 : index === 2 ? 120 : index === 3 ? 460 : index === 4 ? 1700 : index === 5 ? 4600 : index === 6 ? 5900 : 7800),
              gain: band.gain || 0,
              q: band.q || 0.75,
              type: band.type || 'PK',
              enabled: band.enabled !== undefined ? band.enabled : true
            }));
            
            result = {
              eqState,
              globalGain: data.globalGain || 0
            };
          }
        } catch (jsonErr) {
          // JSON parsing failed, continue to PEQ parsing attempt below
        }
      }
      
      if (result && result.eqState) {
        // Update internal state
        setEqState(result.eqState);

        // Update global gain state
        setGlobalGainState(result.globalGain);

        updateGlobalGain(result.globalGain); // Update UI and send gain packet
        renderUI(result.eqState); // Update EQ UI

        log("Profile imported. Click 'SYNC' to apply.");
      } else {
        log("Error: Could not parse file format. Please ensure it's a valid PEQ (.txt) or JSON (.json) file.");
      }
    } catch (err) {
      log(`Parse Error: ${(err as Error).message}`);
    }
  };
  reader.readAsText(file);
}