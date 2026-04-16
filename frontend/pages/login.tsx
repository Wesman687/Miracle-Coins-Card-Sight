import { useEffect } from 'react'
import { useRouter } from 'next/router'

/** Redirect legacy /login to the unified login page. */
export default function LegacyLoginRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/account/login') }, [])
  return null
}
