import { useEffect, useRef, useState } from 'react'

interface Props {
  onCapture: (dataUrl: string) => void
  onCancel: () => void
}

export default function CameraCapture({ onCapture, onCancel }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<{
    type: 'move' | 'tl' | 'tr' | 'bl' | 'br'
    startPx: number; startPy: number
    startCrop: { x: number; y: number; w: number; h: number }
  } | null>(null)

  const [liveBrightness, setLiveBrightness] = useState(100)
  const [liveContrast, setLiveContrast] = useState(100)
  const [liveSaturation, setLiveSaturation] = useState(100)
  const [liveZoom, setLiveZoom] = useState<number>(() => {
    try { const s = localStorage.getItem('cameraZoom'); return s ? Math.min(4, Math.max(1, parseFloat(s))) : 1 } catch { return 1 }
  })
  const [liveCrop, setLiveCrop] = useState({ x: 0, y: 0, w: 1, h: 1 })
  const [liveRatio, setLiveRatio] = useState<number | null>(4 / 3)
  const [cameraError, setCameraError] = useState(false)

  useEffect(() => {
    let active = true
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: { ideal: 'environment' } } })
      .then(stream => {
        if (!active) { stream.getTracks().forEach(t => t.stop()); return }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play()
          videoRef.current.onloadedmetadata = () => {
            if (!videoRef.current) return
            const vw = videoRef.current.videoWidth, vh = videoRef.current.videoHeight
            const r = 4 / 3
            let cw = vw, ch = vh, cx = 0, cy = 0
            if (vw / vh > r) { cw = vh * r; cx = (vw - cw) / 2 }
            else { ch = vw / r; cy = (vh - ch) / 2 }
            setLiveCrop({ x: cx / vw, y: cy / vh, w: cw / vw, h: ch / vh })
          }
        }
      })
      .catch(() => setCameraError(true))
    return () => {
      active = false
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [])

  function setZoom(z: number) {
    setLiveZoom(z)
    try { localStorage.setItem('cameraZoom', String(z)) } catch {}
  }

  function selectRatio(r: number | null) {
    setLiveRatio(r)
    const vw = videoRef.current?.videoWidth || 1
    const vh = videoRef.current?.videoHeight || 1
    if (r === null) { setLiveCrop({ x: 0, y: 0, w: 1, h: 1 }); return }
    let cw = vw, ch = vh, cx = 0, cy = 0
    if (vw / vh > r) { cw = vh * r; cx = (vw - cw) / 2 }
    else { ch = vw / r; cy = (vh - ch) / 2 }
    setLiveCrop({ x: cx / vw, y: cy / vh, w: cw / vw, h: ch / vh })
  }

  function onPointerDown(e: React.PointerEvent, type: 'move' | 'tl' | 'tr' | 'bl' | 'br') {
    e.stopPropagation()
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    dragRef.current = {
      type,
      startPx: (e.clientX - rect.left) / rect.width,
      startPy: (e.clientY - rect.top) / rect.height,
      startCrop: { ...liveCrop },
    }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!dragRef.current || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const dx = (e.clientX - rect.left) / rect.width - dragRef.current.startPx
    const dy = (e.clientY - rect.top) / rect.height - dragRef.current.startPy
    const sc = dragRef.current.startCrop
    const MIN = 0.15
    let { x, y, w, h } = sc
    if (dragRef.current.type === 'move') {
      x = Math.max(0, Math.min(1 - sc.w, sc.x + dx))
      y = Math.max(0, Math.min(1 - sc.h, sc.y + dy))
    } else if (dragRef.current.type === 'br') {
      w = Math.max(MIN, Math.min(1 - sc.x, sc.w + dx))
      h = Math.max(MIN, Math.min(1 - sc.y, sc.h + dy))
    } else if (dragRef.current.type === 'tl') {
      const nx = Math.max(0, Math.min(sc.x + sc.w - MIN, sc.x + dx))
      const ny = Math.max(0, Math.min(sc.y + sc.h - MIN, sc.y + dy))
      w = sc.w + (sc.x - nx); h = sc.h + (sc.y - ny); x = nx; y = ny
    } else if (dragRef.current.type === 'tr') {
      const ny = Math.max(0, Math.min(sc.y + sc.h - MIN, sc.y + dy))
      w = Math.max(MIN, Math.min(1 - sc.x, sc.w + dx)); h = sc.h + (sc.y - ny); y = ny
    } else if (dragRef.current.type === 'bl') {
      const nx = Math.max(0, Math.min(sc.x + sc.w - MIN, sc.x + dx))
      w = sc.w + (sc.x - nx); h = Math.max(MIN, Math.min(1 - sc.y, sc.h + dy)); x = nx
    }
    setLiveCrop({ x, y, w, h })
  }

  function capture() {
    if (!videoRef.current) return
    const v = videoRef.current
    const vw = v.videoWidth, vh = v.videoHeight
    const visStart = 0.5 - 0.5 / liveZoom
    const sx = Math.round((visStart + liveCrop.x / liveZoom) * vw)
    const sy = Math.round((visStart + liveCrop.y / liveZoom) * vh)
    const sw = Math.round((liveCrop.w / liveZoom) * vw)
    const sh = Math.round((liveCrop.h / liveZoom) * vh)
    const canvas = document.createElement('canvas')
    canvas.width = sw; canvas.height = sh
    const ctx = canvas.getContext('2d')!
    ctx.filter = `brightness(${liveBrightness}%) contrast(${liveContrast}%) saturate(${liveSaturation}%)`
    ctx.drawImage(v, sx, sy, sw, sh, 0, 0, sw, sh)
    onCapture(canvas.toDataURL('image/jpeg', 0.95))
  }

  if (cameraError) {
    return (
      <div className="rounded-xl border border-stone-200 bg-stone-50 p-6 text-center text-sm text-stone-500">
        Camera not available.
        <button onClick={onCancel} className="ml-3 text-amber-600 hover:underline">Cancel</button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Live video + crop overlay */}
      <div
        ref={containerRef}
        className="relative overflow-hidden rounded-xl border border-stone-200 bg-black select-none"
        style={{ touchAction: 'none' }}
        onPointerMove={onPointerMove}
        onPointerUp={() => { dragRef.current = null }}
      >
        <video
          ref={videoRef}
          className="w-full block"
          style={{
            filter: `brightness(${liveBrightness}%) contrast(${liveContrast}%) saturate(${liveSaturation}%)`,
            transform: `scale(${liveZoom})`,
            transformOrigin: 'center',
          }}
          autoPlay muted playsInline
        />
        {/* Dark mask outside crop */}
        <div className="absolute inset-x-0 top-0 bg-black/50 pointer-events-none" style={{ height: `${liveCrop.y * 100}%` }} />
        <div className="absolute inset-x-0 bottom-0 bg-black/50 pointer-events-none" style={{ height: `${(1 - liveCrop.y - liveCrop.h) * 100}%` }} />
        <div className="absolute bg-black/50 pointer-events-none" style={{ top: `${liveCrop.y * 100}%`, height: `${liveCrop.h * 100}%`, left: 0, width: `${liveCrop.x * 100}%` }} />
        <div className="absolute bg-black/50 pointer-events-none" style={{ top: `${liveCrop.y * 100}%`, height: `${liveCrop.h * 100}%`, right: 0, width: `${(1 - liveCrop.x - liveCrop.w) * 100}%` }} />
        {/* Crop box */}
        <div
          className="absolute border-2 border-white cursor-move"
          style={{ left: `${liveCrop.x * 100}%`, top: `${liveCrop.y * 100}%`, width: `${liveCrop.w * 100}%`, height: `${liveCrop.h * 100}%` }}
          onPointerDown={e => onPointerDown(e, 'move')}
        >
          <div className="absolute w-5 h-5 bg-white -top-1 -left-1 cursor-nwse-resize" onPointerDown={e => onPointerDown(e, 'tl')} />
          <div className="absolute w-5 h-5 bg-white -top-1 -right-1 cursor-nesw-resize" onPointerDown={e => onPointerDown(e, 'tr')} />
          <div className="absolute w-5 h-5 bg-white -bottom-1 -left-1 cursor-nesw-resize" onPointerDown={e => onPointerDown(e, 'bl')} />
          <div className="absolute w-5 h-5 bg-white -bottom-1 -right-1 cursor-nwse-resize" onPointerDown={e => onPointerDown(e, 'br')} />
        </div>
      </div>

      {/* Ratio presets */}
      <div className="flex flex-wrap gap-1.5">
        {([
          { label: 'Free', value: null },
          { label: '1:1', value: 1 },
          { label: '4:3', value: 4 / 3 },
          { label: '3:4', value: 3 / 4 },
          { label: '16:9', value: 16 / 9 },
          { label: '2:3', value: 2 / 3 },
        ] as const).map(p => (
          <button
            key={p.label}
            onClick={() => selectRatio(p.value)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
              liveRatio === p.value
                ? 'border-amber-400 bg-amber-50 text-amber-700'
                : 'border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-stone-50'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Sliders */}
      <div className="space-y-2 px-1">
        <div className="flex items-center gap-2">
          <span className="w-20 text-xs text-stone-500 flex-shrink-0">Zoom</span>
          <button onClick={() => setZoom(Math.max(1, +(liveZoom - 0.25).toFixed(2)))} className="text-stone-400 hover:text-stone-700 text-base leading-none px-0.5">−</button>
          <input type="range" min={1} max={4} step={0.05} value={liveZoom}
            onChange={e => setZoom(Number(e.target.value))}
            className="flex-1 accent-amber-500" />
          <button onClick={() => setZoom(Math.min(4, +(liveZoom + 0.25).toFixed(2)))} className="text-stone-400 hover:text-stone-700 text-base leading-none px-0.5">+</button>
          <span className="text-xs text-stone-400 w-8 text-right">{liveZoom.toFixed(1)}×</span>
          <button onClick={() => setZoom(1)} className="text-xs text-stone-400 hover:text-stone-600 w-5 text-center">↺</button>
        </div>
        {([
          { label: 'Brightness', val: liveBrightness, set: setLiveBrightness, min: 50, max: 200 },
          { label: 'Contrast',   val: liveContrast,   set: setLiveContrast,   min: 50, max: 200 },
          { label: 'Saturation', val: liveSaturation, set: setLiveSaturation, min: 0,  max: 200 },
        ] as const).map(({ label, val, set, min, max }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="w-20 text-xs text-stone-500 flex-shrink-0">{label}</span>
            <input type="range" min={min} max={max} value={val}
              onChange={e => set(Number(e.target.value))}
              className="flex-1 accent-amber-500" />
            <button onClick={() => set(100)} className="text-xs text-stone-400 hover:text-stone-600 w-5 text-center">↺</button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={capture} className="flex-1 rounded-full bg-amber-500 py-2.5 text-sm font-medium text-white hover:bg-amber-600 transition-colors">
          Capture
        </button>
        <button onClick={onCancel} className="rounded-full border border-stone-200 px-5 py-2.5 text-sm text-stone-600 hover:bg-stone-50">
          Cancel
        </button>
      </div>
    </div>
  )
}
