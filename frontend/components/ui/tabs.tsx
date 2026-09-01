import * as React from "react";
import { cn } from "@/lib/utils";

export interface TabsProps {
  tabs: { id: string; label: string; count?: number }[];
  activeTab: string;
  onTabChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onTabChange, className }: TabsProps) {
  return (
    <div className={cn("flex space-x-1 border-b border-slate-200 pb-px overflow-x-auto no-scrollbar", className)}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 whitespace-nowrap shrink-0 transition-all duration-150",
              isActive
                ? "border-[#0052cc] text-[#0052cc]"
                : "border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300"
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-xs font-semibold",
                  isActive ? "bg-blue-50 text-[#0052cc]" : "bg-slate-100 text-slate-600"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
