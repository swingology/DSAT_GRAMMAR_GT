// Minimal typing for the Google Identity Services script (loaded by useGoogleScript).

interface GoogleAccountsId {
  initialize(config: {
    client_id: string
    callback: (response: { credential: string }) => void
  }): void
  renderButton(parent: HTMLElement, options: Record<string, unknown>): void
  disableAutoSelect(): void
}

interface Window {
  google?: { accounts?: { id?: GoogleAccountsId } }
}
