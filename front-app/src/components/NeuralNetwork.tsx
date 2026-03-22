import { useEffect, useRef } from 'react'

interface Node {
  x: number
  y: number
  vx: number
  vy: number
  activation: number
  connections: number[]
}

interface Signal {
  path: number[]
  hopIndex: number
  progress: number
  speed: number
  normSpeed: number
  fragment: string
  textOffsetX: number
  textOffsetY: number
  bright: boolean    // true = full glow; false = faint background signal
}

const FRAGMENTS = [
  're:', 'mem', '0x4f', 'th..', '#002', 'if(', '...', '??',
  '01', 'fn:', 'var', '::1', 'ctx', 'new', 'log', 'err',
  '404', 'tmp', 'ref', 'del', 'sig', 'rx:', 'τ=', '∂x',
  'α:', 'β1', 'nxt', 'w+1', '∞', 'Δt',
]

const COLS           = 5
const ROWS           = 3
const TARGET_SIGNALS = 100
const BRIGHT_SIGNALS = 25   // how many of the 100 are fully bright
const MIN_SPEED      = 0.002
const MAX_SPEED      = 0.004
const DECAY          = 0.97
const MAX_CONN       = 6
const MAX_DIST       = 160

// Cluster radius variety — mix of tight and loose, scaled up to fill cells
const CLUSTER_RADII = [55, 90, 40, 120, 70, 150, 35, 130, 80, 55, 170, 100, 115, 50, 130]

// indigo (slow) → cyan (fast)
function sigRgb(t: number) {
  return [
    Math.round(99  + (103 - 99)  * t),
    Math.round(102 + (232 - 102) * t),
    Math.round(241 + (249 - 241) * t),
  ] as const
}

function pick<T>(arr: T[]): T { return arr[Math.floor(Math.random() * arr.length)] }

