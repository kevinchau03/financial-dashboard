import { useSyncExternalStore } from 'react'

function subscribe(onChange: () => void) {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

export default function useHash() {
  return useSyncExternalStore(subscribe, () => window.location.hash, () => '')
}
