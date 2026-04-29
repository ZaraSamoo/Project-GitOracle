import { AppHeader } from "@/components/app-header";

interface ProjectPageTemplateProps {
  title: string;
  subtitle: string;
  imageUrl: string;
}

export function ProjectPageTemplate({ title, subtitle, imageUrl }: ProjectPageTemplateProps) {
  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl md:text-5xl font-bold">{title}</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">{subtitle}</p>
        <div className="mt-8 overflow-hidden rounded-2xl border border-white/10">
          <img src={imageUrl} alt={title} className="h-[360px] w-full object-cover" />
        </div>
      </main>
    </div>
  );
}
