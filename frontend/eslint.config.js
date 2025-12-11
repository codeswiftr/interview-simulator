import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Allow setState in effects for state machine patterns (intentional in conversation hooks)
      'react-hooks/set-state-in-effect': 'off',
    },
  },
  // Relaxed rules for test files
  {
    files: ['**/*.test.{ts,tsx}', '**/__tests__/**/*.{ts,tsx}', '**/test/**/*.{ts,tsx}', 'e2e/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',  // Allow `any` in test mocks
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
      'react-hooks/rules-of-hooks': 'off',  // Allow hooks in test utilities
    },
  },
])
