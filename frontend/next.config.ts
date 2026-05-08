import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Transpile design-system package (it ships ESM)
  transpilePackages: ["@thomasbrunner-spec/design-system"],
  // For standalone Docker builds (smaller image)
  output: "standalone",
};

export default nextConfig;
