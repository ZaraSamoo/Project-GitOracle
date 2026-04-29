import { AppHeader } from "@/components/app-header";
import ProfileCard from "@/components/ui/profile-card";

export default function UserProfilePage() {
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
            name="GitOracle Explorer"
            role="Learning-Focused Developer"
            email="explorer@gitoracle.dev"
            statusText="Weekly planning active"
            glowText="Optimizing your next project path"
            statusColor="bg-violet-400"
          />
        </section>
      </main>
    </div>
  );
}
