type GetTokenFn = () => string | null;
type OnUnauthorizedFn = () => void | Promise<void>;

let getTokenFn: GetTokenFn = () => null;
let onUnauthorizedFn: OnUnauthorizedFn = () => {};

export interface ConfigureApiAuthOptions {
  getToken?: GetTokenFn;
  onUnauthorized?: OnUnauthorizedFn;
}

export function configureApiAuth(options: ConfigureApiAuthOptions): void {
  if (options.getToken) {
    getTokenFn = options.getToken;
  }
  if (options.onUnauthorized) {
    onUnauthorizedFn = options.onUnauthorized;
  }
}

export function getApiToken(): string | null {
  return getTokenFn();
}

export function notifyUnauthorized(): void | Promise<void> {
  return onUnauthorizedFn();
}
