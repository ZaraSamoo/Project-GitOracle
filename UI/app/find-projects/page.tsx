import { AppHeader } from "@/components/app-header";
import { PromptInputBox } from "@/components/ui/ai-prompt-box";

export default function FindProjectsPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-bold md:text-5xl">Find Projects</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          Describe your domain and free hours, then generate project prompts tailored to your
          learning path and current skill level.
        </p>

        <section className="mt-8 rounded-3xl border border-white/10 bg-gradient-to-br from-zinc-950 via-violet-950/20 to-cyan-950/20 p-5 md:p-8">
          <div className="mx-auto max-w-3xl">
            <PromptInputBox
              placeholder="Example: I have 6 hours this week and want a Python data project with clear milestones."
              onSend={(message, files) => {
                console.log("Find Projects prompt:", message, files);
              }}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
