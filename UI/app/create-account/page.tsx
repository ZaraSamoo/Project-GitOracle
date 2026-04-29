"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";
import { AppHeader } from "@/components/app-header";

export default function CreateAccountPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold md:text-5xl">Create Account</h1>
          <p className="mt-3 max-w-2xl text-zinc-300">
            Create your GitOracle profile to save repositories, personalize recommendations, and
            track progress by weekly time budget.
          </p>
        </div>

        <section className="grid gap-8 lg:grid-cols-2">
          <form
            className="rounded-2xl border border-white/10 bg-zinc-950/60 p-6"
            onSubmit={(event) => {
              event.preventDefault();
              router.push("/user-profile");
            }}
          >
            <div className="space-y-4">
              <Field label="Full Name" name="name" type="text" placeholder="Jane Developer" />
              <Field label="Email" name="email" type="email" placeholder="jane@example.com" />
              <Field
                label="Password"
                name="password"
                type="password"
                placeholder="Create a secure password"
              />
              <Field
                label="Preferred Stack"
                name="stack"
                type="text"
                placeholder="e.g. Next.js, Python, Rust"
              />
            </div>

            <button
              type="submit"
              className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 font-medium text-black transition hover:bg-zinc-200"
            >
              Create Account
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <div className="rounded-2xl border border-violet-400/30 bg-gradient-to-br from-violet-500/15 via-fuchsia-500/10 to-cyan-500/15 p-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-300/40 bg-violet-500/15 px-3 py-1 text-xs uppercase tracking-wider text-violet-200">
              <Sparkles className="h-3.5 w-3.5" />
              Why create an account
            </div>
            <ul className="mt-4 space-y-3 text-sm text-zinc-100">
              <li>- Save trending repositories and build your own learning backlog.</li>
              <li>- Get recommendations based on skill, interests, and free hours.</li>
              <li>- See difficulty-aware projects instead of random GitHub browsing.</li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}

function Field({
  label,
  name,
  type,
  placeholder,
}: {
  label: string;
  name: string;
  type: string;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-zinc-300">{label}</span>
      <input
        name={name}
        type={type}
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/15 bg-black/40 px-4 py-2.5 text-sm text-white outline-none transition focus:border-violet-400/60"
      />
    </label>
  );
}
