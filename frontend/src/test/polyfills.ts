// Polyfills that must run before any other test code
// This ensures localStorage is available for MSW initialization
// Node.js 25+ has built-in localStorage but requires --localstorage-file flag

// Set up import.meta.env for tests
if (typeof import.meta.env === 'undefined') {
  (import.meta as { env?: Record<string, string> }).env = {
    VITE_API_URL: 'http://localhost:8000/api/v1',
    DEV: 'true',
    MODE: 'test',
  };
} else {
  import.meta.env.VITE_API_URL = 'http://localhost:8000/api/v1';
}

// Set global location for MSW interceptors
// MSW needs this to resolve relative URLs
if (typeof global !== 'undefined' && !global.location) {
  global.location = {
    href: 'http://localhost:3000/',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
  } as Location;
}

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

if (typeof globalThis.ProgressEvent === 'undefined') {
  class TestProgressEvent extends Event {
    readonly lengthComputable: boolean;
    readonly loaded: number;
    readonly total: number;

    constructor(type: string, eventInitDict: ProgressEventInit = {}) {
      super(type, eventInitDict);
      this.lengthComputable = eventInitDict.lengthComputable ?? false;
      this.loaded = eventInitDict.loaded ?? 0;
      this.total = eventInitDict.total ?? 0;
    }
  }

  Object.defineProperty(globalThis, 'ProgressEvent', {
    value: TestProgressEvent,
    writable: true,
    configurable: true,
  });
}

// Set up proper URL base for jsdom/MSW
// This fixes ERR_INVALID_URL errors when MSW intercepts requests
if (typeof window !== 'undefined') {
  // Ensure document.baseURI is set for MSW
  if (!document.baseURI || document.baseURI === 'about:blank' || document.baseURI === '') {
    Object.defineProperty(document, 'baseURI', {
      value: 'http://localhost:3000/',
      writable: true,
      configurable: true,
    });
  }

  // jsdom's location might not be properly configured
  if (window.location) {
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
