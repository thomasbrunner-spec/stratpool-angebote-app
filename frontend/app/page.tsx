import Link from "next/link";
import { Button, Logo, Badge } from "@thomasbrunner-spec/design-system";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl w-full flex flex-col items-center gap-8 text-center">
        <Logo variant="primary-dark" height={56} />

        <Badge variant="signal">TEMPLATE</Badge>

        <h1 className="font-display text-4xl md:text-5xl font-semibold tracking-tight">
          Welcome to StratPool
        </h1>

        <p className="text-text-dim text-lg leading-relaxed max-w-lg">
          This is the app template. Once cloned and configured, it becomes
          a real app on the StratPool platform.
        </p>

        <div className="flex gap-3 mt-4">
          <Link href="/login">
            <Button variant="primary" size="lg">
              Sign in
            </Button>
          </Link>
          <a
            href="https://stratpool.pro"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="ghost" size="lg">
              Learn more
            </Button>
          </a>
        </div>
      </div>
    </main>
  );
}
