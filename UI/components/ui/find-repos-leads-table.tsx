"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, MoreHorizontal } from "lucide-react";

export interface RepoLead {
  id: string;
  name: string;
  email: string;
  source: string;
  sourceType: "organic" | "campaign";
  status: "pre-sale" | "closed" | "lost" | "closing" | "new";
  size: number;
  interest: number[];
  probability: "low" | "mid" | "high";
  lastAction: string;
  repoUrl?: string | null;
}

export function FindReposLeadsTable({ leads, title = "Repository Matches" }: { leads: RepoLead[]; title?: string }) {
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [hoveredAction, setHoveredAction] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const sortedLeads = useMemo(() => {
    const rows = [...leads];
    rows.sort((a, b) => (sortOrder === "asc" ? a.size - b.size : b.size - a.size));
    return rows;
  }, [leads, sortOrder]);

  const isSelected = (leadId: string) => selectedLeads.has(leadId);
  const isAllSelected = selectedLeads.size === sortedLeads.length && sortedLeads.length > 0;
  const isIndeterminate = selectedLeads.size > 0 && selectedLeads.size < sortedLeads.length;

  const handleLeadSelection = (leadId: string, selected: boolean) => {
    const next = new Set(selectedLeads);
    if (selected) next.add(leadId);
    else next.delete(leadId);
    setSelectedLeads(next);
  };

  const handleSelectAll = (selected: boolean) => {
    setSelectedLeads(selected ? new Set(sortedLeads.map((lead) => lead.id)) : new Set());
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
    return `$${amount}`;
  };

  const renderSparkline = (data: number[]) => {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const isUpTrend = data[data.length - 1] > data[0];
    const points = data
      .map((value, index) => {
        const x = (index / (data.length - 1 || 1)) * 60;
        const y = 20 - ((value - min) / range) * 15;
        return `${x},${y}`;
      })
      .join(" ");

    return (
      <div className="h-6 w-16">
        <svg width="60" height="20" viewBox="0 0 60 20" className="overflow-visible">
          <polyline points={points} fill="none" stroke={isUpTrend ? "#22c55e" : "#f87171"} strokeWidth="2" />
        </svg>
      </div>
    );
  };

  return (
    <div className="w-full max-w-7xl">
      <div className="mb-3 text-sm text-zinc-300">{title}</div>
      <div className="overflow-hidden rounded-2xl border border-border/50 bg-background">
        <div className="grid grid-cols-7 gap-4 border-b border-border/20 bg-muted/15 px-6 py-3 text-xs uppercase tracking-wide text-muted-foreground/70">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={isAllSelected}
              ref={(el) => {
                if (el) el.indeterminate = isIndeterminate;
              }}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="h-4 w-4"
            />
            <span>Repository</span>
          </div>
          <div>Source</div>
          <div>Status</div>
          <div>Size</div>
          <div>Interest</div>
          <div>Probability</div>
          <button className="flex items-center gap-2 text-left" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>
            Last Action <ChevronDown className={`h-4 w-4 ${sortOrder === "asc" ? "rotate-180" : ""}`} />
          </button>
        </div>

        {sortedLeads.map((lead, index) => (
          <motion.div key={lead.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.02 }}>
            <div
              className={`grid grid-cols-7 gap-4 px-6 py-2 ${index < sortedLeads.length - 1 ? "border-b border-border/20" : ""} ${isSelected(lead.id) ? "bg-blue-900/10" : "hover:bg-muted/25"}`}
              onMouseEnter={() => setHoveredAction(lead.id)}
              onMouseLeave={() => setHoveredAction(null)}
            >
              <div className="flex items-center gap-3">
                <input type="checkbox" checked={isSelected(lead.id)} onChange={(e) => handleLeadSelection(lead.id, e.target.checked)} className="h-4 w-4" />
                <div className="min-w-0">
                  {lead.repoUrl ? (
                    <a href={lead.repoUrl} target="_blank" rel="noreferrer" className="truncate font-medium text-cyan-300 hover:underline">
                      {lead.name}
                    </a>
                  ) : (
                    <div className="truncate font-medium text-foreground/90">{lead.name}</div>
                  )}
                  <div className="truncate text-xs text-muted-foreground/70">{lead.email}</div>
                </div>
              </div>
              <div className="flex items-center text-xs">{lead.source}</div>
              <div className="flex items-center text-xs uppercase">{lead.status}</div>
              <div className="flex items-center font-semibold">{formatCurrency(lead.size)}</div>
              <div className="flex items-center">{renderSparkline(lead.interest)}</div>
              <div className="flex items-center text-xs uppercase">{lead.probability}</div>
              <div className="flex items-center">
                <AnimatePresence mode="wait">
                  {hoveredAction === lead.id ? (
                    <motion.button
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      className="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-2 py-1 text-xs text-primary"
                    >
                      Engage <MoreHorizontal className="h-3 w-3" />
                    </motion.button>
                  ) : (
                    <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-xs text-muted-foreground/70">
                      {lead.lastAction}
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
