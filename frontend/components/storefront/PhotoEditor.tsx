import { useEffect, useRef, useState } from 'react'

const DEFAULTS_KEY = 'mc_photo_defaults'
const PRESETS_KEY  = 'mc_photo_presets'

interface Adj { brightness: number; contrast: number; saturation: number }
interface Preset extends Adj { name: string }

function loadDefaults(): Adj {
  try {
    if (typeof window === 'undefined') return { brightness: 100, contrast: 100, saturation: 100 }
    const raw = localStorage.getItem(DEFAULTS_KEY)
    return raw ? JSON.parse(raw) : { brightness: 100, contrast: 100, saturation: 100 }
  } catch { return { brightness: 100, contrast: 100, saturation: 100 } }
}

function loadPresets(): Preset[] {
  try {
    if (typeof window === 'undefined') return []
    const raw = localStorage.getItem(PRESETS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function savePresets(presets: Preset[]) {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(presets))
}

interface Crop { x: number; y: number; w: number; h: number }
type Handle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'move'

const RATIO_PRESETS = [
  { label: 'Free',  value: null as number | null },
  { label: '1:1',   value: 1 },
  { label: '4:3',   value: 4 / 3 },
  { label: '3:4',   value: 3 / 4 },
  { label: '16:9',  value: 16 / 9 },
  { label: 'Custom', value: -1 },   // sentinel — shows inputs
]

const CURSOR: Record<Handle, string> = {
  nw: 'nw-resize', n: 'n-resize', ne: 'ne-resize',
  e: 'e-resize', se: 'se-resize', s: 's-resize',
  sw: 'sw-resize', w: 'w-resize', move: 'move',
}

interface Props {
  src: string
  onSave: (dataUrl: string) => void
  onCancel: () => void
}

export default function PhotoEditor({ src, onSave, onCancel }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imgRef    = useRef<HTMLImageElement | null>(null)

  const defs = loadDefaults()
  const [brightness, setBrightness]   = useState(defs.brightness)
  const [contrast,   setContrast]     = useState(defs.contrast)
  const [saturation, setSaturation]   = useState(defs.saturation)
  const [rotation,   setRotation]     = useState(0)
  const [presets,    setPresets]      = useState<Preset[]>(() => loadPresets())
  const [addingPreset, setAddingPreset] = useState(false)
  const [presetName,   setPresetName]   = useState('')
  const [defaultsSaved, setDefaultsSaved] = useState(false)

  const [crop,  setCrop]  = useState<Crop>({ x: 0, y: 0, w: 0, h: 0 })
  const [ratio, setRatio] = useState<number | null>(4 / 3)         // default 4:3
  const [customW, setCustomW] = useState('4')
  const [customH, setCustomH] = useState('3')
  const [showCustom, setShowCustom] = useState(false)

  const drag = useRef<{
    handle: Handle
    startMouse: { x: number; y: number }
    startCrop: Crop
  } | null>(null)

  // ── Load image ────────────────────────────────────────────────────────────
  useEffect(() => {
    const img = new window.Image()
    img.onload = () => {
      imgRef.current = img
      const iw = img.naturalWidth, ih = img.naturalHeight
      const r = 4 / 3
      let cw = iw, ch = ih, cx = 0, cy = 0
      if (iw / ih > r) { cw = ih * r; cx = (iw - cw) / 2 }
      else              { ch = iw / r; cy = (ih - ch) / 2 }
      setCrop({ x: Math.round(cx), y: Math.round(cy), w: Math.round(cw), h: Math.round(ch) })
      renderCanvas(img, defs.brightness, defs.contrast, defs.saturation, 0)
    }
    img.src = src
  }, [src])

  // ── Canvas render ─────────────────────────────────────────────────────────
  function renderCanvas(img: HTMLImageElement, b: number, c: number, s: number, r: number) {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const rotated = r === 90 || r === 270
    const iw = img.naturalWidth, ih = img.naturalHeight
    canvas.width  = rotated ? ih : iw
    canvas.height = rotated ? iw : ih
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.filter = `brightness(${b}%) contrast(${c}%) saturate(${s}%)`
    ctx.save()
    ctx.translate(canvas.width / 2, canvas.height / 2)
    ctx.rotate((r * Math.PI) / 180)
    ctx.drawImage(img, -iw / 2, -ih / 2)
    ctx.restore()
  }

  useEffect(() => {
    if (imgRef.current) renderCanvas(imgRef.current, brightness, contrast, saturation, rotation)
  }, [brightness, contrast, saturation, rotation])

  // ── Crop helpers ──────────────────────────────────────────────────────────
  function clampCrop(c: Crop, iw: number, ih: number, r: number | null): Crop {
    const MIN = 20
    let { x, y, w, h } = c
    w = Math.max(w, MIN); h = Math.max(h, MIN)
    if (r !== null && r > 0) {
      h = w / r
      if (h > ih) { h = ih; w = h * r }
      if (w > iw) { w = iw; h = w / r }
    }
    x = Math.max(0, Math.min(x, iw - w))
    y = Math.max(0, Math.min(y, ih - h))
    w = Math.min(w, iw - x)
    h = Math.min(h, ih - y)
    return { x: Math.round(x), y: Math.round(y), w: Math.round(w), h: Math.round(h) }
  }

  function centerCrop(r: number | null) {
    const canvas = canvasRef.current
    if (!canvas) return
    const iw = canvas.width, ih = canvas.height
    if (r === null || r <= 0) { setCrop({ x: 0, y: 0, w: iw, h: ih }); return }
    let w = iw, h = ih
    if (iw / ih > r) { w = ih * r } else { h = iw / r }
    setCrop({ x: Math.round((iw - w) / 2), y: Math.round((ih - h) / 2), w: Math.round(w), h: Math.round(h) })
  }

  // ── Ratio preset select ───────────────────────────────────────────────────
  function selectPreset(value: number | null) {
    if (value === -1) {
      setShowCustom(true)
      return
    }
    setShowCustom(false)
    setRatio(value)
    centerCrop(value)
  }

  function applyCustomRatio() {
    const w = parseFloat(customW), h = parseFloat(customH)
    if (!w || !h || w <= 0 || h <= 0) return
    const r = w / h
    setRatio(r)
    centerCrop(r)
  }

  // ── Drag handles ──────────────────────────────────────────────────────────
  function startDrag(e: React.PointerEvent, handle: Handle) {
    e.preventDefault(); e.stopPropagation()
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    drag.current = { handle, startMouse: { x: e.clientX, y: e.clientY }, startCrop: { ...crop } }
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!drag.current || !canvasRef.current) return
    const { handle, startMouse, startCrop } = drag.current
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const sx = canvas.width  / rect.width
    const sy = canvas.height / rect.height
    const dx = (e.clientX - startMouse.x) * sx
    const dy = (e.clientY - startMouse.y) * sy

    let { x, y, w, h } = startCrop
    if (handle === 'move') { x += dx; y += dy }
    else {
      if (handle.includes('e')) w += dx
      if (handle.includes('s')) h += dy
      if (handle.includes('w')) { x += dx; w -= dx }
      if (handle.includes('n')) { y += dy; h -= dy }
    }

    setCrop(clampCrop({ x, y, w, h }, canvas.width, canvas.height, ratio))
  }

  function onPointerUp() { drag.current = null }

  // ── Apply crop (bake into new image) ─────────────────────────────────────
  function applyCrop() {
    if (!imgRef.current || !canvasRef.current) return
    const { x, y, w, h } = crop
    if (w < 10 || h < 10) return

    const tmp = document.createElement('canvas')
    const canvas = canvasRef.current
    tmp.width = canvas.width; tmp.height = canvas.height
    const ctx = tmp.getContext('2d')!
    const img = imgRef.current
    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`
    ctx.save()
    ctx.translate(tmp.width / 2, tmp.height / 2)
    ctx.rotate((rotation * Math.PI) / 180)
    ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2)
    ctx.restore()

    const out = document.createElement('canvas')
    out.width = w; out.height = h
    out.getContext('2d')!.drawImage(tmp, x, y, w, h, 0, 0, w, h)

    const cropped = new window.Image()
    cropped.onload = () => {
      imgRef.current = cropped
      setRotation(0)
      setCrop({ x: 0, y: 0, w, h })
      renderCanvas(cropped, brightness, contrast, saturation, 0)
    }
    cropped.src = out.toDataURL('image/jpeg', 0.95)
  }

  // ── Save final (crop + filters applied) ──────────────────────────────────
  function handleSave() {
    if (!imgRef.current || !canvasRef.current) return
    const { x, y, w, h } = crop

    const tmp = document.createElement('canvas')
    const canvas = canvasRef.current
    tmp.width = canvas.width; tmp.height = canvas.height
    const ctx = tmp.getContext('2d')!
    const img = imgRef.current
    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`
    ctx.save()
    ctx.translate(tmp.width / 2, tmp.height / 2)
    ctx.rotate((rotation * Math.PI) / 180)
    ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2)
    ctx.restore()

    const out = document.createElement('canvas')
    out.width = w; out.height = h
    out.getContext('2d')!.drawImage(tmp, x, y, w, h, 0, 0, w, h)
    onSave(out.toDataURL('image/jpeg', 0.92))
  }

  // ── Rotate ────────────────────────────────────────────────────────────────
  function rotate(dir: 1 | -1) {
    const r = (rotation + dir * 90 + 360) % 360
    setRotation(r)
    if (imgRef.current) {
      const rotated = r === 90 || r === 270
      const iw = rotated ? imgRef.current.naturalHeight : imgRef.current.naturalWidth
      const ih = rotated ? imgRef.current.naturalWidth  : imgRef.current.naturalHeight
      setCrop({ x: 0, y: 0, w: iw, h: ih })
    }
  }

  // ── Defaults & Presets ────────────────────────────────────────────────────
  function saveAsDefault() {
    localStorage.setItem(DEFAULTS_KEY, JSON.stringify({ brightness, contrast, saturation }))
    setDefaultsSaved(true)
    setTimeout(() => setDefaultsSaved(false), 2000)
  }

  function applyPreset(p: Preset) {
    setBrightness(p.brightness); setContrast(p.contrast); setSaturation(p.saturation)
    if (imgRef.current) renderCanvas(imgRef.current, p.brightness, p.contrast, p.saturation, rotation)
  }

  function confirmSavePreset() {
    const name = presetName.trim(); if (!name) return
    const next = [...presets.filter(p => p.name !== name), { name, brightness, contrast, saturation }]
    setPresets(next); savePresets(next)
    setPresetName(''); setAddingPreset(false)
  }

  function deletePreset(name: string) {
    const next = presets.filter(p => p.name !== name)
    setPresets(next); savePresets(next)
  }

  // ── Crop overlay positions (as % of canvas display) ───────────────────────
  const cw = canvasRef.current?.width  || 1
  const ch = canvasRef.current?.height || 1
  const ol = crop.x / cw * 100
  const ot = crop.y / ch * 100
  const ow = crop.w / cw * 100
  const oh = crop.h / ch * 100

  const handles: { id: Handle; style: React.CSSProperties }[] = [
    { id: 'nw', style: { top: `${ot}%`,        left: `${ol}%` } },
    { id: 'n',  style: { top: `${ot}%`,        left: `${ol + ow / 2}%` } },
    { id: 'ne', style: { top: `${ot}%`,        left: `${ol + ow}%` } },
    { id: 'e',  style: { top: `${ot + oh / 2}%`, left: `${ol + ow}%` } },
    { id: 'se', style: { top: `${ot + oh}%`,   left: `${ol + ow}%` } },
    { id: 's',  style: { top: `${ot + oh}%`,   left: `${ol + ow / 2}%` } },
    { id: 'sw', style: { top: `${ot + oh}%`,   left: `${ol}%` } },
    { id: 'w',  style: { top: `${ot + oh / 2}%`, left: `${ol}%` } },
  ]

  const currentRatioPreset = showCustom ? -1 : ratio

  return (
    <div className="flex flex-col gap-4">

      {/* ── Preview + crop overlay ──────────────────────────────────────── */}
      <div className="relative rounded-xl overflow-hidden border border-stone-700 bg-stone-900 select-none">
        <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: 'auto' }} />

        {/* Overlay */}
        <div
          className="absolute inset-0"
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
        >
          {/* Dark masks around crop area */}
          <div className="absolute bg-black/50 inset-x-0 top-0 pointer-events-none" style={{ height: `${ot}%` }} />
          <div className="absolute bg-black/50 inset-x-0 bottom-0 pointer-events-none" style={{ top: `${ot + oh}%` }} />
          <div className="absolute bg-black/50 pointer-events-none" style={{ top: `${ot}%`, left: 0, width: `${ol}%`, height: `${oh}%` }} />
          <div className="absolute bg-black/50 pointer-events-none" style={{ top: `${ot}%`, left: `${ol + ow}%`, right: 0, height: `${oh}%` }} />

          {/* Crop box with rule-of-thirds grid */}
          <div
            className="absolute border-2 border-white/90 box-border"
            style={{ top: `${ot}%`, left: `${ol}%`, width: `${ow}%`, height: `${oh}%`, cursor: 'move' }}
            onPointerDown={e => startDrag(e, 'move')}
          >
            {/* Rule of thirds */}
            <div className="absolute inset-0 pointer-events-none" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: '1fr 1fr 1fr' }}>
              {[...Array(9)].map((_, i) => (
                <div key={i} className={[
                  i % 3 !== 2 ? 'border-r border-white/20' : '',
                  i < 6      ? 'border-b border-white/20' : '',
                ].join(' ')} />
              ))}
            </div>
          </div>

          {/* Handles */}
          {handles.map(({ id, style }) => (
            <div
              key={id}
              className="absolute z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-sm border-2 border-white bg-white shadow-md"
              style={{ ...style, cursor: CURSOR[id] }}
              onPointerDown={e => startDrag(e, id)}
            />
          ))}
        </div>
      </div>

      {/* ── Ratio presets ────────────────────────────────────────────────── */}
      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-xs font-medium text-stone-600">Crop Ratio</span>
          <span className="text-xs text-stone-400 tabular-nums">{crop.w} × {crop.h} px</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {RATIO_PRESETS.map(p => (
            <button
              key={p.label}
              onClick={() => selectPreset(p.value)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                currentRatioPreset === p.value
                  ? 'border-amber-400 bg-amber-50 text-amber-700'
                  : 'border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-stone-50'
              }`}
            >
              {p.label}
            </button>
          ))}
          <button
            onClick={applyCrop}
            className="ml-auto rounded-lg border border-green-300 bg-green-50 px-4 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 transition-colors"
          >
            Apply Crop
          </button>
        </div>

        {/* Custom ratio inputs */}
        {showCustom && (
          <div className="mt-2 flex items-center gap-2">
            <input
              type="number" min="1" value={customW}
              onChange={e => setCustomW(e.target.value)}
              className="w-16 rounded-lg border border-stone-200 px-2 py-1.5 text-center text-sm focus:border-amber-400 focus:outline-none"
              placeholder="W"
            />
            <span className="text-stone-400 font-medium">:</span>
            <input
              type="number" min="1" value={customH}
              onChange={e => setCustomH(e.target.value)}
              className="w-16 rounded-lg border border-stone-200 px-2 py-1.5 text-center text-sm focus:border-amber-400 focus:outline-none"
              placeholder="H"
            />
            <button
              onClick={applyCustomRatio}
              className="rounded-lg border border-amber-400 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors"
            >
              Set ratio
            </button>
          </div>
        )}
      </div>

      {/* ── Presets ──────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-stone-200 bg-stone-50 p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-stone-600">Presets</span>
          <button
            onClick={saveAsDefault}
            className={`text-xs transition-colors ${defaultsSaved ? 'text-green-600 font-medium' : 'text-stone-400 hover:text-amber-600'}`}
          >
            {defaultsSaved ? '✓ Set as default' : 'Set as default'}
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {presets.map(p => (
            <div key={p.name} className="flex items-center rounded-full border border-stone-200 bg-white overflow-hidden">
              <button
                onClick={() => applyPreset(p)}
                className="pl-3 pr-1.5 py-1 text-xs text-stone-700 hover:text-amber-700 transition-colors"
              >
                {p.name}
              </button>
              <button
                onClick={() => deletePreset(p.name)}
                className="pr-2 py-1 text-stone-300 hover:text-red-400 transition-colors"
              >
                ×
              </button>
            </div>
          ))}
          {!addingPreset ? (
            <button
              onClick={() => setAddingPreset(true)}
              className="rounded-full border border-dashed border-stone-300 px-3 py-1 text-xs text-stone-400 hover:border-amber-400 hover:text-amber-600 transition-colors"
            >
              + Save preset
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              <input
                autoFocus
                type="text"
                value={presetName}
                onChange={e => setPresetName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') confirmSavePreset(); if (e.key === 'Escape') { setAddingPreset(false); setPresetName('') } }}
                placeholder="Name…"
                className="rounded-lg border border-stone-200 px-2 py-1 text-xs focus:border-amber-400 focus:outline-none w-24"
              />
              <button onClick={confirmSavePreset} className="rounded-lg bg-amber-500 px-2.5 py-1 text-xs font-medium text-white hover:bg-amber-600 transition-colors">Save</button>
              <button onClick={() => { setAddingPreset(false); setPresetName('') }} className="text-xs text-stone-400 hover:text-stone-600">✕</button>
            </div>
          )}
        </div>
      </div>

      {/* ── Adjustments ──────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-stone-200 bg-stone-50 p-4 space-y-3">
        <span className="text-xs font-medium text-stone-600">Adjustments</span>
        {([
          { label: 'Brightness', val: brightness, set: setBrightness },
          { label: 'Contrast',   val: contrast,   set: setContrast   },
          { label: 'Saturation', val: saturation,  set: setSaturation  },
        ] as const).map(({ label, val, set }) => (
          <div key={label}>
            <div className="flex justify-between text-xs text-stone-500 mb-1">
              <span>{label}</span>
              <span className="tabular-nums font-medium">{val}%</span>
            </div>
            <input
              type="range" min="0" max="200" value={val}
              onChange={e => (set as (v: number) => void)(Number(e.target.value))}
              className="w-full h-1.5 accent-amber-500 cursor-pointer"
            />
          </div>
        ))}
      </div>

      {/* ── Rotate + Reset ───────────────────────────────────────────────── */}
      <div className="flex gap-2">
        <button onClick={() => rotate(-1)} className="flex-1 rounded-lg border border-stone-200 py-2 text-sm text-stone-600 hover:bg-stone-50 transition-colors">↺ Left</button>
        <button onClick={() => rotate(1)}  className="flex-1 rounded-lg border border-stone-200 py-2 text-sm text-stone-600 hover:bg-stone-50 transition-colors">↻ Right</button>
        <button
          onClick={() => {
            setBrightness(100); setContrast(100); setSaturation(100); setRotation(0)
            if (imgRef.current) {
              const iw = imgRef.current.naturalWidth, ih = imgRef.current.naturalHeight
              setCrop({ x: 0, y: 0, w: iw, h: ih })
              renderCanvas(imgRef.current, 100, 100, 100, 0)
            }
          }}
          className="rounded-lg border border-stone-200 px-4 py-2 text-sm text-stone-400 hover:bg-stone-50 transition-colors"
        >
          Reset
        </button>
      </div>

      {/* ── Save / Cancel ────────────────────────────────────────────────── */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSave}
          className="flex-1 rounded-full bg-amber-500 py-2.5 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
        >
          Use this photo
        </button>
        <button
          onClick={onCancel}
          className="rounded-full border border-stone-200 px-5 py-2.5 text-sm text-stone-600 hover:bg-stone-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