export function NeuralNetwork() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const c = canvas
    const g = ctx
    let w = 0, h = 0

    let nodes: Node[]     = []
    let signals: Signal[] = []
    let zoneMap: number[][] = []
    let frame = 0
    let initialised = false

    function build() {
      nodes   = []
      signals = []

      // ── Scale node count to screen area ──────────────────────────────────
      const nodeCount    = Math.max(80, Math.min(400, Math.floor(w * h / 5000)))
      const clusterNodes = Math.floor(nodeCount * 0.88)
      const isolatedCount = nodeCount - clusterNodes
      const perCluster   = Math.max(3, Math.floor(clusterNodes / (COLS * ROWS)))

      const cellW = w / COLS
      const cellH = h / ROWS

      // ── One cluster per grid cell ─────────────────────────────────────────
      for (let cellIdx = 0; cellIdx < COLS * ROWS; cellIdx++) {
        const col    = cellIdx % COLS
        const row    = Math.floor(cellIdx / COLS)
        const radius = CLUSTER_RADII[cellIdx] ?? 40
        const cx     = col * cellW + cellW * 0.15 + Math.random() * cellW * 0.7
        const cy     = row * cellH + cellH * 0.15 + Math.random() * cellH * 0.7

        for (let i = 0; i < perCluster; i++) {
          const angle = Math.random() * Math.PI * 2
          const r     = Math.pow(Math.random(), 0.5) * radius
          nodes.push({
            x: Math.max(2, Math.min(w - 2, cx + Math.cos(angle) * r)),
            y: Math.max(2, Math.min(h - 2, cy + Math.sin(angle) * r)),
            vx: (Math.random() - 0.5) * 0.04,
            vy: (Math.random() - 0.5) * 0.04,
            activation: 0,
            connections: [],
          })
        }
      }

      // ── Isolated nodes scattered across full canvas ───────────────────────
      for (let i = 0; i < isolatedCount; i++) {
        nodes.push({
          x: w * 0.02 + Math.random() * w * 0.96,
          y: h * 0.02 + Math.random() * h * 0.96,
          vx: (Math.random() - 0.5) * 0.04,
          vy: (Math.random() - 0.5) * 0.04,
          activation: 0,
          connections: [],
        })
      }

      // ── Wire nearby connections ───────────────────────────────────────────
      for (let i = 0; i < nodes.length; i++) {
        const ranked: [number, number][] = []
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const d  = Math.sqrt(dx * dx + dy * dy)
          if (d < MAX_DIST) ranked.push([j, d])
        }
        ranked.sort((a, b) => a[1] - b[1])
        nodes[i].connections = ranked.slice(0, MAX_CONN).map(r => r[0])
      }

      // ── Build zone map ────────────────────────────────────────────────────
      zoneMap = Array.from({ length: COLS * ROWS }, () => [])
      for (let i = 0; i < nodes.length; i++) {
        const col = Math.min(COLS - 1, Math.floor(nodes[i].x / (w / COLS)))
        const row = Math.min(ROWS - 1, Math.floor(nodes[i].y / (h / ROWS)))
        zoneMap[row * COLS + col].push(i)
      }

      // Pre-fill signals
      for (let i = 0; i < TARGET_SIGNALS; i++) spawnSignal()
    }

    // ── Zone-interpolated waypoint routing ───────────────────────────────────
    // Interpolates through grid zones from source to destination.
    // No BFS = no hub bottleneck. Guarantees signals cross multiple zones.
    function spawnSignal() {
      if (nodes.length < 2 || zoneMap.length === 0) return

      // Pick source and destination zones (must differ)
      const fromZone = Math.floor(Math.random() * (COLS * ROWS))
      let toZone     = Math.floor(Math.random() * (COLS * ROWS))
      let tries = 0
      while (toZone === fromZone && tries++ < 15) toZone = Math.floor(Math.random() * (COLS * ROWS))
      if (toZone === fromZone) return

      const fromCol = fromZone % COLS,    fromRow = Math.floor(fromZone / COLS)
      const toCol   = toZone   % COLS,    toRow   = Math.floor(toZone   / COLS)

      const numHops = 3 + Math.floor(Math.random() * 3)  // 3–5 hops total
      const path: number[] = []

      // Source node
      const srcList = zoneMap[fromZone]
      if (!srcList?.length) return
      path.push(srcList[Math.floor(Math.random() * srcList.length)])

      // Intermediate waypoints — interpolate zone coordinates
      for (let step = 1; step < numHops; step++) {
        const t      = step / numHops
        const midCol = Math.min(COLS - 1, Math.max(0, Math.round(fromCol + t * (toCol - fromCol))))
        const midRow = Math.min(ROWS - 1, Math.max(0, Math.round(fromRow + t * (toRow - fromRow))))
        const midZone = midRow * COLS + midCol
        const midList = zoneMap[midZone]
        if (!midList?.length) continue
        const candidate = midList[Math.floor(Math.random() * midList.length)]
        // Avoid duplicate consecutive nodes
        if (candidate !== path[path.length - 1]) path.push(candidate)
      }

      // Destination node
      const dstList = zoneMap[toZone]
      if (!dstList?.length) return
      const dst = dstList[Math.floor(Math.random() * dstList.length)]
      if (dst !== path[path.length - 1]) path.push(dst)

      if (path.length < 2) return

      const raw    = MIN_SPEED + Math.random() * (MAX_SPEED - MIN_SPEED)
      const norm   = (raw - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)
      const bright = signals.filter(s => s.bright).length < BRIGHT_SIGNALS
      signals.push({
        path,
        hopIndex: 0,
        progress: Math.random() * 0.6,
        speed: raw,
        normSpeed: norm,
        fragment: pick(FRAGMENTS),
        textOffsetX: (Math.random() - 0.5) * 16,
        textOffsetY: -8 - Math.random() * 10,
        bright,
      })
    }

    function draw() {
      frame = requestAnimationFrame(draw)
      g.clearRect(0, 0, w, h)

      // Drift nodes (barely)
      for (const n of nodes) {
        n.x += n.vx;  n.y += n.vy
        if (n.x < 0 || n.x > w) n.vx *= -1
        if (n.y < 0 || n.y > h) n.vy *= -1
        n.activation *= DECAY
      }

      // Maintain 100 active signals, capped spawn attempts per frame
      let spawnTries = 0
      while (signals.length < TARGET_SIGNALS && spawnTries++ < 10) spawnSignal()

      // ── Connection web ────────────────────────────────────────────────────
      for (let i = 0; i < nodes.length; i++) {
        for (const j of nodes[i].connections) {
          if (j <= i) continue
          const act   = Math.max(nodes[i].activation, nodes[j].activation)
          const alpha = 0.04 + act * 0.22
          g.beginPath()
          g.moveTo(nodes[i].x, nodes[i].y)
          g.lineTo(nodes[j].x, nodes[j].y)
          g.strokeStyle = `rgba(99,102,241,${alpha})`
          g.lineWidth   = 0.5 + act * 0.8
          g.stroke()
        }
      }

      // ── Nodes ─────────────────────────────────────────────────────────────
      for (const n of nodes) {
        const act = n.activation

        // Always-on ambient glow
        const ag = g.createRadialGradient(n.x, n.y, 0, n.x, n.y, 6)
        ag.addColorStop(0, 'rgba(99,102,241,0.18)')
        ag.addColorStop(1, 'rgba(99,102,241,0)')
        g.beginPath()
        g.arc(n.x, n.y, 6, 0, Math.PI * 2)
        g.fillStyle = ag
        g.fill()

        // Activation pulse
        if (act > 0.03) {
          const gr = 5 + act * 20
          const ng = g.createRadialGradient(n.x, n.y, 0, n.x, n.y, gr)
          ng.addColorStop(0, `rgba(165,180,252,${act * 0.85})`)
          ng.addColorStop(1, 'rgba(99,102,241,0)')
          g.beginPath()
          g.arc(n.x, n.y, gr, 0, Math.PI * 2)
          g.fillStyle = ng
          g.fill()
        }

        // Core dot
        g.beginPath()
        g.arc(n.x, n.y, 2.2 + act * 2.5, 0, Math.PI * 2)
        g.fillStyle = act > 0.05
          ? `rgba(224,231,255,${0.7 + act * 0.3})`
          : 'rgba(148,154,255,0.75)'
        g.fill()
      }

      // ── Signals ───────────────────────────────────────────────────────────
      for (let i = signals.length - 1; i >= 0; i--) {
        const sig = signals[i]
        sig.progress += sig.speed

        if (sig.progress >= 1) {
          // Arrived at next waypoint — pulse it
          const arrived = sig.path[sig.hopIndex + 1]
          if (nodes[arrived]) nodes[arrived].activation = 1
          sig.hopIndex++
          sig.progress = 0

          // Reached final destination — retire signal
          if (sig.hopIndex >= sig.path.length - 1) {
            signals.splice(i, 1)
          }
          continue
        }

        const fn = nodes[sig.path[sig.hopIndex]]
        const tn = nodes[sig.path[sig.hopIndex + 1]]
        if (!fn || !tn) { signals.splice(i, 1); continue }

        const x = fn.x + (tn.x - fn.x) * sig.progress
        const y = fn.y + (tn.y - fn.y) * sig.progress
        const [r, gv, b] = sigRgb(sig.normSpeed)

        if (sig.bright) {
          // ── Bright signal: full glow + trail + text ──────────────────────
          const trailT = Math.max(0, sig.progress - 0.22)
          const tx1    = fn.x + (tn.x - fn.x) * trailT
          const ty1    = fn.y + (tn.y - fn.y) * trailT
          const tGrad  = g.createLinearGradient(tx1, ty1, x, y)
          tGrad.addColorStop(0, `rgba(${r},${gv},${b},0)`)
          tGrad.addColorStop(1, `rgba(${r},${gv},${b},0.6)`)
          g.beginPath(); g.moveTo(tx1, ty1); g.lineTo(x, y)
          g.strokeStyle = tGrad; g.lineWidth = 1.2 + sig.normSpeed; g.stroke()

          const hr    = 6 + sig.normSpeed * 8
          const hGrad = g.createRadialGradient(x, y, 0, x, y, hr)
          hGrad.addColorStop(0, `rgba(${r},${gv},${b},0.9)`)
          hGrad.addColorStop(1, `rgba(${r},${gv},${b},0)`)
          g.beginPath(); g.arc(x, y, hr, 0, Math.PI * 2)
          g.fillStyle = hGrad; g.fill()

          g.beginPath(); g.arc(x, y, 2 + sig.normSpeed * 1.5, 0, Math.PI * 2)
          g.fillStyle = 'rgba(255,255,255,0.95)'; g.fill()

          g.save()
          g.font = '8px monospace'
          g.fillStyle   = `rgba(${r},${gv},${b},0.32)`
          g.shadowColor = `rgba(${r},${gv},${b},0.6)`
          g.shadowBlur  = 4
          g.fillText(sig.fragment, x + sig.textOffsetX, y + sig.textOffsetY)
          g.restore()
        } else {
          // ── Dim signal: faint trail + tiny dot only ───────────────────────
          const trailT = Math.max(0, sig.progress - 0.18)
          const tx1    = fn.x + (tn.x - fn.x) * trailT
          const ty1    = fn.y + (tn.y - fn.y) * trailT
          const tGrad  = g.createLinearGradient(tx1, ty1, x, y)
          tGrad.addColorStop(0, `rgba(${r},${gv},${b},0)`)
          tGrad.addColorStop(1, `rgba(${r},${gv},${b},0.18)`)
          g.beginPath(); g.moveTo(tx1, ty1); g.lineTo(x, y)
          g.strokeStyle = tGrad; g.lineWidth = 0.7; g.stroke()

          g.beginPath(); g.arc(x, y, 1.2, 0, Math.PI * 2)
          g.fillStyle = `rgba(148,154,255,0.45)`; g.fill()
        }
      }
    }

    const ro = new ResizeObserver(entries => {
      const rect = entries[0].contentRect
      w = rect.width
      h = rect.height
      c.width  = w
      c.height = h
      if (!initialised && w > 0 && h > 0) {
        initialised = true
        build()
        draw()
      }
    })
    ro.observe(c)

    return () => { cancelAnimationFrame(frame); ro.disconnect() }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
    />
  )
}
