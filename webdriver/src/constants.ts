/**
 * CONSTANTS
 */
export const REPORT_ID = 75;
export const PACKET_SIZE = 63;
export const NUM_BANDS = 8;

// Command Codes
export const CMD = {
	PEQ: 0x09,
	VERSION: 0x0c,
	TEMP: 0x0a,
	FLASH: 0x01,
	GAIN: 0x03,
	READ: 0x80,
	WRITE: 0x01,
	END: 0x00,
};

/**
 * DEFAULT SETTINGS (Based on user request)
 */
export const DEFAULT_FREQS = [40, 100, 250, 500, 1000, 3000, 8000, 16000];
export const DEFAULT_LABELS = [
	"Sub-Bass",
	"Bass",
	"Low-Mids",
	"Mids",
	"Mids",
	"High-Mids",
	"Presence",
	"Air",
];

/**
 * Frequency ranges for automatic label detection
 * Matches PEQBand.FREQ_LABEL_RANGES in peq_configurator/src/models/peq_config.py
 * (min_freq, max_freq, label) - inclusive min, exclusive max
 */
const FREQ_LABEL_RANGES: Array<[number, number, string]> = [
	[20, 60, "Sub-Bass"],
	[60, 250, "Bass"],
	[250, 500, "Low-Mids"],
	[500, 2000, "Mids"],
	[2000, 4000, "High-Mids"],
	[4000, 6000, "Upper Mids"],
	[6000, 10000, "Presence"],
	[10000, 20000, "Air"],
];

/**
 * Get the label for a given frequency based on standard audio frequency ranges
 * @param freq Frequency in Hz
 * @returns Label string for the frequency range
 */
export function getLabelForFrequency(freq: number): string {
	for (const [minFreq, maxFreq, label] of FREQ_LABEL_RANGES) {
		if (freq >= minFreq && freq < maxFreq) {
			return label;
		}
	}
	// Handle edge case for exactly 20000 Hz
	if (freq >= 20000) return "Air";
	return `Freq ${Math.round(freq)} Hz`;
}
