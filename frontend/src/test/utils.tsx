import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

interface AllProvidersProps {
  children: ReactNode;
}

// Simple wrapper without AuthProvider to avoid navigation issues in tests
function AllProviders({ children }: AllProvidersProps) {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
