import { useEffect, useMemo, useState } from 'react'
import { Search, X } from 'lucide-react'

import type { Workspace } from '@/components/workspace-card'
import { WorkspaceCard } from '@/components/workspace-card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import rawWorkspacesData from '@/data/community_workspaces.json'
import categoriesData from '@/data/categories.json'
import { ThemeToggle } from '@/components/theme-toggle'
import backgroundImage from '@/assets/background1.jpg'
type RawWorkspacesData = Record<string, RawRepositoryEntry>

type RawRepositoryEntry = {
  github_pages?: string
  workspaces?: Array<Record<string, RawWorkspaceDefinition | undefined>>
  stars?: number
  last_commit?: string
  pushed_at?: string
}

type RawCompatibilityEntry = {
  available_tags?: string[]
  image?: string
}

type RawWorkspaceDefinition = {
  friendly_name?: string
  description?: string
  categories?: string[]
  architecture?: string[]
  compatibility?: RawCompatibilityEntry[]
  docker_registry?: string
  name?: string
}

type RawCategoryEntry =
  | string
  | {
      label?: string
      aliases?: string[]
    }

type CategoryDefinition = {
  label: string
  normalizedLabel: string
  aliases: string[]
  normalizedAliases: string[]
}

const LOAD_STEP = 24
const DEFAULT_LAST_COMMIT = '2024-01-01T00:00:00Z'

const sortFilters = [
  { label: 'Most stars', value: 'stars' }, // Sorting options
  { label: 'Most recently updated', value: 'updated' },
]

const normalizedWorkspaces = normalizeWorkspaces(
  rawWorkspacesData as unknown as RawWorkspacesData,
)

