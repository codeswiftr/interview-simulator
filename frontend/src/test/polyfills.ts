// Polyfills that must run before any other test code
// This ensures localStorage is available for MSW initialization
// Node.js 25+ has built-in localStorage but requires --localstorage-file flag

// Create a proper localStorage mock that works with MSW
const createStorageMock = () => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
};

// Always override localStorage to ensure it has proper methods
// Node.js 25+ localStorage exists but may not be functional without --localstorage-file
const localStorageMock = createStorageMock();
Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

// Set up proper URL base for jsdom/MSW
// This fixes ERR_INVALID_URL errors when MSW intercepts requests
if (typeof window !== 'undefined' && window.location) {
  // jsdom's location might not be properly configured
  try {
    // Ensure location has a valid href
    if (!window.location.href || window.location.href === 'about:blank') {
      Object.defineProperty(window, 'location', {
        value: {
          ...window.location,
          href: 'http://localhost:3000/',
          origin: 'http://localhost:3000',
          protocol: 'http:',
          host: 'localhost:3000',
          hostname: 'localhost',
          port: '3000',
          pathname: '/',
          search: '',
          hash: '',
          assign: () => {},
          reload: () => {},
          replace: () => {},
          toString: () => 'http://localhost:3000/',
        },
        writable: true,
        configurable: true,
      });
    }
  } catch {
    // If we can't modify location, that's okay
  }
}

// Also ensure sessionStorage
if (typeof globalThis.sessionStorage === 'undefined') {
  const sessionStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = String(value);
      },
      removeItem: (key: string) => {
        delete store[key];
      },
      clear: () => {
        store = {};
      },
      get length() {
        return Object.keys(store).length;
      },
      key: (index: number) => Object.keys(store)[index] ?? null,
    };
  })();

  Object.defineProperty(globalThis, 'sessionStorage', {
    value: sessionStorageMock,
    writable: true,
    configurable: true,
  });
}
