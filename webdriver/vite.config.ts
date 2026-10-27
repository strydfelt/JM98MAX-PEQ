import { defineConfig } from "vite";
import { existsSync, cpSync } from "fs";
import { resolve } from "path";

export default defineConfig({
	base: "./",
	build: {
		outDir: resolve(__dirname, "dist"),
		emptyOutDir: true,
	},
	plugins: [
		{
			name: "copy-to-root",
			closeBundle: () => {
				const srcDir = resolve(__dirname, "dist");
				const destDir = resolve(__dirname, "../");
				if (existsSync(srcDir)) {
					cpSync(srcDir, destDir, { recursive: true });
				}
			},
		},
	],
});
