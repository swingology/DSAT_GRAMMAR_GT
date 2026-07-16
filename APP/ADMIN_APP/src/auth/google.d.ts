// Minimal typing for the Google Identity Services script (loaded by useGoogleScript).

interface GoogleAccountsId {
  initialize(config: {
    client_id: string
    callback: (response: { credential: string }) => void
    // Never auto-credential a single previously-approved session — always show
    // the account chooser so the user can pick between admin accounts.
    auto_select?: boolean
  }): void
  renderButton(parent: HTMLElement, options: Record<string, unknown>): void
  disableAutoSelect(): void
}

interface Window {
  google?: { accounts?: { id?: GoogleAccountsId } }
}
