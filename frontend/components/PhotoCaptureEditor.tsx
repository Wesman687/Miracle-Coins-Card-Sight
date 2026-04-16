import { useEffect, useMemo, useRef, useState } from 'react'
import { CameraIcon, PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Props {
  onAddImages: (files: File[]) => Promise<void> | void
  onClose: () => void
}

export default function PhotoCaptureEditor({ onAddImages, onClose }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [sourceUrl, setSourceUrl] = useState<string | null>(null)
  const [sourceImage, setSourceImage] = useState<HTMLImageElement | null>(null)
  const [brightness, setBrightness] = useState(100)
  const [contrast, setContrast] = useState(100)
  const [cropX, setCropX] = useState(0)
  const [cropY, setCropY] = useState(0)
  const [cropSize, setCropSize] = useState(80)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
      if (sourceUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(sourceUrl)
      }
    }
  }, [stream, sourceUrl])

  const startCamera = async () => {
    try {
      const media = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      })
      setStream(media)
      if (videoRef.current) {
        videoRef.current.srcObject = media
      }
    } catch (error) {
      console.error(error)
      toast.error('Camera access failed')
    }
  }

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  const loadImageFromUrl = (url: string) => {
    const img = new Image()
    img.onload = () => {
      setSourceImage(img)
      setSourceUrl(url)
      setCropX(0)
      setCropY(0)
      setCropSize(80)
    }
    img.src = url
  }

  const handleFilePick = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    loadImageFromUrl(url)
  }

  const takeSnapshot = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)
    const url = canvas.toDataURL('image/jpeg', 0.95)
    loadImageFromUrl(url)
  }

  const previewStyle = useMemo(
    () => ({
      filter: `brightness(${brightness}%) contrast(${contrast}%)`,
      objectPosition: `${cropX}% ${cropY}%`,
      transform: `scale(${100 / cropSize})`,
      transformOrigin: `${cropX}% ${cropY}%`,
    }),
    [brightness, contrast, cropX, cropY, cropSize]
  )

  const saveEditedImage = async () => {
    if (!sourceImage) return
    setIsSaving(true)
    try {
      const canvas = document.createElement('canvas')
      const size = 1200
      canvas.width = size
      canvas.height = size
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Canvas unavailable')

      const minSide = Math.min(sourceImage.width, sourceImage.height)
      const cropPx = (cropSize / 100) * minSide
      const maxX = Math.max(sourceImage.width - cropPx, 0)
      const maxY = Math.max(sourceImage.height - cropPx, 0)
      const sx = (cropX / 100) * maxX
      const sy = (cropY / 100) * maxY

      ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`
      ctx.drawImage(sourceImage, sx, sy, cropPx, cropPx, 0, 0, size, size)

      const blob: Blob | null = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
      if (!blob) throw new Error('Failed to export image')
      const file = new File([blob], `coin-photo-${Date.now()}.jpg`, { type: 'image/jpeg' })
      await onAddImages([file])
      toast.success('Edited image added')
      onClose()
    } catch (error) {
      console.error(error)
      toast.error('Failed to save edited image')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-2xl border border-white/10 bg-gray-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Photo capture & editor</h2>
            <p className="text-sm text-gray-400">Take a photo, crop it, then adjust brightness and contrast before saving.</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><XMarkIcon className="h-6 w-6" /></button>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            {!sourceImage ? (
              <div className="space-y-4">
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-black">
                  {stream ? (
                    <video ref={videoRef} autoPlay playsInline className="aspect-video w-full object-cover" />
                  ) : (
                    <div className="flex aspect-video items-center justify-center text-gray-500">Start camera or choose an image</div>
                  )}
                </div>
                <div className="flex flex-wrap gap-3">
                  <button onClick={startCamera} className="rounded-lg bg-yellow-500 px-4 py-2 font-medium text-black"><CameraIcon className="mr-2 inline h-5 w-5" />Start camera</button>
                  {stream && <button onClick={takeSnapshot} className="rounded-lg border border-white/15 px-4 py-2 text-white">Capture photo</button>}
                  <label className="rounded-lg border border-white/15 px-4 py-2 text-white cursor-pointer">
                    <PhotoIcon className="mr-2 inline h-5 w-5" />Choose file
                    <input type="file" accept="image/*" className="hidden" onChange={handleFilePick} />
                  </label>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-black">
                  <div className="mx-auto aspect-square max-w-2xl overflow-hidden">
                    <img src={sourceUrl || ''} alt="Editor preview" className="h-full w-full object-cover" style={previewStyle} />
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="block text-sm text-gray-300">Crop zoom
                    <input type="range" min="35" max="100" value={cropSize} onChange={(e) => setCropSize(Number(e.target.value))} className="mt-2 w-full" />
                  </label>
                  <label className="block text-sm text-gray-300">Crop horizontal
                    <input type="range" min="0" max="100" value={cropX} onChange={(e) => setCropX(Number(e.target.value))} className="mt-2 w-full" />
                  </label>
                  <label className="block text-sm text-gray-300">Crop vertical
                    <input type="range" min="0" max="100" value={cropY} onChange={(e) => setCropY(Number(e.target.value))} className="mt-2 w-full" />
                  </label>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4 rounded-2xl border border-white/10 bg-gray-800/60 p-4">
            <h3 className="text-lg font-semibold text-white">Adjustments</h3>
            <label className="block text-sm text-gray-300">Brightness
              <input type="range" min="60" max="160" value={brightness} onChange={(e) => setBrightness(Number(e.target.value))} className="mt-2 w-full" />
              <div className="mt-1 text-xs text-gray-500">{brightness}%</div>
            </label>
            <label className="block text-sm text-gray-300">Contrast
              <input type="range" min="60" max="180" value={contrast} onChange={(e) => setContrast(Number(e.target.value))} className="mt-2 w-full" />
              <div className="mt-1 text-xs text-gray-500">{contrast}%</div>
            </label>
            <div className="rounded-xl border border-white/10 bg-gray-900/60 p-3 text-sm text-gray-400">
              Saved output is a square JPG, good for storefront cards and product galleries.
            </div>
            {sourceImage && (
              <div className="flex flex-col gap-3">
                <button onClick={saveEditedImage} disabled={isSaving} className="rounded-lg bg-yellow-500 px-4 py-2 font-medium text-black disabled:opacity-60">
                  {isSaving ? 'Saving...' : 'Save edited image'}
                </button>
                <button onClick={() => { setSourceImage(null); setSourceUrl(null) }} className="rounded-lg border border-white/15 px-4 py-2 text-white">
                  Pick another image
                </button>
              </div>
            )}
          </div>
        </div>
        <canvas ref={canvasRef} className="hidden" />
      </div>
    </div>
  )
}
