"use client";

import React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { ArrowUp, BrainCog, FolderCode, Globe, Mic, Paperclip, Square, StopCircle, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface PromptInputBoxProps {
  onSend?: (message: string, files?: File[]) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export const PromptInputBox = React.forwardRef<HTMLDivElement, PromptInputBoxProps>(
  ({ onSend = () => {}, isLoading = false, placeholder = "Describe your ideal repo...", className }, ref) => {
    const [input, setInput] = React.useState("");
    const [files, setFiles] = React.useState<File[]>([]);
    const [filePreview, setFilePreview] = React.useState<string | null>(null);
    const [isRecording, setIsRecording] = React.useState(false);
    const [showSearch, setShowSearch] = React.useState(false);
    const [showThink, setShowThink] = React.useState(false);
    const [showCanvas, setShowCanvas] = React.useState(false);
    const uploadInputRef = React.useRef<HTMLInputElement>(null);

    const processFile = (file: File) => {
      if (!file.type.startsWith("image/")) return;
      if (file.size > 10 * 1024 * 1024) return;
      setFiles([file]);
      const reader = new FileReader();
      reader.onload = (event) => setFilePreview((event.target?.result as string) || null);
      reader.readAsDataURL(file);
    };

    const submit = () => {
      if (!input.trim() && files.length === 0) return;
      let prefix = "";
      if (showSearch) prefix = "[Search] ";
      else if (showThink) prefix = "[Think] ";
      else if (showCanvas) prefix = "[Canvas] ";
      onSend(`${prefix}${input}`.trim(), files);
      setInput("");
      setFiles([]);
      setFilePreview(null);
    };

    const hasContent = input.trim().length > 0 || files.length > 0;

    return (
      <TooltipPrimitive.Provider delayDuration={120}>
        <div
          ref={ref}
          className={cn(
            "w-full rounded-3xl border border-cyan-300/30 bg-zinc-950/85 p-3 shadow-[0_10px_40px_rgba(0,0,0,0.45)] backdrop-blur-sm",
            className
          )}
        >
          {filePreview && (
            <div className="mb-2">
              <div className="relative h-16 w-16 overflow-hidden rounded-xl">
                <img src={filePreview} alt="preview" className="h-full w-full object-cover" />
                <button
                  type="button"
                  className="absolute right-1 top-1 rounded-full bg-black/70 p-0.5"
                  onClick={() => {
                    setFiles([]);
                    setFilePreview(null);
                  }}
                >
                  <X className="h-3 w-3 text-white" />
                </button>
              </div>
            </div>
          )}

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={
              showSearch ? "Search GitHub trends..." : showThink ? "Think through constraints..." : showCanvas ? "Draft in canvas mode..." : placeholder
            }
            className="min-h-[46px] w-full resize-none rounded-xl bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-zinc-500"
            disabled={isLoading}
          />

          <div className="mt-2 flex items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              <Action tooltip="Upload image">
                <button
                  type="button"
                  onClick={() => uploadInputRef.current?.click()}
                  className="flex h-8 w-8 items-center justify-center rounded-full text-zinc-400 transition hover:bg-white/10 hover:text-zinc-100"
                >
                  <Paperclip className="h-4 w-4" />
                </button>
              </Action>
              <input
                ref={uploadInputRef}
                type="file"
                className="hidden"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) processFile(file);
                  e.currentTarget.value = "";
                }}
              />

              <ToggleButton
                active={showSearch}
                icon={<Globe className="h-4 w-4" />}
                label="Search"
                colorClass="text-cyan-300 border-cyan-300/60 bg-cyan-500/10"
                onClick={() => {
                  setShowSearch((v) => !v);
                  setShowThink(false);
                }}
              />
              <ToggleButton
                active={showThink}
                icon={<BrainCog className="h-4 w-4" />}
                label="Think"
                colorClass="text-violet-300 border-violet-300/60 bg-violet-500/10"
                onClick={() => {
                  setShowThink((v) => !v);
                  setShowSearch(false);
                }}
              />
              <ToggleButton
                active={showCanvas}
                icon={<FolderCode className="h-4 w-4" />}
                label="Canvas"
                colorClass="text-orange-300 border-orange-300/60 bg-orange-500/10"
                onClick={() => setShowCanvas((v) => !v)}
              />
            </div>

            <Action tooltip={isLoading ? "Stop" : isRecording ? "Stop recording" : hasContent ? "Send" : "Record"}>
              <button
                type="button"
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full transition",
                  isRecording
                    ? "bg-rose-500/15 text-rose-300"
                    : hasContent
                    ? "bg-white text-black hover:bg-zinc-200"
                    : "text-zinc-400 hover:bg-white/10 hover:text-zinc-100"
                )}
                onClick={() => {
                  if (isLoading) return;
                  if (isRecording) {
                    setIsRecording(false);
                    onSend("[Voice message]", []);
                    return;
                  }
                  if (hasContent) {
                    submit();
                    return;
                  }
                  setIsRecording(true);
                }}
              >
                {isLoading ? (
                  <Square className="h-3.5 w-3.5 fill-current" />
                ) : isRecording ? (
                  <StopCircle className="h-4.5 w-4.5" />
                ) : hasContent ? (
                  <ArrowUp className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </button>
            </Action>
          </div>

          <AnimatePresence>
            {isRecording && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 36 }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-2 flex items-center gap-1 overflow-hidden"
              >
                {Array.from({ length: 24 }).map((_, i) => (
                  <span
                    key={i}
                    className="h-full w-0.5 animate-pulse rounded-full bg-rose-300/70"
                    style={{ animationDelay: `${i * 0.03}s`, height: `${12 + ((i * 7) % 20)}px` }}
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </TooltipPrimitive.Provider>
    );
  }
);

PromptInputBox.displayName = "PromptInputBox";

function Action({ tooltip, children }: { tooltip: string; children: React.ReactNode }) {
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          sideOffset={5}
          className="z-50 rounded-md border border-white/10 bg-zinc-900 px-2 py-1 text-xs text-white shadow-xl"
        >
          {tooltip}
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}

function ToggleButton({
  active,
  icon,
  label,
  onClick,
  colorClass,
}: {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  colorClass: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-8 items-center gap-1 rounded-full border px-2 text-xs transition",
        active ? colorClass : "border-transparent text-zinc-400 hover:text-zinc-100"
      )}
    >
      <motion.span animate={{ rotate: active ? 360 : 0 }} transition={{ type: "spring", stiffness: 240, damping: 20 }}>
        {icon}
      </motion.span>
      <AnimatePresence>
        {active && (
          <motion.span
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "auto", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="overflow-hidden whitespace-nowrap"
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
