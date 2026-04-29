"use client";

import {
  BookmarkCheck,
  Compass,
  Home,
  TrendingUp,
  UserRound,
} from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";
import RainingLetters from "@/components/ui/modern-animated-hero-section";
import RadialOrbitalTimeline from "@/components/ui/radial-orbital-timeline";

const timelineData = [
  {
    id: 1,
    title: "Home",
    date: "Gateway",
    content: "Overview of GitOracle and how to get project recommendations quickly.",
    category: "Overview",
    icon: Home,
    relatedIds: [2, 3],
    status: "completed" as const,
    energy: 96,
    href: "/",
  },
  {
    id: 2,
    title: "Find Projects",
    date: "Core",
    content: "Enter domain and available time to match beginner to advanced repos.",
    category: "Search",
    icon: Compass,
    relatedIds: [1, 4],
    status: "in-progress" as const,
    energy: 90,
    href: "/find-projects",
  },
  {
    id: 3,
    title: "Trending",
    date: "Explore",
    content: "See currently popular repositories filtered by your learning goals.",
    category: "Discovery",
    icon: TrendingUp,
    relatedIds: [1, 4],
    status: "completed" as const,
    energy: 84,
    href: "/trending-projects",
  },
  {
    id: 4,
    title: "Saved",
    date: "Collection",
    content: "Track repositories you want to build and revisit estimated completion time.",
    category: "Library",
    icon: BookmarkCheck,
    relatedIds: [2, 3, 5],
    status: "pending" as const,
    energy: 72,
    href: "/saved-projects",
  },
  {
    id: 5,
    title: "Profile",
    date: "Personalization",
    content: "Configure your preferred stacks, daily free hours, and current skill level.",
    category: "User",
    icon: UserRound,
    relatedIds: [4],
    status: "pending" as const,
    energy: 65,
    href: "/user-profile",
  },
];

export default function HomePage() {
  return (
    <div className="bg-black text-white">
      <AppHeader />
      <RainingLetters />
      <section className="relative mx-auto max-w-6xl px-4">
        <ContainerScroll
          titleComponent={
            <div>
              <h2 className="text-3xl md:text-5xl font-bold text-white">Build Smarter with GitOracle</h2>
              <p className="mt-4 text-zinc-300 max-w-3xl mx-auto">
                Choose your domain like C++, machine learning, or web scraping and the time you
                have. GitOracle maps you to GitHub projects with difficulty and estimated time.
              </p>
            </div>
          }
        >
          <div className="relative h-full w-full overflow-hidden bg-gradient-to-br from-fuchsia-950/40 via-violet-950/35 to-cyan-950/35 p-5 md:p-8">
            <div className="pointer-events-none absolute -left-10 top-8 h-32 w-32 rounded-full bg-fuchsia-500/30 blur-3xl md:h-44 md:w-44" />
            <div className="pointer-events-none absolute -right-10 bottom-6 h-32 w-32 rounded-full bg-cyan-500/30 blur-3xl md:h-44 md:w-44" />
            <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center rounded-2xl border border-white/15 bg-black/35 p-4 text-center backdrop-blur-sm md:p-8">
              <p className="rounded-full border border-fuchsia-300/40 bg-fuchsia-500/15 px-4 py-1 text-xs uppercase tracking-[0.24em] text-fuchsia-200">
                Built for curious builders
              </p>
              <h3 className="mt-6 text-2xl font-semibold text-white md:text-3xl">
                Pick your stack, set your free hours, and let GitOracle find the perfect repo quest.
              </h3>
              <p className="mt-4 max-w-2xl text-sm text-zinc-200 md:text-base">
                No doom-scrolling. No random bookmarks. Just fun, right-sized projects with clear
                momentum signals so you can ship something cool every week.
              </p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-2 text-xs text-zinc-200">
                {["Quick wins", "Real-world repos", "Difficulty-aware picks", "Time-smart planning"].map((chip) => (
                  <span
                    key={chip}
                    className="rounded-full border border-cyan-300/30 bg-gradient-to-r from-fuchsia-500/20 to-cyan-500/20 px-3 py-1"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </ContainerScroll>
      </section>

      <section>
        <RadialOrbitalTimeline timelineData={timelineData} />
      </section>
    </div>
  );
}
