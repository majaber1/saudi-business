import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  {
    // Client hydration reads localStorage after mount; these guarded state
    // updates are intentional and do not create an effect dependency loop.
    rules: { "react-hooks/set-state-in-effect": "off" },
  },
  globalIgnores([".next/**", "next-env.d.ts"]),
]);
