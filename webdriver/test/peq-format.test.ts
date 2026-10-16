/**
 * Tests for PEQ format import/export functionality
 * These tests verify that the webdriver can correctly import and export 
 * PEQ files in the format shown in prx-daybreak-8peq.txt
 */

// Import the functions we want to test
import { eqStateToText, textToEqState } from "../src/importExport.ts";

describe("PEQ Format Conversion", () => {
  const samplePEQContent = `Preamp: -1.8 dB
Filter 1: ON PK Fc 26 Hz Gain -2.7 dB Q 0.500
Filter 2: ON PK Fc 40 Hz Gain 0.4 dB Q 2.000
Filter 3: ON PK Fc 120 Hz Gain -1.6 dB Q 1.500
Filter 4: ON PK Fc 460 Hz Gain 1.9 dB Q 0.900
Filter 5: ON PK Fc 1700 Hz Gain -1.9 dB Q 2.000
Filter 6: ON PK Fc 4600 Hz Gain 1.5 dB Q 1.100
Filter 7: ON PK Fc 5900 Hz Gain 1.2 dB Q 1.200
Filter 8: ON PK Fc 7800 Hz Gain -8.0 dB Q 1.600`;

  test("textToEqState correctly parses PEQ format", () => {
    const result = textToEqState(samplePEQContent);
    
    expect(result).not.toBeNull();
    if (result) {
      // Check global gain
      expect(result.globalGain).toBeCloseTo(-1.8, 1);
      
      // Check that we have 8 bands
      expect(result.eqState).toHaveLength(8);
      
      // Check first band
      expect(result.eqState[0]).toMatchObject({
        index: 0,
        freq: 26,
        gain: -2.7,
        q: 0.5,
        type: "PK",
        enabled: true
      });
      
      // Check second band
      expect(result.eqState[1]).toMatchObject({
        index: 1,
        freq: 40,
        gain: 0.4,
        q: 2.0,
        type: "PK",
        enabled: true
      });
      
      // Check last band
      expect(result.eqState[7]).toMatchObject({
        index: 7,
        freq: 7800,
        gain: -8.0,
        q: 1.6,
        type: "PK",
        enabled: true
      });
    }
  });

  test("eqStateToText generates correct PEQ format", () => {
    // Create the expected EQ state from the sample
    const eqState = [
      { index: 0, freq: 26, gain: -2.7, q: 0.5, type: "PK", enabled: true },
      { index: 1, freq: 40, gain: 0.4, q: 2.0, type: "PK", enabled: true },
      { index: 2, freq: 120, gain: -1.6, q: 1.5, type: "PK", enabled: true },
      { index: 3, freq: 460, gain: 1.9, q: 0.9, type: "PK", enabled: true },
      { index: 4, freq: 1700, gain: -1.9, q: 2.0, type: "PK", enabled: true },
      { index: 5, freq: 4600, gain: 1.5, q: 1.1, type: "PK", enabled: true },
      { index: 6, freq: 5900, gain: 1.2, q: 1.2, type: "PK", enabled: true },
      { index: 7, freq: 7800, gain: -8.0, q: 1.6, type: "PK", enabled: true }
    ];
    const globalGain = -1.8;
    
    const result = eqStateToText(eqState, globalGain);
    
    // Check that it contains the expected lines
    expect(result).toContain("Preamp: -1.8 dB");
    expect(result).toContain("Filter 1: ON PK Fc 26 Hz Gain -2.7 dB Q 0.500");
    expect(result).toContain("Filter 2: ON PK Fc 40 Hz Gain 0.4 dB Q 2.000");
    expect(result).toContain("Filter 3: ON PK Fc 120 Hz Gain -1.6 dB Q 1.500");
    expect(result).toContain("Filter 4: ON PK Fc 460 Hz Gain 1.9 dB Q 0.900");
    expect(result).toContain("Filter 5: ON PK Fc 1700 Hz Gain -1.9 dB Q 2.000");
    expect(result).toContain("Filter 6: ON PK Fc 4600 Hz Gain 1.5 dB Q 1.100");
    expect(result).toContain("Filter 7: ON PK Fc 5900 Hz Gain 1.2 dB Q 1.200");
    expect(result).toContain("Filter 8: ON PK Fc 7800 Hz Gain -8.0 dB Q 1.600");
  });

  test("round-trip conversion preserves data", () => {
    // Parse the sample
    const parsed = textToEqState(samplePEQContent);
    expect(parsed).not.toBeNull();
    
    if (parsed) {
      // Convert back to text
      const regenerated = eqStateToText(parsed.eqState, parsed.globalGain);
      
      // Parse again
      const reparsed = textToEqState(regenerated);
      expect(reparsed).not.toBeNull();
      
      if (reparsed) {
        // Check that values match
        expect(reparsed.globalGain).toBeCloseTo(parsed.globalGain, 1);
        expect(reparsed.eqState).toHaveLength(parsed.eqState.length);
        
        // Check each band
        parsed.eqState.forEach((original, index) => {
          const regeneratedBand = reparsed.eqState[index];
          expect(regeneratedBand.freq).toBe(original.freq);
          expect(regeneratedBand.gain).toBeCloseTo(original.gain, 1);
          expect(regeneratedBand.q).toBeCloseTo(original.q, 3);
          expect(regeneratedBand.type).toBe(original.type);
          expect(regeneratedBand.enabled).toBe(original.enabled);
        });
      }
    }
  });

  test("handles various filter types", () => {
    const mixedContent = `Preamp: 0.0 dB
Filter 1: ON PK Fc 100 Hz Gain 0.0 dB Q 0.700
Filter 2: ON LSQ Fc 200 Hz Gain 2.0 dB Q 0.700
Filter 3: ON HSQ Fc 8000 Hz Gain -3.0 dB Q 0.700
Filter 4: OFF PK Fc 1000 Hz Gain 0.0 dB Q 0.700`;
    
    const result = textToEqState(mixedContent);
    expect(result).not.toBeNull();
    
    if (result) {
      expect(result.globalGain).toBeCloseTo(0.0, 1);
      expect(result.eqState[0].type).toBe("PK");
      expect(result.eqState[0].enabled).toBe(true);
      expect(result.eqState[1].type).toBe("LSQ");
      expect(result.eqState[1].enabled).toBe(true);
      expect(result.eqState[2].type).toBe("HSQ");
      expect(result.eqState[2].enabled).toBe(true);
      expect(result.eqState[3].type).toBe("PK");
      expect(result.eqState[3].enabled).toBe(false);
    }
  });
});