import Link from "next/link";
import { ArrowUpRight, GitBranch } from "lucide-react";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/find-projects", label: "Find Projects" },
  { href: "/trending-projects", label: "Trending" },
  { href: "/saved-projects", label: "Saved" },
  { href: "/user-profile", label: "Profile" },
];

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 px-3 pt-3">
      <div className="mx-auto flex max-w-6xl items-center justify-between rounded-2xl border border-white/20 bg-black/35 px-4 py-3 backdrop-blur-xl shadow-[0_10px_35px_rgba(0,0,0,0.45)]">
        <Link href="/" className="flex items-center gap-2 text-white">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/30 bg-white/5">
            <GitBranch className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold tracking-wide text-white">GitOracle</span>
        </Link>

        <nav className="hidden items-center space-x-1 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-3 py-2 text-xs font-light text-white/80 transition-all duration-200 hover:bg-white/10 hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="relative flex items-center group">
          <Link
            href="/sign-in"
            className="absolute right-0 flex h-8 -translate-x-10 items-center rounded-full bg-white px-2.5 text-black transition-all duration-300 group-hover:-translate-x-16"
          >
            <ArrowUpRight className="h-3 w-3" />
          </Link>
          <Link
            href="/sign-in"
            className="z-10 flex h-8 items-center rounded-full bg-white px-6 text-xs font-normal text-black transition-all duration-300 hover:bg-white/90"
          >
            Login
          </Link>
        </div>
      </div>
    </header>
  );
}
