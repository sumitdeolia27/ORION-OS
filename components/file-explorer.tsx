"use client"

import { useState } from "react"
import {
  Folder,
  File,
  FileText,
  ImageIcon,
  Music,
  Video,
  Code,
  ChevronRight,
  ChevronDown,
  Search,
  Grid,
  List,
  FolderOpen,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

interface FileItem {
  id: string
  name: string
  type: "folder" | "file"
  extension?: string
  size?: string
  children?: FileItem[]
  expanded?: boolean
}

const getFileIcon = (extension?: string) => {
  switch (extension) {
    case "jpg":
    case "png":
    case "gif":
      return ImageIcon
    case "mp3":
    case "wav":
      return Music
    case "mp4":
    case "mov":
      return Video
    case "js":
    case "ts":
    case "py":
      return Code
    case "txt":
    case "md":
      return FileText
    default:
      return File
  }
}

export function FileExplorer() {
  const [files, setFiles] = useState<FileItem[]>([
    {
      id: "1",
      name: "Documents",
      type: "folder",
      expanded: true,
      children: [
        { id: "1a", name: "project_notes.md", type: "file", extension: "md", size: "12 KB" },
        { id: "1b", name: "config.json", type: "file", extension: "json", size: "2 KB" },
      ],
    },
    {
      id: "2",
      name: "Media",
      type: "folder",
      expanded: false,
      children: [
        { id: "2a", name: "screenshot.png", type: "file", extension: "png", size: "245 KB" },
        { id: "2b", name: "recording.mp3", type: "file", extension: "mp3", size: "3.2 MB" },
      ],
    },
    {
      id: "3",
      name: "Scripts",
      type: "folder",
      expanded: false,
      children: [
        { id: "3a", name: "automation.py", type: "file", extension: "py", size: "8 KB" },
        { id: "3b", name: "utils.js", type: "file", extension: "js", size: "4 KB" },
      ],
    },
    { id: "4", name: "readme.txt", type: "file", extension: "txt", size: "1 KB" },
  ])
  const [search, setSearch] = useState("")
  const [viewMode, setViewMode] = useState<"list" | "grid">("list")

  const toggleFolder = (id: string) => {
    setFiles(files.map((f) => (f.id === id ? { ...f, expanded: !f.expanded } : f)))
  }

  const renderFileItem = (item: FileItem, depth = 0) => {
    const Icon = item.type === "folder" ? Folder : getFileIcon(item.extension)
    return (
      <div key={item.id}>
        <div
          className="flex items-center gap-3 px-4 py-2.5 rounded-xl hover:bg-slate-800/50 cursor-pointer transition-colors group"
          style={{ paddingLeft: `${16 + depth * 20}px` }}
          onClick={() => item.type === "folder" && toggleFolder(item.id)}
        >
          {item.type === "folder" && (
            <span className="text-slate-500">
              {item.expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </span>
          )}
          <Icon className={`w-4 h-4 ${item.type === "folder" ? "text-amber-400" : "text-slate-400"}`} />
          <span className="flex-1 text-white group-hover:text-violet-300 transition-colors">{item.name}</span>
          {item.size && <span className="text-xs text-slate-500">{item.size}</span>}
        </div>
        {item.type === "folder" && item.expanded && item.children?.map((child) => renderFileItem(child, depth + 1))}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-fuchsia-400" />
            File Explorer
          </h2>
          <p className="text-sm text-slate-400 mt-1">Browse system files</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setViewMode("list")}
            className={`rounded-xl ${viewMode === "list" ? "bg-violet-500/20 text-violet-400" : "text-slate-500"}`}
          >
            <List className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setViewMode("grid")}
            className={`rounded-xl ${viewMode === "grid" ? "bg-violet-500/20 text-violet-400" : "text-slate-500"}`}
          >
            <Grid className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search files..."
          className="pl-11 bg-slate-900/50 border-violet-500/30 focus:border-violet-500/60 text-white placeholder:text-slate-500"
        />
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-1">{files.map((f) => renderFileItem(f))}</div>
      </ScrollArea>
    </div>
  )
}
