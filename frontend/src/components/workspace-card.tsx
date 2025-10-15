import { Clock, ExternalLink, Github, Globe, Layers3, Star, User } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export type Workspace = {
  slug: string
  name: string
  description: string
  registryUrl: string
  author: string
  stars: number
  categories: string[]
  architectures: string[]
  dockerImage?: string
  tags: string[]
  repository: string
  lastCommit?: string | null
  lastCommitTimestamp: number
  rawWorkspaces: Array<Record<string, unknown>>
}

type WorkspaceCardProps = {
  workspace: Workspace
  onViewDetails?: (workspace: Workspace) => void
}

export function WorkspaceCard({ workspace, onViewDetails }: WorkspaceCardProps) {
  const updatedLabel = formatRelativeUpdated(workspace.lastCommitTimestamp)
  return (
    <Card className="flex h-full flex-col justify-between border-border/60 bg-card/80 backdrop-blur-sm transition hover:border-primary/70 hover:shadow-lg">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold text-foreground/90">
              {workspace.name}
            </CardTitle>
            <CardDescription className="line-clamp-2 text-sm">
            <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-muted-foreground/80">
              <Clock className="h-3 w-3" />
              <span>{updatedLabel}</span>
            </div>
              {workspace.description || 'No description available'}
            </CardDescription>
          </div>
          <a
            href={`https://github.com/${workspace.repository}`}
            target="_blank"
            rel="noopener noreferrer"
            className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2"
          >
            <Badge variant="outline" className="border-primary/40 text-xs text-primary transition hover:border-primary hover:text-primary">
              <Star className="mr-1 h-3 w-3" />
              {workspace.stars.toLocaleString()}
            </Badge>
          </a>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <User className="h-4 w-4 text-primary" />
          <span className="font-medium text-foreground/80">{workspace.author}</span>
        </div>
        {workspace.dockerImage ? (
          <div className="flex items-center gap-2 truncate text-xs text-muted-foreground/80">
            <Layers3 className="h-4 w-4 text-muted-foreground/70" />
            <span className="truncate">{workspace.dockerImage}</span>
          </div>
        ) : null}
        <div className="flex items-center gap-2 truncate text-xs text-muted-foreground/80">
          <Github className="h-4 w-4 text-muted-foreground/70" />
          <span className="truncate">{workspace.repository}</span>
        </div>
        <div className="flex items-center gap-2 truncate text-xs text-muted-foreground/80">
          <Globe className="h-4 w-4 text-muted-foreground/70" />
          <span className="truncate">{workspace.registryUrl}</span>
        </div>
        {workspace.categories.length ? (
          <div className="flex flex-wrap gap-1">
            {workspace.categories.slice(0, 4).map((category) => (
              <Badge
                key={`${workspace.slug}-${category}`}
                variant="outline"
                className="border-border/60 text-[10px] uppercase tracking-wide text-muted-foreground"
              >
                {category}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
      <CardFooter className="flex items-center justify-between gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="border-primary/40 text-primary hover:bg-primary/20"
          onClick={() => onViewDetails?.(workspace)}
        >
          View Details
        </Button>
        <Button
          asChild
          size="sm"
          variant="outline"
          className="border-primary/40 text-primary hover:bg-primary/20"
        >
          <a href={workspace.registryUrl} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            View Registry
          </a>
        </Button>
      </CardFooter>
    </Card>
  )
}

function formatRelativeUpdated(timestamp: number) {
  if (!Number.isFinite(timestamp) || timestamp <= 0) {
    return 'Updated recently'
  }

  const now = Date.now()
  const diffMs = Math.max(0, now - timestamp)
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const week = 7 * day
  const month = 30 * day
  const year = 365 * day

  if (diffMs < hour) {
    const minutes = Math.max(1, Math.round(diffMs / minute))
    return `Updated ${minutes} minute${minutes === 1 ? '' : 's'} ago`
  }

  if (diffMs < day) {
    const hours = Math.max(1, Math.round(diffMs / hour))
    return `Updated ${hours} hour${hours === 1 ? '' : 's'} ago`
  }

  if (diffMs < week) {
    const days = Math.max(1, Math.round(diffMs / day))
    return `Updated ${days} day${days === 1 ? '' : 's'} ago`
  }

  if (diffMs < month) {
    const weeks = Math.max(1, Math.round(diffMs / week))
    return `Updated ${weeks} week${weeks === 1 ? '' : 's'} ago`
  }

  if (diffMs < year) {
    const months = Math.max(1, Math.round(diffMs / month))
    return `Updated ${months} month${months === 1 ? '' : 's'} ago`
  }

  const years = Math.max(1, Math.round(diffMs / year))
  return `Updated ${years} year${years === 1 ? '' : 's'} ago`
}
