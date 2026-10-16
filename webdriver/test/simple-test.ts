// Simple test that only tests the conversion logic without importing DOM-dependent modules

// Copy the conversion functions directly to avoid DOM dependencies
type Band = {
  index: number;
  freq: number;
  gain: number;
  q: number;
  type: string;
  enabled: boolean;
};
type EQ = Band[];

/**
 * Convert EQ state to text format (like PEQ files)
 */
function eqStateToText(eqState: EQ, globalGain: number): string {
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
function textToEqState(text: string): {eqState: EQ, globalGain: number} | null {
  const lines = text.trim().split('\n');
  const eqState: EQ = [];
  let globalGain = 0;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    // Parse Preamp line
    if (trimmed.startsWith('Preamp:')) {
      const match = trimmed.match(/Preamp:\s*(-?\d+\.?\d*)\s*dB/);
      if (match) {
        globalGain = parseFloat(match[1]);
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
      }
    }
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

console.log("Running PEQ format tests (DOM-independent)...\n");

// Test 1: Parse the sample file
console.log("Test 1: Parsing sample PEQ file");
const samplePEQContent = `Preamp: -1.8 dB
Filter 1: ON PK Fc 26 Hz Gain -2.7 dB Q 0.500
Filter 2: ON PK Fc 40 Hz Gain 0.4 dB Q 2.000
Filter 3: ON PK Fc 120 Hz Gain -1.6 dB Q 1.500
Filter 4: ON PK Fc 460 Hz Gain 1.9 dB Q 0.900
Filter 5: ON PK Fc 1700 Hz Gain -1.9 dB Q 2.000
Filter 6: ON PK Fc 4600 Hz Gain 1.5 dB Q 1.100
Filter 7: ON PK Fc 5900 Hz Gain 1.2 dB Q 1.200
Filter 8: ON PK Fc 7800 Hz Gain -8.0 dB Q 1.600`;

const parsed = textToEqState(samplePEQContent);
if (parsed) {
  console.log("✓ Successfully parsed PEQ file");
  console.log(`  Global Gain: ${parsed.globalGain} dB`);
  console.log(`  Number of bands: ${parsed.eqState.length}`);
  
  // Show first and last band
  console.log(`  Band 1: ${parsed.eqState[0].enabled ? "ON" : "OFF"} ${parsed.eqState[0].type} Fc ${parsed.eqState[0].freq} Hz Gain ${parsed.eqState[0].gain} dB Q ${parsed.eqState[0].q}`);
  console.log(`  Band 8: ${parsed.eqState[7].enabled ? "ON" : "OFF"} ${parsed.eqState[7].type} Fc ${parsed.eqState[7].freq} Hz Gain ${parsed.eqState[7].gain} dB Q ${parsed.eqState[7].q}`);
} else {
  console.log("✗ Failed to parse PEQ file");
}

console.log("\nTest 2: Convert EQ state back to text");
if (parsed) {
  const regenerated = eqStateToText(parsed.eqState, parsed.globalGain);
  console.log("✓ Successfully generated PEQ text");
  console.log("Generated text:");
  console.log(regenerated);
  
  // Test round-trip
  console.log("\nTest 3: Round-trip conversion");
  const reparsed = textToEqState(regenerated);
  if (reparsed) {
    const gainMatch = Math.abs(reparsed.globalGain - parsed.globalGain) < 0.01;
    const bandsMatch = reparsed.eqState.every((band, index) => {
      const original = parsed.eqState[index];
      return band.freq === original.freq &&
             Math.abs(band.gain - original.gain) < 0.01 &&
             Math.abs(band.q - original.q) < 0.001 &&
             band.type === original.type &&
             band.enabled === original.enabled;
    });
    
    if (gainMatch && bandsMatch) {
      console.log("✓ Round-trip conversion successful - data preserved perfectly");
    } else {
      console.log("✗ Round-trip conversion failed - data mismatch");
      console.log(`  Global gain match: ${gainMatch} (${parsed.globalGain} -> ${reparsed.globalGain})`);
      console.log(`  Bands match: ${bandsMatch}`);
    }
  } else {
    console.log("✗ Failed to parse regenerated text");
  }
}

console.log("\nTest 4: Test with actual file");
try {
  const fs = await import("fs");
  const fileContent = fs.readFileSync("../prx-daybreak-8peq.txt", "utf8");
  const fileParsed = textToEqState(fileContent);
  if (fileParsed) {
    console.log("✓ Successfully parsed actual PEQ file");
    console.log(`  Global Gain: ${fileParsed.globalGain} dB`);
    console.log(`  Number of bands: ${fileParsed.eqState.length}`);
    
    // Test round-trip with actual file
    const fileRegenerated = eqStateToText(fileParsed.eqState, fileParsed.globalGain);
    const fileReparsed = textToEqState(fileRegenerated);
    if (fileReparsed) {
      const gainMatch = Math.abs(fileReparsed.globalGain - fileParsed.globalGain) < 0.01;
      const bandsMatch = fileReparsed.eqState.every((band, index) => {
        const original = fileParsed.eqState[index];
        return band.freq === original.freq &&
               Math.abs(band.gain - original.gain) < 0.01 &&
               Math.abs(band.q - original.q) < 0.001 &&
               band.type === original.type &&
               band.enabled === original.enabled;
      });
      
      if (gainMatch && bandsMatch) {
        console.log("✓ Actual file round-trip conversion successful");
      } else {
        console.log("✗ Actual file round-trip conversion failed");
      }
    }
  } else {
    console.log("✗ Failed to parse actual PEQ file");
  }
} catch (err) {
  console.log("✗ Error reading actual PEQ file:", err);
}

console.log("\nAll tests completed!");