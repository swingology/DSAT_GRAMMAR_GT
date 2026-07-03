import { useCallback, useState, type ReactElement } from 'react'
import { motion } from 'framer-motion'
import { Responsive, WidthProvider, type Layout, type ResponsiveLayouts } from 'react-grid-layout/legacy'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import {
  AutoReleaseWidget,
  GenerationWidget,
  RecentBatchesWidget,
  UsersWidget,
  WeakSpotsWidget,
} from '../components/dashboard/widgets'

const ResponsiveGridLayout = WidthProvider(Responsive)

const WIDGETS: Record<string, () => ReactElement> = {
  users: UsersWidget,
  generation: GenerationWidget,
  autoRelease: AutoReleaseWidget,
  weakSpots: WeakSpotsWidget,
  recentBatches: RecentBatchesWidget,
}

const DEFAULT_LAYOUTS: ResponsiveLayouts = {
  lg: [
    { i: 'users', x: 0, y: 0, w: 3, h: 3 },
    { i: 'generation', x: 3, y: 0, w: 3, h: 3 },
    { i: 'autoRelease', x: 6, y: 0, w: 3, h: 3 },
    { i: 'weakSpots', x: 9, y: 0, w: 3, h: 5 },
    { i: 'recentBatches', x: 0, y: 3, w: 9, h: 5 },
  ],
  md: [
    { i: 'users', x: 0, y: 0, w: 4, h: 3 },
    { i: 'generation', x: 4, y: 0, w: 4, h: 3 },
    { i: 'autoRelease', x: 0, y: 3, w: 4, h: 3 },
    { i: 'weakSpots', x: 4, y: 3, w: 4, h: 5 },
    { i: 'recentBatches', x: 0, y: 6, w: 8, h: 5 },
  ],
  sm: [
    { i: 'users', x: 0, y: 0, w: 4, h: 3 },
    { i: 'generation', x: 0, y: 3, w: 4, h: 3 },
    { i: 'autoRelease', x: 0, y: 6, w: 4, h: 3 },
    { i: 'weakSpots', x: 0, y: 9, w: 4, h: 5 },
    { i: 'recentBatches', x: 0, y: 14, w: 4, h: 5 },
  ],
}

const STORAGE_KEY = 'admin-dashboard-layouts-v1'

function loadLayouts(): ResponsiveLayouts {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : DEFAULT_LAYOUTS
  } catch {
    return DEFAULT_LAYOUTS
  }
}

export function Dashboard() {
  const [layouts, setLayouts] = useState<ResponsiveLayouts>(loadLayouts)

  const handleLayoutChange = useCallback((_current: Layout, all: ResponsiveLayouts) => {
    setLayouts(all)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
  }, [])

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Dashboard</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Drag panels by their header to rearrange. Layout is saved automatically.
        </p>
      </div>
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1024, md: 768, sm: 480 }}
        cols={{ lg: 12, md: 8, sm: 4 }}
        rowHeight={60}
        draggableHandle=".panel-drag-handle"
        onLayoutChange={handleLayoutChange}
      >
        {Object.entries(WIDGETS).map(([key, Widget], index) => (
          <div key={key}>
            <motion.div
              className="h-full"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.25 }}
            >
              <Widget />
            </motion.div>
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  )
}