function App() {
  const workspaces = normalizedWorkspaces

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedSort, setSelectedSort] = useState<string>('stars')
  const [visibleCount, setVisibleCount] = useState(LOAD_STEP)
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [showWelcomeModal, setShowWelcomeModal] = useState(true)

  const categoryConfigs = useMemo<CategoryDefinition[]>(() => {
    if (!Array.isArray(categoriesData)) {
      return []
    }

    const entries = categoriesData as RawCategoryEntry[]

    return entries
      .map((entry) => {
        if (typeof entry === 'string') {
          const label = entry.trim()
          if (label.length === 0) {
            return null
          }

          return {
            label,
            normalizedLabel: normalizeQuery(label),
            aliases: [],
            normalizedAliases: [] as string[],
          }
        }

        if (entry && typeof entry === 'object') {
          const label = typeof entry.label === 'string' ? entry.label.trim() : ''
          if (label.length === 0) {
            return null
          }

          const aliases = Array.isArray(entry.aliases)
            ? entry.aliases
                .map((alias) => (typeof alias === 'string' ? alias.trim() : ''))
                .filter((alias) => alias.length > 0)
            : []

          return {
            label,
            normalizedLabel: normalizeQuery(label),
            aliases,
            normalizedAliases: aliases.map((alias) => normalizeQuery(alias)),
          }
        }

        return null
      })
      .filter((entry): entry is CategoryDefinition => entry !== null)
  }, [])

  const aliasLookup = useMemo(() => {
    const map = new Map<string, string>()
    categoryConfigs.forEach((config) => {
      map.set(config.normalizedLabel, config.normalizedLabel)
      config.normalizedAliases.forEach((alias) => {
        if (!map.has(alias)) {
          map.set(alias, config.normalizedLabel)
        }
      })
    })
    return map
  }, [categoryConfigs])

  const availableCategories = useMemo(() => {
    const normalizedLabels = categoryConfigs.map((config) => config.normalizedLabel)
    const uniqueNormalized = Array.from(new Set(normalizedLabels)).sort((a, b) =>
      a.localeCompare(b),
    )

    return ['all', ...uniqueNormalized, 'other']
  }, [categoryConfigs])

  const filteredWorkspaces = useMemo(() => {
    const needle = normalizeQuery(searchTerm)
    const normalizedCategory = normalizeQuery(selectedCategory)
    const results: Array<{ workspace: Workspace; score: number }> = []

    workspaces.forEach((workspace) => {
      const normalizedFields = [
        workspace.slug,
        workspace.name,
        workspace.author,
        workspace.repository,
        workspace.registryUrl,
      ]
        .map((field) => normalizeQuery(field))
        .filter((field) => field.length > 0)

      const matchesSearch =
        needle.length === 0 ||
        normalizedFields.some((field) => field.includes(needle))

      if (!matchesSearch) {
        return
      }

      const matchesCategory =
        normalizedCategory === 'all' ||
        (normalizedCategory === 'other'
          ? workspace.categories.some((category) => {
              const normalized = normalizeQuery(category)
              const canonical = aliasLookup.get(normalized)
              return !canonical
            })
          : workspace.categories.some((category) => {
              const normalized = normalizeQuery(category)
              const canonical = aliasLookup.get(normalized)
              return canonical === normalizedCategory
            }))

      if (!matchesCategory) {
        return
      }

      const hasExact =
        needle.length > 0 && normalizedFields.some((field) => field === needle)
      const hasPrefix =
        needle.length > 0 && normalizedFields.some((field) => field.startsWith(needle))

      const score =
        needle.length === 0 ? 3 : hasExact ? 0 : hasPrefix ? 1 : 2

      results.push({ workspace, score })
    })

    results.sort((a, b) => {
      if (a.score !== b.score) {
        return a.score - b.score
      }

      if (selectedSort === 'updated') {
        if (b.workspace.lastCommitTimestamp !== a.workspace.lastCommitTimestamp) {
          return b.workspace.lastCommitTimestamp - a.workspace.lastCommitTimestamp
        }

        if (b.workspace.stars !== a.workspace.stars) {
          return b.workspace.stars - a.workspace.stars
        }
      } else {
        if (b.workspace.stars !== a.workspace.stars) {
          return b.workspace.stars - a.workspace.stars
        }

        if (b.workspace.lastCommitTimestamp !== a.workspace.lastCommitTimestamp) {
          return b.workspace.lastCommitTimestamp - a.workspace.lastCommitTimestamp
        }
      }

      return a.workspace.name.localeCompare(b.workspace.name)
    })

    return results.map((entry) => entry.workspace)
  }, [workspaces, searchTerm, selectedCategory, selectedSort, aliasLookup])

  useEffect(() => {
    setVisibleCount(LOAD_STEP)
  }, [searchTerm, selectedCategory, selectedSort])

  const safeVisibleCount = Math.min(visibleCount, filteredWorkspaces.length)
  const visibleWorkspaces = filteredWorkspaces.slice(0, safeVisibleCount)

  const hasMore = filteredWorkspaces.length > safeVisibleCount

  const handleOpenDetails = (workspace: Workspace) => {
    setSelectedWorkspace(workspace)
  }

  const handleCloseDetails = () => {
    setSelectedWorkspace(null)
  }

  return (
    <div className="relative min-h-screen bg-background">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 bg-cover bg-center bg-no-repeat bg-fixed bg-blend-overlay opacity-10 transition-all duration-700 dark:opacity-5"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundColor: 'rgba(var(--brand-navy-rgb), 0.8)',
        }}
      />
      <div className="relative z-10 min-h-screen overflow-hidden">
  <div className="container relative flex min-h-screen flex-col gap-10 py-10 pt-12">
          <header className="space-y-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <h1 className="text-3xl font-semibold text-foreground md:text-4xl">
                  Kasm Community Images Explorer
                </h1>
                <p className="max-w-2xl text-sm text-muted-foreground md:text-base">
                  Browse community-created Kasm images, compare stars, and find the workspace that fits your workflow. Search or filter based on category, most recent updates or most stars.
                </p>
              </div>
              <div className="flex justify-end md:justify-start">
                <ThemeToggle />
              </div>
            </div>

            <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4 shadow-md md:flex-row md:items-center">
              <div className="flex w-full flex-1 items-center gap-2">
                <div className="relative w-full md:max-w-md">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search by workspace, author, or registry"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="flex flex-1 flex-wrap items-center gap-3">
                <div className="flex min-w-[180px] flex-1 flex-col gap-1">
                  <label className="text-xs uppercase tracking-wide text-muted-foreground/80">
                    Category
                  </label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="All categories" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px] overflow-y-auto">
                      {availableCategories.map((category) => (
                        <SelectItem key={category} value={category}>
                          {category === 'all'
                            ? 'ALL CATEGORIES'
                            : category === 'other'
                            ? 'OTHER'
                            : formatCategoryLabel(category).toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex min-w-[180px] flex-1 flex-col gap-1">
                  <label className="text-xs uppercase tracking-wide text-muted-foreground/80">
                    Filter by
                  </label>
                  <Select value={selectedSort} onValueChange={setSelectedSort}>
                    <SelectTrigger>
                      <SelectValue placeholder="Sort option" />
                    </SelectTrigger>
                    <SelectContent>
                      {sortFilters.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </section>
          </header>

          <section className="space-y-4">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Showing {visibleWorkspaces.length} of {filteredWorkspaces.length}{' '}
                workspaces
              </span>
            </div>

            <div className="flex items-start">
              <button
                onClick={() => setShowInfoModal(true)}
                className="text-sm text-primary hover:underline"
              >
                Why isn't my workspace listed here?
              </button>
            </div>

            {filteredWorkspaces.length === 0 ? (
              <div className="flex min-h-[200px] flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card text-center text-muted-foreground">
                <p className="text-base font-medium text-foreground/80">
                  No workspaces matched your filters
                </p>
                <p className="mt-2 max-w-md text-sm">
                  Try broadening your search keywords or resetting the filters to explore everything the community has shared.
                </p>
              </div>
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {visibleWorkspaces.map((workspace) => (
                    <WorkspaceCard
                      key={`${workspace.repository}/${workspace.slug}`}
                      workspace={workspace}
                      onViewDetails={handleOpenDetails}
                    />
                  ))}
                </div>
                {hasMore ? (
                  <div className="flex justify-center pt-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        setVisibleCount((current) =>
                          Math.min(current + LOAD_STEP, filteredWorkspaces.length),
                        )
                      }
                    >
                      Load more
                    </Button>
                  </div>
                ) : null}
              </>
            )}
          </section>
        </div>
      </div>
      {showWelcomeModal ? (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-background/80 px-4 backdrop-blur"
          onClick={() => setShowWelcomeModal(false)}
        >
          <div
            className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-border bg-modal text-modal-foreground shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border bg-muted px-6 py-4">
              <h2 className="text-lg font-semibold text-modal-foreground">Welcome!</h2>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="text-muted-foreground"
                onClick={() => setShowWelcomeModal(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4 px-6 py-5 text-sm text-muted-foreground">
              <p>
                The images listed in this explorer are created and maintained by the Kasm
                community. They are NOT officially QA tested, certified, or supported by
                Kasm Technologies.
              </p>
              <p className="font-medium text-foreground">
                Use these community images at your own risk. Review the source repository and
                validate compatibility before deploying to your Kasm Workspaces.
              </p>
            </div>
          </div>
        </div>
      ) : null}
      {showInfoModal ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 px-4 backdrop-blur"
          onClick={() => setShowInfoModal(false)}
        >
          <div
            className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-modal text-modal-foreground shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border bg-muted px-6 py-4">
              <h2 className="text-lg font-semibold text-modal-foreground">
                Why isn't my workspace listed here?
              </h2>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="text-muted-foreground"
                onClick={() => setShowInfoModal(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4 px-6 py-5 text-sm text-muted-foreground">
              <p>
                This explorer automatically discovers community Kasm workspaces from GitHub repositories. Your workspace might not be listed for several reasons:
              </p>
              <div className="space-y-3">
                <div>
                  <h3 className="font-semibold text-foreground mb-1">1. Repository Not Discoverable</h3>
                  <p>Make sure your repository includes the discovery identifier <code className="rounded bg-muted/60 px-1">KASM-REGISTRY-DISCOVERY-IDENTIFIER</code> in the README.md file (This comes by default if you created the template from the{' '}
                  <a
                    href="https://github.com/kasmtech/workspaces_registry_template"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Kasm Workspaces Registry Template
                  </a>
                  ). Also, make sure your repository is public.</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">2. Images Not Pullable</h3>
                  <p>All Docker images defined in your workspace.json must be publicly accessible and pullable. Private or inaccessible images are filtered out and only publicly pullable images are listed.</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">3. Profanity</h3>
                  <p>If your workspace name, description, or categories contain profanity, it will be filtered out.</p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">4. Recently Added</h3>
                  <p>The explorer updates every 24 hours. If you just added your workspace, it will not appear until the next update cycle.</p>
                </div>
              </div>
              <p className="pt-2">
                For more information, check out {' '}
                <a
                  href="https://github.com/teja156/kasm_community_images_explorer/blob/main/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  how this app works
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      ) : null}
      {selectedWorkspace ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 px-4 backdrop-blur"
          onClick={handleCloseDetails}
        >
          <div
            className="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-border bg-modal text-modal-foreground shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border bg-muted px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  {selectedWorkspace.name}
                </h2>
                <p className="text-xs text-muted-foreground">
                  Repository: {selectedWorkspace.repository}
                </p>
              </div>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="text-muted-foreground"
                onClick={handleCloseDetails}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4 px-6 py-5">
              <p className="text-sm text-muted-foreground">
                Showing raw <code className="rounded bg-muted/60 px-1">workspace.json</code> data for this workspace.
              </p>
              <pre className="max-h-[60vh] overflow-auto rounded-xl bg-muted p-4 text-xs leading-relaxed text-muted-foreground">
                {JSON.stringify(selectedWorkspace.rawWorkspaceData, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default App

function normalizeWorkspaces(data: RawWorkspacesData): Workspace[] {
  const normalized: Workspace[] = []

  Object.entries(data).forEach(([repositoryKey, repositoryValue]) => {
    if (!repositoryValue) {
      return
    }

    const author = repositoryKey.split('/')[0] ?? repositoryKey
    const registryUrl =
      repositoryValue.github_pages ?? `https://github.com/${repositoryKey}`
    const repositoryStars = parseStars(repositoryValue.stars)
    const effectiveLastCommit =
      repositoryValue.last_commit ??
      repositoryValue.pushed_at ??
      DEFAULT_LAST_COMMIT
    const repositoryLastCommit = parseTimestamp(effectiveLastCommit)

    repositoryValue.workspaces?.forEach((workspaceGroup) => {
      Object.entries(workspaceGroup ?? {}).forEach(([slug, details]) => {
        if (!details) {
          return
        }

        const compatibility = details.compatibility ?? []
        const availableTags = compatibility.flatMap(
          (entry) => entry.available_tags ?? [],
        )
        const dockerImage = deriveDockerImage(slug, details, compatibility)

        normalized.push({
          slug,
          name: details.friendly_name ?? slug,
          description: details.description ?? 'No description available',
          registryUrl,
          author,
          stars: repositoryStars,
          categories: details.categories ?? [],
          architectures: details.architecture ?? [],
          dockerImage,
          tags: availableTags,
          repository: repositoryKey,
          lastCommit: effectiveLastCommit,
          lastCommitTimestamp: repositoryLastCommit,
          rawWorkspaceData: details,
        })
      })
    })
  })

  return normalized.sort((a, b) => {
    if (b.stars !== a.stars) {
      return b.stars - a.stars
    }

    if (b.lastCommitTimestamp !== a.lastCommitTimestamp) {
      return b.lastCommitTimestamp - a.lastCommitTimestamp
    }

    return a.name.localeCompare(b.name)
  })
}

function deriveDockerImage(
  slug: string,
  details: RawWorkspaceDefinition,
  compatibility: RawCompatibilityEntry[],
) {
  if (details.name) {
    return details.name
  }

  if (compatibility.length && compatibility[0]?.image) {
    return compatibility[0].image
  }

  if (details.docker_registry) {
    const registry = details.docker_registry.replace(/\/$/, '')
    return `${registry}/${slug}`
  }

  return undefined
}
function normalizeQuery(input: string | undefined) {
  return input?.toString().trim().toLocaleLowerCase() ?? ''
}

function parseStars(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return Math.max(0, Math.floor(value))
  }

  const parsed = Number(value)
  if (Number.isFinite(parsed)) {
    return Math.max(0, Math.floor(parsed))
  }

  return 0
}

function parseTimestamp(value: unknown) {
  if (typeof value === 'string') {
    const timestamp = Date.parse(value)
    if (!Number.isNaN(timestamp)) {
      return timestamp
    }
  }

  return 0
}

function formatCategoryLabel(value: string) {
  return value
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')
}
