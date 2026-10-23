import { createContext } from 'react'

// Native dialogs live in the top layer and must close while reauthenticating.
export const AuthenticationVisibility = createContext(true)
