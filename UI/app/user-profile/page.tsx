"use client";

import Link from "next/link";
import { AppHeader } from "@/components/app-header";
import ProfileCard from "@/components/ui/profile-card";
import { getSessionEmail, getSessionUserId, getSessionUsername } from "@/lib/auth-session";

export default function UserProfilePage() {
  const userId = getSessionUserId();
  const username = getSessionUsername();
  const email = getSessionEmail();

  if (!userId || !username || !email) {
    return (
      <div className="min-h-screen bg-black text-white">
        <AppHeader />
        <main className="mx-auto flex max-w-3xl flex-col items-center justify-center px-4 py-20 text-center">
          <h1 className="text-2xl font-semibold md:text-3xl">Sign up first</h1>
          <p className="mt-2 text-sm text-zinc-400">Create an account to unlock your profile.</p>
          <Link href="/create-account" className="mt-6 rounded-full border border-white/20 px-5 py-2 text-sm hover:bg-white/10">
            Create Account
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-bold md:text-5xl">Your Profile</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          Tune your learning profile so GitOracle can recommend repositories that match your skill,
          available hours, and current momentum.
        </p>

        <section className="mt-10 flex justify-center">
          <ProfileCard
            name={username}
            role="Learning-Focused Developer"
            email={email}
            statusText="Weekly planning active"
            glowText="Optimizing your next project path"
            statusColor="bg-violet-400"
          />
        </section>
      </main>
    </div>
  );
}
